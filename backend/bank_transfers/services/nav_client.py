import requests
import hashlib
import hmac
import base64
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from django.conf import settings
from .credential_manager import CredentialManager
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


class NavApiClient:
    """
    Hungarian NAV Online Invoice API client.
    
    Handles authentication, request signing, and API communication
    with the NAV Online Invoice system for invoice synchronization.
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
        
        # Configure client certificate authentication if available
        self._configure_client_certificate()
        
        # Current authentication token
        self._auth_token = None
        self._token_expiry = None
    
    def _get_base_url(self):
        """Get the appropriate NAV API base URL based on environment."""
        if self.config.api_environment == 'production':
            return 'https://api.onlineszamla.nav.gov.hu/invoiceService/v3'
        else:
            return 'https://api-test.onlineszamla.nav.gov.hu/invoiceService/v3'
    
    def _configure_client_certificate(self):
        """Configure client certificate authentication if available."""
        if self.config.client_certificate:
            try:
                cert_path = self.config.client_certificate.path
                cert_password = self.config.get_decrypted_certificate_password()
                
                if cert_password:
                    # For .p12/.pfx files with password
                    self.session.cert = (cert_path, cert_password)
                else:
                    # For certificate files without password
                    self.session.cert = cert_path
                    
                print(f"✅ Client certificate configured: {cert_path}")
            except Exception as e:
                print(f"⚠️ Failed to configure client certificate: {e}")
        else:
            print("ℹ️ No client certificate configured (using credential-only authentication)")
    
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
            print(f"AES-128 ECB decryption failed: {e}")
            # Return original data if decryption fails
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
            print(f"AES-128 ECB processed exchange key: {processed_exchange_key}")
        
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
        
        # For debugging - can be removed in production
        # print(f"Sending XML to {url}:")
        # print(xml_data.decode('utf-8'))
        
        try:
            response = self.session.post(
                url,
                data=xml_data,
                headers={
                    'Content-Type': 'application/xml',
                    'Accept': 'application/xml'
                }
            )
            
            # Log errors for debugging
            if response.status_code != 200:
                print(f"NAV API Error {response.status_code}: {response.text[:200]}...")
            
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
                'softwareDevContact': 'support@itcardigan.hu',
                'softwareDevTaxNumber': credentials['tax_number']
            }
        }
        
        try:
            response = self._make_api_request('tokenExchange', request_data)
            
            # Extract token from response
            if 'result' in response and 'encodedExchangeToken' in response['result']:
                self._auth_token = response['result']['encodedExchangeToken']
                # Set token expiry (NAV tokens typically expire in 5 minutes)
                self._token_expiry = datetime.now(timezone.utc).timestamp() + 300
                return self._auth_token
            else:
                raise Exception("Invalid token exchange response")
                
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
        Query invoice digest from NAV API.
        
        Args:
            direction: 'INBOUND' or 'OUTBOUND'
            page: Page number for pagination (1-based)
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            
        Returns:
            Dictionary with invoice digest data
        """
        self._ensure_valid_token()
        
        request_data = self._create_base_request('queryInvoiceDigest')
        
        # Add query parameters
        query_params = {
            'invoiceDirection': direction,
            'page': page
        }
        
        if date_from:
            query_params['dateTimeFrom'] = f"{date_from}T00:00:00.000Z"
        if date_to:
            query_params['dateTimeTo'] = f"{date_to}T23:59:59.999Z"
        
        request_data['invoiceDigestRequest'] = query_params
        request_data['exchangeToken'] = self._auth_token
        
        try:
            response = self._make_api_request('queryInvoiceDigest', request_data)
            return response
            
        except Exception as e:
            raise Exception(f"Query invoice digest failed: {str(e)}")
    
    def query_invoice_data(self, invoice_number, direction='OUTBOUND'):
        """
        Query detailed invoice data from NAV API.
        
        Args:
            invoice_number: NAV invoice number
            direction: 'INBOUND' or 'OUTBOUND'
            
        Returns:
            Dictionary with detailed invoice data
        """
        self._ensure_valid_token()
        
        request_data = self._create_base_request('queryInvoiceData')
        
        # Add query parameters
        request_data['invoiceDataRequest'] = {
            'invoiceNumber': invoice_number,
            'invoiceDirection': direction
        }
        request_data['exchangeToken'] = self._auth_token
        
        try:
            response = self._make_api_request('queryInvoiceData', request_data)
            return response
            
        except Exception as e:
            raise Exception(f"Query invoice data failed: {str(e)}")
    
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