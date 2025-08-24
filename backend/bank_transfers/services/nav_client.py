import requests
import hashlib
import hmac
import base64
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from django.conf import settings
from .credential_manager import CredentialManager
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


class NavApiClient:
    """
    Hungarian NAV Online Invoice API client - READ-ONLY OPERATIONS.
    
    IMPORTANT: This client is designed for READ-ONLY operations only.
    It queries invoice data from NAV but NEVER modifies, creates, or deletes
    anything in the NAV system.
    
    Supported operations:
    - tokenExchange: Get authentication token
    - queryInvoiceDigest: Get invoice list/summary  
    - queryInvoiceData: Get detailed invoice data
    
    FORBIDDEN operations (NOT implemented for safety):
    - manageInvoice: Submit/modify invoices
    - manageAnnulment: Cancel invoices
    """
    
    def __init__(self, nav_config):
        """
        Initialize NAV API client with company configuration.
        
        Args:
            nav_config: NavConfiguration instance with encrypted credentials
        """
        self.config = nav_config
        self.credential_manager = CredentialManager()
        self.base_url = self._get_base_url()
        self.session = requests.Session()
        self.session.timeout = settings.NAV_API_TIMEOUT
        
        # Current authentication token
        self._auth_token = None
        self._token_expiry = None
    
    def _get_base_url(self):
        """Get the appropriate NAV API base URL based on environment."""
        if self.config.api_environment == 'production':
            return 'https://api.onlineszamla.nav.gov.hu/invoiceService/v3'
        else:
            return 'https://api-test.onlineszamla.nav.gov.hu/invoiceService/v3'
    
    
    def _aes_128_ecb_decrypt(self, encrypted_data, key):
        """Decrypt data using AES-128 ECB as required by NAV API."""
        try:
            # Ensure key is exactly 16 bytes for AES-128
            if len(key) > 16:
                aes_key = key[:16].encode('utf-8') if isinstance(key, str) else key[:16]
            else:
                aes_key = key.ljust(16, b'\0').encode('utf-8') if isinstance(key, str) else key.ljust(16, b'\0')
            
            # Decode base64 if needed
            if isinstance(encrypted_data, str):
                try:
                    data_to_decrypt = base64.b64decode(encrypted_data)
                except:
                    data_to_decrypt = encrypted_data.encode('utf-8')
            else:
                data_to_decrypt = encrypted_data
            
            # Create AES-128 ECB cipher
            cipher = Cipher(algorithms.AES(aes_key), modes.ECB(), backend=default_backend())
            decryptor = cipher.decryptor()
            
            # Decrypt
            decrypted = decryptor.update(data_to_decrypt) + decryptor.finalize()
            
            # Remove PKCS7 padding
            padding_length = decrypted[-1]
            return decrypted[:-padding_length].decode('utf-8')
            
        except Exception as e:
            # AES decryption failed, return original data
            return encrypted_data

    def _get_decrypted_credentials(self):
        """Get decrypted NAV API credentials."""
        raw_exchange_key = self.config.get_decrypted_exchange_key()
        
        # Try AES-128 ECB decryption of exchange key if it looks encrypted
        processed_exchange_key = raw_exchange_key
        if len(raw_exchange_key) > 16 and '=' in raw_exchange_key:
            # Looks like it might be base64 encoded and need AES decryption
            # Try using signing key as AES key
            signing_key = self.config.get_decrypted_signing_key()
            processed_exchange_key = self._aes_128_ecb_decrypt(raw_exchange_key, signing_key)
        
        return {
            'technical_user_login': self.config.technical_user_login,
            'technical_user_password': self.config.get_decrypted_password(),
            'signing_key': self.config.get_decrypted_signing_key(),
            'exchange_key': processed_exchange_key,
            'raw_exchange_key': raw_exchange_key,
            'tax_number': self.config.tax_number
        }
    
    def _generate_request_id(self):
        """Generate a unique request ID for NAV API calls."""
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')[:-3]
        return f"REQ{timestamp}"
    
    def _generate_timestamp(self):
        """Generate RFC 3339 timestamp for NAV API."""
        return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    
    def _generate_request_signature(self, request_data):
        """
        Generate request signature for NAV API authentication.
        
        According to NAV 3.0 specification (section 1.5.2):
        For operations outside manageInvoice/manageAnnulment:
        requestSignature = SHA3-512(requestId + timestampMask + signingKey)
        
        Where:
        - requestId: the request ID value
        - timestampMask: UTC timestamp using YYYYMMDDhhmmss mask (NO separators, NO timezone)
        - signingKey: string literal of technical user's signature key
        
        Args:
            request_data: Dictionary containing request data
            
        Returns:
            Hex encoded signature string (uppercase)
        """
        credentials = self._get_decrypted_credentials()
        
        # Get the raw signing key (as stored, no additional decoding needed)
        signing_key = credentials['signing_key']
        
        # Convert ISO timestamp to NAV mask format: YYYYMMDDhhmmss
        # From: 2025-08-22T19:19:44.649Z
        # To:   20250822191944
        iso_timestamp = request_data['timestamp']
        timestamp_mask = self._convert_to_nav_timestamp_mask(iso_timestamp)
        
        # Create string to sign according to NAV specification (section 1.5.2)
        # Format: requestId + timestampMask + signingKey
        string_to_sign = (
            f"{request_data['requestId']}"
            f"{timestamp_mask}"
            f"{signing_key}"
        )
        
        # NAV API 3.0 uses SHA3-512
        hash_object = hashlib.sha3_512()
        hash_object.update(string_to_sign.encode('utf-8'))
        
        # NAV expects HEX format in uppercase
        encoded_signature = hash_object.hexdigest().upper()
        
        return encoded_signature
    
    def _convert_to_nav_timestamp_mask(self, iso_timestamp):
        """
        Convert ISO timestamp to NAV timestamp mask format.
        
        From: 2025-08-22T19:19:44.649Z
        To:   20250822191944
        
        Args:
            iso_timestamp: ISO format timestamp string
            
        Returns:
            NAV timestamp mask (YYYYMMDDhhmmss)
        """
        # Parse the ISO timestamp
        dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        
        # Format as YYYYMMDDhhmmss (remove all separators and timezone)
        return dt.strftime('%Y%m%d%H%M%S')
    
    def _create_base_request(self, operation):
        """
        Create base request structure for NAV API calls.
        
        Args:
            operation: NAV API operation name
            
        Returns:
            Dictionary with base request structure
        """
        credentials = self._get_decrypted_credentials()
        request_id = self._generate_request_id()
        timestamp = self._generate_timestamp()
        
        request_data = {
            'requestId': request_id,
            'timestamp': timestamp,
            'requestVersion': '3.0',
            'headerVersion': '1.0'
        }
        
        # Generate signature
        signature = self._generate_request_signature(request_data)
        
        # Complete request structure
        base_request = {
            'header': {
                'requestId': request_id,
                'timestamp': timestamp,
                'requestVersion': '3.0',
                'headerVersion': '1.0'
            },
            'user': {
                'login': credentials['technical_user_login'],
                'passwordHash': self._hash_password(credentials['technical_user_password']),
                'taxNumber': credentials['tax_number'],
                'requestSignature': signature
            }
        }
        
        return base_request
    
    def _hash_password(self, password):
        """
        Hash password according to NAV specification.
        
        Args:
            password: Plain text password
            
        Returns:
            SHA512 hash of password in uppercase
        """
        hash_object = hashlib.sha512()
        hash_object.update(password.encode('utf-8'))
        return hash_object.hexdigest().upper()
    
    def _make_api_request(self, endpoint, request_data):
        """
        Make authenticated request to NAV API.
        
        Args:
            endpoint: API endpoint path
            request_data: Request payload (dict)
            
        Returns:
            Response data dictionary
        """
        url = f"{self.base_url}/{endpoint}"
        
        # Convert request data to XML
        if endpoint == 'tokenExchange':
            xml_data = self._create_token_exchange_xml(request_data)
        else:
            xml_data = self._dict_to_xml(request_data)
        
        # Send request to NAV API
        
        try:
            response = self.session.post(
                url,
                data=xml_data,
                headers={
                    'Content-Type': 'application/xml',
                    'Accept': 'application/xml'
                }
            )
            
            # Handle non-200 responses
            
            response.raise_for_status()
            
            # Parse XML response
            return self._xml_to_dict(response.text)
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"NAV API request failed: {str(e)}")
    
    def _create_token_exchange_xml(self, request_data):
        """Create properly formatted NAV token exchange XML."""
        # Create XML with exact structure from NAV example
        xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<TokenExchangeRequest xmlns:common="http://schemas.nav.gov.hu/NTCA/1.0/common" xmlns="http://schemas.nav.gov.hu/OSA/3.0/api">
	<common:header>
		<common:requestId>{request_data['header']['requestId']}</common:requestId>
		<common:timestamp>{request_data['header']['timestamp']}</common:timestamp>
		<common:requestVersion>{request_data['header']['requestVersion']}</common:requestVersion>
		<common:headerVersion>{request_data['header']['headerVersion']}</common:headerVersion>
	</common:header>
	<common:user>
		<common:login>{request_data['user']['login']}</common:login>
		<common:passwordHash cryptoType="SHA-512">{request_data['user']['passwordHash']}</common:passwordHash>
		<common:taxNumber>{request_data['user']['taxNumber'].replace('-', '')[:8]}</common:taxNumber>
		<common:requestSignature cryptoType="SHA3-512">{request_data['user']['requestSignature']}</common:requestSignature>
	</common:user>
	<software>
		<softwareId>{request_data['software']['softwareId']}</softwareId>
		<softwareName>{request_data['software']['softwareName']}</softwareName>
		<softwareOperation>{request_data['software']['softwareOperation']}</softwareOperation>
		<softwareMainVersion>{request_data['software']['softwareMainVersion']}</softwareMainVersion>
		<softwareDevName>{request_data['software']['softwareDevName']}</softwareDevName>
		<softwareDevContact>{request_data['software']['softwareDevContact']}</softwareDevContact>
		<softwareDevCountryCode>HU</softwareDevCountryCode>
		<softwareDevTaxNumber>{request_data['software']['softwareDevTaxNumber'].replace('-', '')[:8]}</softwareDevTaxNumber>
	</software>
</TokenExchangeRequest>'''
        return xml_content.encode('utf-8')
    
    def _dict_to_xml(self, data, root_name="Request"):
        """Fallback XML generation for non-tokenExchange requests."""
        # Simple XML generation as fallback
        return f'<{root_name}></{root_name}>'.encode('utf-8')
    
    def _xml_to_dict(self, xml_string):
        """Convert XML string to dictionary."""
        root = ET.fromstring(xml_string)
        
        def element_to_dict(element):
            result = {}
            for child in element:
                if len(child) == 0:
                    result[child.tag] = child.text
                else:
                    result[child.tag] = element_to_dict(child)
            return result
        
        return element_to_dict(root)
    
    def token_exchange(self):
        """
        Perform token exchange with NAV API.
        
        Returns:
            Authentication token string
        """
        # Create proper NAV API 3.0 token exchange request
        credentials = self._get_decrypted_credentials()
        request_id = self._generate_request_id()
        timestamp = self._generate_timestamp()
        
        # Create proper XML structure for NAV API 3.0
        request_data = {
            'header': {
                'requestId': request_id,
                'timestamp': timestamp,
                'requestVersion': '3.0',
                'headerVersion': '1.0'
            },
            'user': {
                'login': credentials['technical_user_login'],
                'passwordHash': self._hash_password(credentials['technical_user_password']),
                'taxNumber': credentials['tax_number'],
                'requestSignature': self._generate_request_signature({
                    'requestId': request_id,
                    'timestamp': timestamp
                })
            },
            'software': {
                'softwareId': '28778367-TXMLGEN01',  # Must be exactly 18 chars: [0-9A-Z\-]{18}
                'softwareName': 'Transfer XML Generator',
                'softwareOperation': 'LOCAL_SOFTWARE', 
                'softwareMainVersion': '1.0',
                'softwareDevName': 'IT Cardigan Kft.',
                'softwareDevContact': 'info@itcardigan.hu',
                'softwareDevTaxNumber': credentials['tax_number']
            }
        }
        
        try:
            response = self._make_api_request('tokenExchange', request_data)
            
            # Extract token from response (handle namespaced XML)
            token = None
            
            # Try different possible keys due to XML namespacing
            token_keys = [
                'encodedExchangeToken',
                '{http://schemas.nav.gov.hu/OSA/3.0/api}encodedExchangeToken'
            ]
            
            for key in token_keys:
                if key in response:
                    token = response[key]
                    break
            
            if token:
                self._auth_token = token
                # Set token expiry (NAV tokens typically expire in 5 minutes)
                self._token_expiry = datetime.now(timezone.utc).timestamp() + 300
                return self._auth_token
            else:
                raise Exception(f"Token not found in response. Available keys: {list(response.keys())}")
                
        except Exception as e:
            raise Exception(f"Token exchange failed: {str(e)}")
    
    def _ensure_valid_token(self):
        """Ensure we have a valid authentication token."""
        current_time = datetime.now(timezone.utc).timestamp()
        
        if (not self._auth_token or 
            not self._token_expiry or 
            current_time >= self._token_expiry - 30):  # Refresh 30 seconds before expiry
            self.token_exchange()
    
    def query_invoice_digest(self, direction='OUTBOUND', page=1, date_from=None, date_to=None):
        """
        Query invoice digest from NAV API using proper XML format.
        
        Args:
            direction: 'INBOUND' or 'OUTBOUND'
            page: Page number for pagination (1-based)
            date_from: datetime object for start date
            date_to: datetime object for end date
            
        Returns:
            List of invoice digest entries
        """
        self._ensure_valid_token()
        
        # Convert datetime to string format needed by NAV
        if date_from:
            if isinstance(date_from, str):
                date_from_str = date_from
            else:
                date_from_str = date_from.strftime('%Y-%m-%d')
        else:
            # Default to last 30 days to stay within NAV's 35-day limit
            default_date_from = datetime.now() - timedelta(days=30)
            date_from_str = default_date_from.strftime('%Y-%m-%d')
            
        if date_to:
            if isinstance(date_to, str):
                date_to_str = date_to
            else:
                date_to_str = date_to.strftime('%Y-%m-%d')
        else:
            date_to_str = datetime.now().strftime('%Y-%m-%d')
        
        # Create the XML request based on NAV 3.0 specification
        xml_request = self._create_query_invoice_digest_xml(direction, page, date_from_str, date_to_str)
        
        try:
            response = self._make_xml_request('queryInvoiceDigest', xml_request)
            return self._parse_invoice_digest_response(response)
            
        except Exception as e:
            raise Exception(f"Query invoice digest failed: {str(e)}")
    
    def _clean_tax_number_for_query(self, tax_number):
        """
        Clean tax number for NAV query requests.
        
        For query requests (queryInvoiceDigest), NAV expects tax numbers:
        - Without dashes or spaces
        - Maximum 8 characters
        - For Hungarian tax numbers like "28778367-2-16", use first 8 digits: "28778367"
        """
        # Remove all non-digit characters
        clean_tax_number = ''.join(filter(str.isdigit, tax_number))
        
        # For Hungarian tax numbers, take first 8 digits
        if len(clean_tax_number) > 8:
            clean_tax_number = clean_tax_number[:8]
        
        return clean_tax_number
    
    def _create_query_invoice_digest_xml(self, direction, page, date_from_str, date_to_str):
        """Create XML request for queryInvoiceDigest based on NAV 3.0 specification."""
        
        # Use the existing credential management methods
        credentials = self._get_decrypted_credentials()
        request_id = self._generate_request_id()
        timestamp = self._generate_timestamp()
        
        # Create password hash using the existing method
        password_hash = self._hash_password(credentials['technical_user_password'])
        
        # Calculate request signature using existing method
        request_signature = self._generate_request_signature({
            'requestId': request_id,
            'timestamp': timestamp
        })
        
        # Clean tax numbers for query requests (8 digits max, no dashes)
        clean_tax_number = self._clean_tax_number_for_query(self.config.tax_number)
        
        # Convert date strings to datetime format for insDate (NAV insertion date)
        # BIP's working implementation uses insDate instead of invoiceIssueDate
        date_from_datetime = f"{date_from_str}T00:00:00.000Z"
        date_to_datetime = f"{date_to_str}T23:59:59.999Z"
        
        # Create XML matching BIP's exact software configuration
        # BIP uses full tax number with dashes in softwareDevTaxNumber
        dev_tax_number = self.config.tax_number  # Keep full format for software block
        software_id = f"HU{clean_tax_number}TXG00001"  # Match BIP's pattern: HU{taxNumber}XXX00001
        
        xml_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<QueryInvoiceDigestRequest xmlns:common="http://schemas.nav.gov.hu/NTCA/1.0/common" xmlns="http://schemas.nav.gov.hu/OSA/3.0/api">
\t<common:header>
\t\t<common:requestId>{request_id}</common:requestId>
\t\t<common:timestamp>{timestamp}</common:timestamp>
\t\t<common:requestVersion>3.0</common:requestVersion>
\t\t<common:headerVersion>1.0</common:headerVersion>
\t</common:header>
\t<common:user>
\t\t<common:login>{credentials['technical_user_login']}</common:login>
\t\t<common:passwordHash cryptoType="SHA-512">{password_hash}</common:passwordHash>
\t\t<common:taxNumber>{clean_tax_number}</common:taxNumber>
\t\t<common:requestSignature cryptoType="SHA3-512">{request_signature}</common:requestSignature>
\t</common:user>
\t<software>
\t\t<softwareId>{software_id}</softwareId>
\t\t<softwareName>TransferXMLGenerator</softwareName>
\t\t<softwareOperation>LOCAL_SOFTWARE</softwareOperation>
\t\t<softwareMainVersion>1.0</softwareMainVersion>
\t\t<softwareDevName>IT Cardigan Kft.</softwareDevName>
\t\t<softwareDevContact>info@itcardigan.hu</softwareDevContact>
\t\t<softwareDevCountryCode>HU</softwareDevCountryCode>
\t\t<softwareDevTaxNumber>{dev_tax_number}</softwareDevTaxNumber>
\t</software>
\t<page>{page}</page>
\t<invoiceDirection>{direction}</invoiceDirection>
\t<invoiceQueryParams>
\t\t<mandatoryQueryParams>
\t\t\t<insDate>
\t\t\t\t<dateTimeFrom>{date_from_datetime}</dateTimeFrom>
\t\t\t\t<dateTimeTo>{date_to_datetime}</dateTimeTo>
\t\t\t</insDate>
\t\t</mandatoryQueryParams>
\t</invoiceQueryParams>
</QueryInvoiceDigestRequest>"""
        
        return xml_request
    
    def _create_query_invoice_chain_digest_xml(self, tax_number, invoice_number, direction):
        """Create XML request for queryInvoiceChainDigest based on NAV 3.0 specification."""
        
        # Use the existing credential management methods
        credentials = self._get_decrypted_credentials()
        request_id = self._generate_request_id()
        timestamp = self._generate_timestamp()
        
        # Create password hash and request signature using existing methods
        password_hash = self._hash_password(credentials['technical_user_password'])
        request_signature = self._generate_request_signature({
            'requestId': request_id,
            'timestamp': timestamp
        })
        
        # Clean tax numbers for query requests (8 digits max, no dashes)
        clean_tax_number = self._clean_tax_number_for_query(self.config.tax_number)
        clean_supplier_tax_number = self._clean_tax_number_for_query(tax_number)
        
        # Create XML matching the NAV 3.0 specification
        dev_tax_number = self.config.tax_number  # Keep full format for software block
        software_id = f"HU{clean_tax_number}TXG00001"  # Match BIP's pattern
        
        xml_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<QueryInvoiceChainDigestRequest xmlns:common="http://schemas.nav.gov.hu/NTCA/1.0/common" xmlns="http://schemas.nav.gov.hu/OSA/3.0/api">
\t<common:header>
\t\t<common:requestId>{request_id}</common:requestId>
\t\t<common:timestamp>{timestamp}</common:timestamp>
\t\t<common:requestVersion>3.0</common:requestVersion>
\t\t<common:headerVersion>1.0</common:headerVersion>
\t</common:header>
\t<common:user>
\t\t<common:login>{credentials['technical_user_login']}</common:login>
\t\t<common:passwordHash cryptoType="SHA-512">{password_hash}</common:passwordHash>
\t\t<common:taxNumber>{clean_tax_number}</common:taxNumber>
\t\t<common:requestSignature cryptoType="SHA3-512">{request_signature}</common:requestSignature>
\t</common:user>
\t<software>
\t\t<softwareId>{software_id}</softwareId>
\t\t<softwareName>TransferXMLGenerator</softwareName>
\t\t<softwareOperation>LOCAL_SOFTWARE</softwareOperation>
\t\t<softwareMainVersion>1.0</softwareMainVersion>
\t\t<softwareDevName>IT Cardigan Kft.</softwareDevName>
\t\t<softwareDevContact>info@itcardigan.hu</softwareDevContact>
\t\t<softwareDevCountryCode>HU</softwareDevCountryCode>
\t\t<softwareDevTaxNumber>{dev_tax_number}</softwareDevTaxNumber>
\t</software>
\t<page>1</page>
\t<invoiceChainQuery>
\t\t<invoiceNumber>{invoice_number}</invoiceNumber>
\t\t<invoiceDirection>{direction}</invoiceDirection>
\t\t<taxNumber>{clean_supplier_tax_number}</taxNumber>
\t</invoiceChainQuery>
</QueryInvoiceChainDigestRequest>"""
        
        return xml_request
    
    def _parse_invoice_chain_digest_response(self, xml_response):
        """Parse XML response from queryInvoiceChainDigest."""
        try:
            root = ET.fromstring(xml_response)
            
            # Check for successful response first
            result_elem = root.find('.//{http://schemas.nav.gov.hu/NTCA/1.0/common}result')
            if result_elem is not None:
                func_code_elem = result_elem.find('.//{http://schemas.nav.gov.hu/NTCA/1.0/common}funcCode')
                if func_code_elem is not None and func_code_elem.text != 'OK':
                    error_code = func_code_elem.text
                    message_elem = result_elem.find('.//{http://schemas.nav.gov.hu/NTCA/1.0/common}message')
                    message = message_elem.text if message_elem is not None else "Unknown error"
                    raise Exception(f"NAV API error: {error_code} - {message}")
            
            # Extract invoice chain elements
            chain_elements = []
            
            # Look for invoiceChainElement elements in the response
            for chain_elem in root.findall('.//{http://schemas.nav.gov.hu/OSA/3.0/api}invoiceChainElement'):
                element_data = {}
                
                # Helper function to extract text from element
                def get_text(parent, tag_name):
                    namespace = 'http://schemas.nav.gov.hu/OSA/3.0/api'
                    elem = parent.find(f'.//{{{namespace}}}{tag_name}')
                    return elem.text if elem is not None else None
                
                # Extract chain digest data
                digest_elem = chain_elem.find('.//{http://schemas.nav.gov.hu/OSA/3.0/api}invoiceChainDigest')
                if digest_elem is not None:
                    element_data['invoiceNumber'] = get_text(digest_elem, 'invoiceNumber')
                    element_data['invoiceOperation'] = get_text(digest_elem, 'invoiceOperation')
                    element_data['supplierTaxNumber'] = get_text(digest_elem, 'supplierTaxNumber')
                    element_data['customerTaxNumber'] = get_text(digest_elem, 'customerTaxNumber')
                    element_data['insDate'] = get_text(digest_elem, 'insDate')
                    element_data['originalRequestVersion'] = get_text(digest_elem, 'originalRequestVersion')
                    
                # Extract audit data if present
                audit_elem = chain_elem.find('.//{http://schemas.nav.gov.hu/OSA/3.0/api}auditData')
                if audit_elem is not None:
                    element_data['transactionId'] = get_text(audit_elem, 'transactionId')
                    element_data['index'] = get_text(audit_elem, 'index')
                    element_data['source'] = get_text(audit_elem, 'source')
                    element_data['originalRequestVersion'] = get_text(audit_elem, 'originalRequestVersion')
                    element_data['insDate'] = get_text(audit_elem, 'insDate')
                    element_data['insCusUser'] = get_text(audit_elem, 'insCusUser')
                
                # Extract invoice lines information
                lines_elem = chain_elem.find('.//{http://schemas.nav.gov.hu/OSA/3.0/api}invoiceLines')
                if lines_elem is not None:
                    element_data['maxLineNumber'] = get_text(lines_elem, 'maxLineNumber')
                    element_data['lineNumbers'] = []
                    # Look for specific line numbers
                    for line_elem in lines_elem.findall('.//{http://schemas.nav.gov.hu/OSA/3.0/api}lineNumber'):
                        if line_elem.text:
                            element_data['lineNumbers'].append(int(line_elem.text))
                
                chain_elements.append(element_data)
            
            return {
                'chainElements': chain_elements,
                'raw_response': xml_response[:1000]  # First 1000 chars for debugging
            }
            
        except ET.ParseError as e:
            raise Exception(f"Failed to parse invoice chain digest response: {str(e)}")
    
    def _make_xml_request(self, endpoint, xml_data):
        """Make XML request to NAV API."""
        url = f"{self.base_url}/{endpoint}"
        
        headers = {
            'Content-Type': 'application/xml',
            'Accept': 'application/xml'
        }
        
        response = self.session.post(url, data=xml_data, headers=headers)
        response.raise_for_status()
        
        return response.text
    
    def _parse_invoice_digest_response(self, xml_response):
        """Parse XML response from queryInvoiceDigest."""
        try:
            root = ET.fromstring(xml_response)
            
            # Extract invoice digest entries
            invoices = []
            
            # Look for invoiceDigest elements (adjust namespace as needed)
            for invoice_elem in root.findall('.//{http://schemas.nav.gov.hu/OSA/3.0/api}invoiceDigest'):
                invoice_data = {}
                
                # Helper function to extract text from element
                def get_text(parent, tag_name):
                    namespace = 'http://schemas.nav.gov.hu/OSA/3.0/api'
                    elem = parent.find(f'.//{{{namespace}}}{tag_name}')
                    return elem.text if elem is not None else None
                
                # Extract ALL available fields from digest (following BIP's approach)
                invoice_data['invoiceNumber'] = get_text(invoice_elem, 'invoiceNumber')
                invoice_data['invoiceOperation'] = get_text(invoice_elem, 'invoiceOperation') 
                invoice_data['invoiceCategory'] = get_text(invoice_elem, 'invoiceCategory')
                invoice_data['invoiceIssueDate'] = get_text(invoice_elem, 'invoiceIssueDate')
                invoice_data['supplierTaxNumber'] = get_text(invoice_elem, 'supplierTaxNumber')
                invoice_data['supplierName'] = get_text(invoice_elem, 'supplierName')
                invoice_data['customerTaxNumber'] = get_text(invoice_elem, 'customerTaxNumber')
                invoice_data['customerName'] = get_text(invoice_elem, 'customerName')
                invoice_data['paymentMethod'] = get_text(invoice_elem, 'paymentMethod')
                invoice_data['paymentDate'] = get_text(invoice_elem, 'paymentDate')
                invoice_data['invoiceAppearance'] = get_text(invoice_elem, 'invoiceAppearance')
                invoice_data['source'] = get_text(invoice_elem, 'source')
                invoice_data['invoiceDeliveryDate'] = get_text(invoice_elem, 'invoiceDeliveryDate')
                invoice_data['currency'] = get_text(invoice_elem, 'currency')
                invoice_data['invoiceNetAmount'] = get_text(invoice_elem, 'invoiceNetAmount')
                invoice_data['invoiceNetAmountHUF'] = get_text(invoice_elem, 'invoiceNetAmountHUF')
                invoice_data['invoiceVatAmount'] = get_text(invoice_elem, 'invoiceVatAmount')
                invoice_data['invoiceVatAmountHUF'] = get_text(invoice_elem, 'invoiceVatAmountHUF')
                invoice_data['transactionId'] = get_text(invoice_elem, 'transactionId')
                invoice_data['index'] = get_text(invoice_elem, 'index')
                invoice_data['insDate'] = get_text(invoice_elem, 'insDate')  # NAV creation date
                invoice_data['completenessIndicator'] = get_text(invoice_elem, 'completenessIndicator')
                invoice_data['modificationIndex'] = get_text(invoice_elem, 'modificationIndex')
                invoice_data['originalInvoiceNumber'] = get_text(invoice_elem, 'originalInvoiceNumber')
                
                # Extract batch index if available
                batch_index_text = get_text(invoice_elem, 'batchIndex')
                invoice_data['batchIndex'] = int(batch_index_text) if batch_index_text else 1
                
                invoices.append(invoice_data)
            
            return invoices
            
        except ET.ParseError as e:
            raise Exception(f"Failed to parse invoice digest response: {str(e)}")
    
    def query_invoice_chain_digest(self, tax_number, invoice_number, direction='INBOUND'):
        """
        Query invoice chain digest from NAV API - this must be called BEFORE queryInvoiceData.
        
        This method gets the invoice chain metadata including version, operation, and transaction ID
        which are required for successful queryInvoiceData calls.
        
        Args:
            tax_number: Tax number of the supplier/customer (8 digits)
            invoice_number: NAV invoice number  
            direction: 'INBOUND' or 'OUTBOUND'
            
        Returns:
            Dictionary with chain data including version, operation, transactionId
        """
        self._ensure_valid_token()
        
        try:
            xml_request = self._create_query_invoice_chain_digest_xml(tax_number, invoice_number, direction)
            response = self._make_xml_request('queryInvoiceChainDigest', xml_request)
            return self._parse_invoice_chain_digest_response(response)
            
        except Exception as e:
            raise Exception(f"Query invoice chain digest failed: {str(e)}")

    def query_invoice_data(self, invoice_number, direction='INBOUND', supplier_tax_number=None, batch_index=1, version=None, operation=None):
        """
        Query detailed invoice data from NAV API using XML format.
        
        IMPORTANT: This should be called AFTER queryInvoiceChainDigest to get version/operation metadata.
        
        Args:
            invoice_number: NAV invoice number
            direction: 'INBOUND' or 'OUTBOUND'
            supplier_tax_number: Tax number of the supplier (8 digits)
            batch_index: Batch index (default 1)
            version: NAV API version from chain digest (optional)
            operation: Invoice operation from chain digest (optional)
            
        Returns:
            Dictionary with detailed invoice data including XML content
        """
        self._ensure_valid_token()
        
        try:
            xml_request = self._create_query_invoice_data_xml(invoice_number, direction, supplier_tax_number, batch_index)
            response = self._make_xml_request('queryInvoiceData', xml_request)
            return self._parse_invoice_data_response(response)
            
        except Exception as e:
            raise Exception(f"Query invoice data failed: NAV API request failed: {str(e)}")
    
    def _create_query_invoice_data_xml(self, invoice_number, direction, supplier_tax_number, batch_index):
        """Create XML request for queryInvoiceData based on NAV 3.0 specification."""
        
        # Use the existing credential management methods
        credentials = self._get_decrypted_credentials()
        request_id = self._generate_request_id()
        timestamp = self._generate_timestamp()
        
        # Create password hash and request signature using existing methods
        password_hash = self._hash_password(credentials['technical_user_password'])
        request_signature = self._generate_request_signature({
            'requestId': request_id,
            'timestamp': timestamp
        })
        
        # Clean tax numbers for query requests (8 digits max, no dashes)
        clean_tax_number = self._clean_tax_number_for_query(self.config.tax_number)
        clean_supplier_tax_number = self._clean_tax_number_for_query(supplier_tax_number) if supplier_tax_number else ""
        
        # Create XML matching the working sample structure  
        dev_tax_number = self.config.tax_number  # Keep full format for software block
        software_id = f"HU{clean_tax_number}TXG00001"  # Match BIP's pattern
        
        xml_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<QueryInvoiceDataRequest xmlns:common="http://schemas.nav.gov.hu/NTCA/1.0/common" xmlns="http://schemas.nav.gov.hu/OSA/3.0/api">
\t<common:header>
\t\t<common:requestId>{request_id}</common:requestId>
\t\t<common:timestamp>{timestamp}</common:timestamp>
\t\t<common:requestVersion>3.0</common:requestVersion>
\t\t<common:headerVersion>1.0</common:headerVersion>
\t</common:header>
\t<common:user>
\t\t<common:login>{credentials['technical_user_login']}</common:login>
\t\t<common:passwordHash cryptoType="SHA-512">{password_hash}</common:passwordHash>
\t\t<common:taxNumber>{clean_tax_number}</common:taxNumber>
\t\t<common:requestSignature cryptoType="SHA3-512">{request_signature}</common:requestSignature>
\t</common:user>
\t<software>
\t\t<softwareId>{software_id}</softwareId>
\t\t<softwareName>TransferXMLGenerator</softwareName>
\t\t<softwareOperation>LOCAL_SOFTWARE</softwareOperation>
\t\t<softwareMainVersion>1.0</softwareMainVersion>
\t\t<softwareDevName>IT Cardigan Kft.</softwareDevName>
\t\t<softwareDevContact>info@itcardigan.hu</softwareDevContact>
\t\t<softwareDevCountryCode>HU</softwareDevCountryCode>
\t\t<softwareDevTaxNumber>{dev_tax_number}</softwareDevTaxNumber>
\t</software>
\t<invoiceNumberQuery>
\t\t<invoiceNumber>{invoice_number}</invoiceNumber>
\t\t<invoiceDirection>{direction}</invoiceDirection>"""
        
        # Add supplier tax number if provided
        if clean_supplier_tax_number:
            xml_request += f"""
\t\t<supplierTaxNumber>{clean_supplier_tax_number}</supplierTaxNumber>"""
        
        xml_request += """
\t</invoiceNumberQuery>
</QueryInvoiceDataRequest>"""
        
        return xml_request
    
    def _parse_invoice_data_response(self, xml_response):
        """Parse XML response from queryInvoiceData."""
        try:
            root = ET.fromstring(xml_response)
            
            # Check for successful response first
            result_elem = root.find('.//{http://schemas.nav.gov.hu/NTCA/1.0/common}result')
            if result_elem is not None:
                func_code_elem = result_elem.find('.//{http://schemas.nav.gov.hu/NTCA/1.0/common}funcCode')
                if func_code_elem is not None and func_code_elem.text != 'OK':
                    error_code = func_code_elem.text
                    message_elem = result_elem.find('.//{http://schemas.nav.gov.hu/NTCA/1.0/common}message')
                    message = message_elem.text if message_elem is not None else "Unknown error"
                    raise Exception(f"NAV API error: {error_code} - {message}")
            
            # Check if we have invoiceDataResult (the new successful format)
            data_result_elem = root.find('.//{http://schemas.nav.gov.hu/OSA/3.0/api}invoiceDataResult')
            if data_result_elem is not None:
                # Extract the base64 encoded invoice XML
                invoice_data_elem = data_result_elem.find('.//{http://schemas.nav.gov.hu/OSA/3.0/api}invoiceData')
                audit_data_elem = data_result_elem.find('.//{http://schemas.nav.gov.hu/OSA/3.0/api}auditData')
                
                invoice_data = {}
                
                if invoice_data_elem is not None:
                    # Decode base64 invoice XML data
                    import base64
                    try:
                        encoded_xml = invoice_data_elem.text
                        decoded_xml_bytes = base64.b64decode(encoded_xml)
                        decoded_xml = decoded_xml_bytes.decode('utf-8')
                        
                        # Store the raw XML data
                        invoice_data['nav_invoice_xml'] = decoded_xml
                        
                        # Parse the decoded XML to extract financial data
                        import xml.etree.ElementTree as XMLParser
                        xml_root = XMLParser.fromstring(decoded_xml)
                        
                        # Extract amounts from the decoded XML
                        gross_amount_elem = xml_root.find('.//{http://schemas.nav.gov.hu/OSA/3.0/data}invoiceGrossAmount')
                        if gross_amount_elem is not None:
                            invoice_data['gross_amount'] = float(gross_amount_elem.text)
                        
                        # Extract VAT content gross amount as fallback
                        vat_gross_elem = xml_root.find('.//{http://schemas.nav.gov.hu/OSA/3.0/data}vatContentGrossAmount')
                        if vat_gross_elem is not None and 'gross_amount' not in invoice_data:
                            invoice_data['gross_amount'] = float(vat_gross_elem.text)
                            
                        # Extract line gross amount as another fallback
                        line_gross_elem = xml_root.find('.//{http://schemas.nav.gov.hu/OSA/3.0/data}lineGrossAmountSimplified')
                        if line_gross_elem is not None and 'gross_amount' not in invoice_data:
                            invoice_data['gross_amount'] = float(line_gross_elem.text)
                        
                        # Extract invoice number
                        inv_num_elem = xml_root.find('.//{http://schemas.nav.gov.hu/OSA/3.0/data}invoiceNumber')
                        if inv_num_elem is not None:
                            invoice_data['invoice_number'] = inv_num_elem.text
                        
                        # Extract issue date
                        issue_date_elem = xml_root.find('.//{http://schemas.nav.gov.hu/OSA/3.0/data}invoiceIssueDate')
                        if issue_date_elem is not None:
                            invoice_data['issue_date'] = issue_date_elem.text
                            
                        # Extract supplier name
                        supplier_name_elem = xml_root.find('.//{http://schemas.nav.gov.hu/OSA/3.0/data}supplierName')
                        if supplier_name_elem is not None:
                            invoice_data['supplier_name'] = supplier_name_elem.text
                            
                        # Extract customer name  
                        customer_name_elem = xml_root.find('.//{http://schemas.nav.gov.hu/OSA/3.0/data}customerName')
                        if customer_name_elem is not None:
                            invoice_data['customer_name'] = customer_name_elem.text
                            
                        # Extract currency
                        currency_elem = xml_root.find('.//{http://schemas.nav.gov.hu/OSA/3.0/data}currencyCode')
                        if currency_elem is not None:
                            invoice_data['currency'] = currency_elem.text
                        else:
                            invoice_data['currency'] = 'HUF'
                            
                    except Exception as e:
                        logger.warning(f"Failed to decode invoice XML data: {str(e)}")
                        invoice_data['nav_invoice_xml'] = encoded_xml  # Store encoded if decode fails
                
                # Extract audit data
                if audit_data_elem is not None:
                    def get_audit_text(tag_name):
                        elem = audit_data_elem.find(f'.//{{{namespaces_api}}}{tag_name}')
                        return elem.text if elem is not None else None
                    
                    namespaces_api = 'http://schemas.nav.gov.hu/OSA/3.0/api'
                    invoice_data['transaction_id'] = get_audit_text('transactionId')
                    invoice_data['nav_index'] = get_audit_text('index')
                    invoice_data['nav_source'] = get_audit_text('source')
                    invoice_data['original_request_version'] = get_audit_text('originalRequestVersion')
                    invoice_data['nav_creation_date'] = get_audit_text('insdate')
                    invoice_data['ins_cus_user'] = get_audit_text('insCusUser')
                
                return invoice_data
            
            # Fallback: try old parsing method for backwards compatibility
            invoice_data = {}
            
            # Look for invoice elements in the response  
            invoice_elem = root.find('.//{http://schemas.nav.gov.hu/OSA/3.0/data}invoiceData')
            if invoice_elem is None:
                # Try alternative path
                invoice_elem = root.find('.//{http://schemas.nav.gov.hu/OSA/3.0/api}invoiceData')
                
            if invoice_elem is not None:
                # Extract basic invoice information
                invoice_number_elem = invoice_elem.find('.//{http://schemas.nav.gov.hu/OSA/3.0/data}invoiceNumber')
                if invoice_number_elem is not None:
                    invoice_data['invoice_number'] = invoice_number_elem.text
                
                # Extract issue date
                issue_date_elem = invoice_elem.find('.//{http://schemas.nav.gov.hu/OSA/3.0/data}invoiceIssueDate')
                if issue_date_elem is not None:
                    invoice_data['issue_date'] = issue_date_elem.text
                
                # Extract supplier info
                supplier_name_elem = invoice_elem.find('.//{http://schemas.nav.gov.hu/OSA/3.0/data}supplierName')
                if supplier_name_elem is not None:
                    invoice_data['supplier_name'] = supplier_name_elem.text
                
                supplier_tax_elem = invoice_elem.find('.//{http://schemas.nav.gov.hu/OSA/3.0/data}supplierTaxNumber')
                if supplier_tax_elem is not None:
                    invoice_data['supplier_tax_number'] = supplier_tax_elem.text
                
                # Extract customer info  
                customer_name_elem = invoice_elem.find('.//{http://schemas.nav.gov.hu/OSA/3.0/data}customerName')
                if customer_name_elem is not None:
                    invoice_data['customer_name'] = customer_name_elem.text
                
                # Extract amounts
                net_amount_elem = invoice_elem.find('.//{http://schemas.nav.gov.hu/OSA/3.0/data}invoiceNetAmount')
                if net_amount_elem is not None:
                    invoice_data['net_amount'] = float(net_amount_elem.text) if net_amount_elem.text else 0.0
                    
                gross_amount_elem = invoice_elem.find('.//{http://schemas.nav.gov.hu/OSA/3.0/data}invoiceGrossAmount') 
                if gross_amount_elem is not None:
                    invoice_data['gross_amount'] = float(gross_amount_elem.text) if gross_amount_elem.text else 0.0
                
                # Extract currency
                currency_elem = invoice_elem.find('.//{http://schemas.nav.gov.hu/OSA/3.0/data}currencyCode')
                if currency_elem is not None:
                    invoice_data['currency'] = currency_elem.text
                else:
                    invoice_data['currency'] = 'HUF'  # Default to HUF
            
            # If we don't have critical data, provide defaults to avoid NULL constraint errors
            if 'invoice_number' not in invoice_data:
                # NAV response doesn't contain detailed invoice data
                # This is normal - many detailed queries return empty results
                # Return None to indicate no detailed data available
                return None
                
            if 'issue_date' not in invoice_data:
                # Use today's date as fallback for issue_date to avoid NULL constraint
                from datetime import date
                invoice_data['issue_date'] = date.today().isoformat()
                
            if 'net_amount' not in invoice_data:
                invoice_data['net_amount'] = 0.0
                
            if 'gross_amount' not in invoice_data:
                invoice_data['gross_amount'] = 0.0
            
            # Also keep raw response for debugging
            invoice_data['raw_response'] = xml_response[:1000]  # First 1000 chars for debugging
            
            return invoice_data
            
        except ET.ParseError as e:
            raise Exception(f"Failed to parse invoice data XML response: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to parse invoice data response: {str(e)}")
    
    def test_connection(self):
        """
        Test NAV API connection and authentication.
        
        Returns:
            Dictionary with connection test results
        """
        try:
            # Test token exchange
            token = self.token_exchange()
            
            # Test basic query (get first page of outbound invoices)
            digest_response = self.query_invoice_digest(
                direction='OUTBOUND', 
                page=1
            )
            
            return {
                'success': True,
                'message': 'NAV API connection successful',
                'token_received': bool(token),
                'api_environment': self.config.api_environment,
                'base_url': self.base_url
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'NAV API connection failed: {str(e)}',
                'api_environment': self.config.api_environment,
                'base_url': self.base_url
            }