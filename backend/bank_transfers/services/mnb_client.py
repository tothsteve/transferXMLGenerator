"""
MNB (Magyar Nemzeti Bank) Exchange Rate API Client

This module provides a Python interface to the MNB SOAP web service
for retrieving official Hungarian Forint exchange rates.

API Documentation: https://www.mnb.hu/arfolyam-letoltes
WSDL: https://www.mnb.hu/arfolyamok.asmx?wsdl
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import List, Dict, Optional, Tuple
import xml.etree.ElementTree as ET

import requests

logger = logging.getLogger(__name__)


class MNBClientError(Exception):
    """Base exception for MNB client errors"""
    pass


class MNBClient:
    """
    Client for interacting with the Magyar Nemzeti Bank (MNB) exchange rate API.

    The MNB provides official daily exchange rates via a SOAP web service.
    This client uses direct HTTP requests with SOAP XML for simplicity.
    """

    SOAP_URL = 'http://www.mnb.hu/arfolyamok.asmx'
    SOAP_NAMESPACE = 'http://www.mnb.hu/webservices/'
    TIMEOUT = 10  # seconds

    def __init__(self):
        """Initialize MNB client"""
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'text/xml; charset=utf-8',
            'Accept': 'application/xml'
        })

    def _make_soap_request(self, method: str, body_content: str = '') -> str:
        """
        Make a SOAP request to the MNB API.

        Args:
            method: SOAP method name (e.g., 'GetCurrencies')
            body_content: XML content for the method body

        Returns:
            Response XML as string

        Raises:
            MNBClientError: If the request fails
        """
        soap_envelope = f'''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:web="{self.SOAP_NAMESPACE}">
  <soap:Header/>
  <soap:Body>
    <web:{method}>{body_content}</web:{method}>
  </soap:Body>
</soap:Envelope>'''

        try:
            response = self.session.post(
                self.SOAP_URL,
                data=soap_envelope.encode('utf-8'),
                headers={'SOAPAction': f'"{self.SOAP_NAMESPACE}{method}"'},
                timeout=self.TIMEOUT
            )
            response.raise_for_status()
            return response.text

        except requests.exceptions.Timeout:
            logger.error(f"MNB API timeout for method {method}")
            raise MNBClientError(f"Request timeout after {self.TIMEOUT} seconds")
        except requests.exceptions.RequestException as e:
            logger.error(f"MNB API request failed for {method}: {str(e)}")
            raise MNBClientError(f"API request failed: {str(e)}")

    def _parse_soap_response(self, response_xml: str, result_tag: str) -> str:
        """
        Extract result data from SOAP response.

        Args:
            response_xml: Full SOAP response
            result_tag: Name of the result tag to extract

        Returns:
            Inner XML content of the result tag
        """
        try:
            root = ET.fromstring(response_xml)

            # Find the result tag (strip namespaces for simplicity)
            for elem in root.iter():
                if elem.tag.endswith(result_tag):
                    return elem.text or ''

            raise MNBClientError(f"Result tag '{result_tag}' not found in response")

        except ET.ParseError as e:
            logger.error(f"Failed to parse SOAP response: {str(e)}")
            raise MNBClientError(f"XML parsing error: {str(e)}")

    def get_currencies(self) -> List[str]:
        """
        Get list of available currency codes from MNB.

        Returns:
            List of currency codes (e.g., ['USD', 'EUR', 'GBP', ...])
        """
        try:
            response = self._make_soap_request('GetCurrencies')
            result_xml = self._parse_soap_response(response, 'GetCurrenciesResult')

            # Parse the currency list XML
            root = ET.fromstring(result_xml)
            currencies = []
            for curr in root.iter('Curr'):
                if curr.text:
                    currencies.append(curr.text.strip())

            logger.info(f"Retrieved {len(currencies)} currencies from MNB")
            return currencies

        except Exception as e:
            logger.error(f"Failed to get currencies: {str(e)}")
            raise MNBClientError(f"Failed to retrieve currency list: {str(e)}")

    def get_current_exchange_rates(self, currencies: Optional[List[str]] = None) -> Tuple[str, Dict[str, Decimal]]:
        """
        Get current day's exchange rates for specified currencies.

        Args:
            currencies: List of currency codes (default: ['USD', 'EUR'])

        Returns:
            Tuple of (date_string, rates_dict)
            Example: ('2025-10-01', {'USD': Decimal('385.5'), 'EUR': Decimal('410.2')})
        """
        if currencies is None:
            currencies = ['USD', 'EUR']

        try:
            response = self._make_soap_request('GetCurrentExchangeRates')
            result_xml = self._parse_soap_response(response, 'GetCurrentExchangeRatesResult')

            # Parse the current exchange rates XML (root: MNBCurrentExchangeRates)
            root = ET.fromstring(result_xml)
            current_rates = {}
            rate_date = None

            # Find the Day element (should be only one for current rates)
            day = root.find('Day')
            if day is not None:
                # Extract the actual date from MNB response (don't use date.today()!)
                rate_date = day.get('date')

                for rate_elem in day.findall('Rate'):
                    currency = rate_elem.get('curr')
                    rate_value = rate_elem.text
                    unit = rate_elem.get('unit', '1')

                    # Filter for requested currencies
                    if currency and rate_value and currency in currencies:
                        try:
                            # MNB uses comma as decimal separator
                            rate_value_clean = rate_value.replace(',', '.')
                            rate = Decimal(rate_value_clean)

                            # Normalize to rate per 1 unit
                            unit_int = int(unit)
                            if unit_int != 1:
                                rate = rate / unit_int

                            current_rates[currency] = rate

                        except (ValueError, InvalidOperation) as e:
                            logger.warning(
                                f"Invalid rate value for {currency}: {rate_value} (unit: {unit})"
                            )
                            continue

            if not rate_date:
                raise MNBClientError("No date found in MNB response")

            logger.info(f"Retrieved current exchange rates for {rate_date}: {', '.join(current_rates.keys())}")
            return (rate_date, current_rates)

        except Exception as e:
            logger.error(f"Failed to get current exchange rates: {str(e)}")
            raise MNBClientError(f"Failed to retrieve current exchange rates: {str(e)}")

    def get_exchange_rates(
        self,
        start_date: date,
        end_date: date,
        currencies: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Decimal]]:
        """
        Get historical exchange rates for specified date range and currencies.

        Args:
            start_date: Start date for rate history
            end_date: End date for rate history
            currencies: List of currency codes (default: ['USD', 'EUR'])

        Returns:
            Nested dictionary: {date_str: {currency: rate}}
            Example:
            {
                '2025-01-15': {'USD': Decimal('385.5'), 'EUR': Decimal('410.2')},
                '2025-01-16': {'USD': Decimal('386.1'), 'EUR': Decimal('411.0')}
            }
        """
        if currencies is None:
            currencies = ['USD', 'EUR']

        # Format dates for MNB API
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        curr_list = ','.join(currencies)

        body_content = f'''
      <web:startDate>{start_str}</web:startDate>
      <web:endDate>{end_str}</web:endDate>
      <web:currencyNames>{curr_list}</web:currencyNames>'''

        try:
            response = self._make_soap_request('GetExchangeRates', body_content)
            result_xml = self._parse_soap_response(response, 'GetExchangeRatesResult')

            # Parse the exchange rates XML
            rates_data = self._parse_exchange_rates_xml(result_xml)

            logger.info(
                f"Retrieved exchange rates from {start_str} to {end_str} "
                f"for currencies: {curr_list}"
            )

            return rates_data

        except Exception as e:
            logger.error(
                f"Failed to get exchange rates for {start_str} to {end_str}: {str(e)}"
            )
            raise MNBClientError(f"Failed to retrieve exchange rates: {str(e)}")

    def _parse_exchange_rates_xml(self, xml_str: str) -> Dict[str, Dict[str, Decimal]]:
        """
        Parse MNB exchange rates XML response.

        MNB XML structure:
        <MNBExchangeRates>
          <Day date="2025-01-15">
            <Rate unit="1" curr="USD">385.5</Rate>
            <Rate unit="1" curr="EUR">410.2</Rate>
          </Day>
          ...
        </MNBExchangeRates>

        Args:
            xml_str: XML string from MNB API

        Returns:
            Nested dictionary: {date_str: {currency: rate}}
        """
        try:
            root = ET.fromstring(xml_str)
            rates_by_date = {}

            for day in root.findall('Day'):
                date_str = day.get('date')
                if not date_str:
                    continue

                day_rates = {}
                for rate_elem in day.findall('Rate'):
                    currency = rate_elem.get('curr')
                    rate_value = rate_elem.text
                    unit = rate_elem.get('unit', '1')

                    if currency and rate_value:
                        try:
                            # MNB uses comma as decimal separator
                            rate_value_clean = rate_value.replace(',', '.')
                            rate = Decimal(rate_value_clean)

                            # Normalize to rate per 1 unit
                            unit_int = int(unit)
                            if unit_int != 1:
                                rate = rate / unit_int

                            day_rates[currency] = rate

                        except (ValueError, InvalidOperation) as e:
                            logger.warning(
                                f"Invalid rate value for {currency} on {date_str}: "
                                f"{rate_value} (unit: {unit})"
                            )
                            continue

                if day_rates:
                    rates_by_date[date_str] = day_rates

            return rates_by_date

        except ET.ParseError as e:
            logger.error(f"Failed to parse exchange rates XML: {str(e)}")
            raise MNBClientError(f"XML parsing error: {str(e)}")

    def get_info(self) -> Dict[str, any]:
        """
        Get information about available data from MNB.

        Returns:
            Dictionary with first_date, last_date, and currencies
        """
        try:
            response = self._make_soap_request('GetInfo')
            result_xml = self._parse_soap_response(response, 'GetInfoResult')

            root = ET.fromstring(result_xml)

            info = {}

            # Extract first and last dates
            first_date_elem = root.find('FirstDate')
            last_date_elem = root.find('LastDate')

            if first_date_elem is not None and first_date_elem.text:
                info['first_date'] = first_date_elem.text

            if last_date_elem is not None and last_date_elem.text:
                info['last_date'] = last_date_elem.text

            # Extract currencies
            currencies = []
            for curr in root.iter('Curr'):
                if curr.text:
                    currencies.append(curr.text.strip())

            info['currencies'] = currencies

            logger.info(f"MNB Info: {info}")
            return info

        except Exception as e:
            logger.error(f"Failed to get MNB info: {str(e)}")
            raise MNBClientError(f"Failed to retrieve MNB info: {str(e)}")


# Convenience functions for common operations

def get_current_usd_eur_rates() -> Tuple[str, Dict[str, Decimal]]:
    """
    Quick helper to get current USD and EUR rates.

    Returns:
        Tuple of (date_string, rates_dict) with 'USD' and 'EUR' keys
        Example: ('2025-10-01', {'USD': Decimal('331.16'), 'EUR': Decimal('389.08')})
    """
    client = MNBClient()
    return client.get_current_exchange_rates(['USD', 'EUR'])


def get_rate_for_date(target_date: date, currency: str = 'EUR') -> Optional[Decimal]:
    """
    Get exchange rate for a specific date and currency.

    Args:
        target_date: Date to get rate for
        currency: Currency code (default: EUR)

    Returns:
        Exchange rate as Decimal, or None if not available
    """
    client = MNBClient()
    rates_data = client.get_exchange_rates(target_date, target_date, [currency])

    date_str = target_date.strftime('%Y-%m-%d')
    day_rates = rates_data.get(date_str, {})

    return day_rates.get(currency)
