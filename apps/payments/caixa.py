import hashlib
import hmac
import base64
import json
import logging
from typing import Dict, Optional
from decouple import config

logger = logging.getLogger(__name__)

# CaixaBank/Redsys environment variables
ENVIRONMENT = config("CAIXA_ENVIRONMENT", default="TEST")
MERCHANT_CODE = config("CAIXA_MERCHANT_CODE", default=None)
TERMINAL = config("CAIXA_TERMINAL", default="1")
CURRENCY = config("CAIXA_CURRENCY", default="978")  # 978 = EUR
SECRET_KEY = config("CAIXA_SECRET_KEY", default=None)
SIGNATURE_VERSION = config("CAIXA_SIGNATURE_VERSION", default="HMAC_SHA512_V2")
BASE_URL = config("CAIXA_BASE_URL", default="https://sis-t.redsys.es:25443")

class CaixaError(Exception):
    """Custom CaixaBank/Redsys API exception"""
    pass

def _encode_merchant_parameters(parameters: Dict) -> str:
    """Encode merchant parameters to Base64"""
    json_data = json.dumps(parameters, separators=(',', ':'))
    return base64.b64encode(json_data.encode('utf-8')).decode('utf-8')

def _generate_signature(merchant_parameters: str, secret_key: str) -> str:
    """Generate signature for Redsys - supports both SHA256 and SHA512 versions"""
    if not secret_key:
        raise CaixaError("CaixaBank secret key not configured")
    
    # Decode merchant parameters to get the order number for key derivation
    import json
    
    decoded_params = base64.b64decode(merchant_parameters).decode('utf-8')
    params_dict = json.loads(decoded_params)
    order_number = params_dict.get("DS_MERCHANT_ORDER", "")
    
    # Decode the secret key from Base64
    merchant_key = base64.b64decode(secret_key)
    
    if SIGNATURE_VERSION == "HMAC_SHA512_V2":
        # Use AES-CBC for SHA512 version
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import pad
        
        # AES requires 16, 24, or 32 byte keys
        if len(merchant_key) == 24:
            # Extend 24-byte key to 32 bytes for AES-256
            aes_key = merchant_key + merchant_key[:8]
        elif len(merchant_key) < 32:
            aes_key = merchant_key + b'\x00' * (32 - len(merchant_key))
        else:
            aes_key = merchant_key[:32]
        
        # Pad order to 16-byte blocks for AES
        order_bytes = order_number.encode('utf-8')
        order_padded = pad(order_bytes, 16)
        
        # Create derived key using AES-CBC with zero IV
        iv = b'\x00' * 16
        cipher = AES.new(aes_key, AES.MODE_CBC, iv)
        derived_key = cipher.encrypt(order_padded)[:32]  # Use first 32 bytes
        
        # Generate HMAC-SHA512 signature
        signature = hmac.new(derived_key, merchant_parameters.encode('ascii'), hashlib.sha512)
        return base64.b64encode(signature.digest()).decode('ascii')
    
    else:
        # Use 3DES-CBC for SHA256 version (original implementation)
        from Crypto.Cipher import DES3
        
        # Zero padding to 8-byte blocks
        order_bytes = order_number.encode('utf-8')
        pad_len = (8 - (len(order_bytes) % 8)) % 8
        order_padded = order_bytes + b'\x00' * pad_len
        
        # Create derived key using 3DES-CBC with zero IV
        iv = b'\x00' * 8
        cipher = DES3.new(merchant_key, DES3.MODE_CBC, iv)
        derived_key = cipher.encrypt(order_padded)
        
        # Generate HMAC-SHA256 signature
        signature = hmac.new(derived_key, merchant_parameters.encode('ascii'), hashlib.sha256)
        return base64.b64encode(signature.digest()).decode('ascii')

def _verify_signature(merchant_parameters: str, signature: str, secret_key: str) -> bool:
    """Verify incoming signature from Redsys"""
    try:
        expected_signature = _generate_signature(merchant_parameters, secret_key)
        return hmac.compare_digest(expected_signature, signature)
    except Exception as e:
        logger.error(f"CaixaBank signature verification error: {e}")
        return False

def create_payment_form(amount: float, order_number: str, merchant_url: str, 
                       success_url: str, error_url: str, 
                       customer_name: Optional[str] = None, currency: str = "EUR") -> Dict:
    """
    Create CaixaBank payment form data for TPV Virtual integration.
    Returns form data that should be POSTed to Redsys gateway.
    """
    if not MERCHANT_CODE or not SECRET_KEY:
        raise CaixaError("CaixaBank credentials not configured")
    
    # CaixaBank only accepts EUR currency
    if currency != "EUR":
        raise CaixaError(f"CaixaBank only accepts EUR currency, received: {currency}")
    
    # Convert amount to cents (Redsys expects integer cents)
    amount_cents = int(amount * 100)
    
    # Format order number for Redsys (4-12 chars, first 4 must be numeric)
    import re
    import time
    
    # Create a Redsys-compliant order number
    # Use last 4 digits of timestamp + last 6 chars of original order (alphanumeric only)
    timestamp = str(int(time.time()))[-4:]  # Last 4 digits of timestamp (numeric)
    order_suffix = re.sub(r'[^A-Z0-9]', '', order_number.upper())[-6:]  # Last 6 alphanumeric chars
    redsys_order = timestamp + order_suffix
    redsys_order = redsys_order[:12]  # Max 12 characters
    
    logger.info(f"Original order: {order_number} -> Redsys order: {redsys_order}")
    
    # Merchant parameters
    merchant_parameters = {
        "DS_MERCHANT_AMOUNT": str(amount_cents),
        "DS_MERCHANT_ORDER": redsys_order,
        "DS_MERCHANT_MERCHANTCODE": MERCHANT_CODE,
        "DS_MERCHANT_CURRENCY": CURRENCY,
        "DS_MERCHANT_TRANSACTIONTYPE": "0",  # 0 = Authorization
        "DS_MERCHANT_TERMINAL": TERMINAL,
        "DS_MERCHANT_MERCHANTURL": merchant_url,  # Webhook URL
        "DS_MERCHANT_URLOK": success_url,
        "DS_MERCHANT_URLKO": error_url,
        "DS_MERCHANT_PRODUCTDESCRIPTION": "Online Payment",  # Required field
    }
    
    # Add customer name if provided
    if customer_name:
        merchant_parameters["DS_MERCHANT_TITULAR"] = customer_name[:60]  # Max 60 chars
    
    # Encode parameters
    encoded_parameters = _encode_merchant_parameters(merchant_parameters)
    
    # Generate signature
    signature = _generate_signature(encoded_parameters, SECRET_KEY)
    
    # Return form data for frontend
    form_data = {
        "Ds_SignatureVersion": SIGNATURE_VERSION,
        "Ds_MerchantParameters": encoded_parameters,
        "Ds_Signature": signature,
        "payment_url": f"{BASE_URL}/sis/realizarPago"
    }
    
    logger.info(f"CaixaBank payment form created for order: {order_number}")
    return form_data

def process_webhook_response(form_data: Dict) -> Dict:
    """
    Process webhook response from Redsys after payment.
    Returns parsed payment information.
    """
    try:
        # Extract parameters
        merchant_parameters = form_data.get("Ds_MerchantParameters")
        signature = form_data.get("Ds_Signature")
        signature_version = form_data.get("Ds_SignatureVersion")
        
        if not merchant_parameters or not signature:
            raise CaixaError("Missing required webhook parameters")
        
        # Verify signature
        if not _verify_signature(merchant_parameters, signature, SECRET_KEY):
            raise CaixaError("Invalid webhook signature")
        
        # Decode merchant parameters
        decoded_data = base64.b64decode(merchant_parameters).decode('utf-8')
        payment_data = json.loads(decoded_data)
        
        # Extract key payment information
        response_code = payment_data.get("Ds_Response")
        order_number = payment_data.get("Ds_Order")
        amount = payment_data.get("Ds_Amount")
        currency = payment_data.get("Ds_Currency")
        authorization_code = payment_data.get("Ds_AuthorisationCode")
        
        # Determine payment status
        # Response codes 0000-0099 indicate successful transactions
        if response_code and response_code.isdigit():
            response_int = int(response_code)
            is_successful = 0 <= response_int <= 99
        else:
            is_successful = False
        
        processed_data = {
            "order_number": order_number,
            "amount": float(amount) / 100 if amount else 0,  # Convert from cents
            "currency": currency,
            "response_code": response_code,
            "authorization_code": authorization_code,
            "is_successful": is_successful,
            "raw_data": payment_data
        }
        
        logger.info(f"CaixaBank webhook processed for order: {order_number}, success: {is_successful}")
        return processed_data
        
    except Exception as e:
        logger.error(f"CaixaBank webhook processing error: {e}")
        raise CaixaError(f"Failed to process webhook response: {e}")

def get_response_code_description(response_code: str) -> str:
    """Get human-readable description for Redsys response codes"""
    response_codes = {
        "0000": "Transaction approved",
        "0001": "Refer to card issuer",
        "0002": "Refer to card issuer, special condition",
        "0003": "Invalid merchant",
        "0004": "Pick up card",
        "0005": "Do not honour",
        "0006": "Error",
        "0007": "Pick up card, special condition",
        "0008": "Honour with identification",
        "0009": "Request in progress",
        "0010": "Approved for partial amount",
        "0011": "Approved (VIP)",
        "0012": "Invalid transaction",
        "0013": "Invalid amount",
        "0014": "Invalid card number",
        "0015": "No such issuer",
        "0016": "Approved, update track 3",
        "0017": "Customer cancellation",
        "0018": "Customer dispute",
        "0019": "Re-enter transaction",
        "0020": "Invalid response",
        "0021": "No action taken",
        "0022": "Suspected malfunction",
        "0023": "Unacceptable transaction fee",
        "0024": "File update not supported",
        "0025": "Unable to locate record",
        "0026": "Duplicate record",
        "0027": "File update field edit error",
        "0028": "File update file locked",
        "0029": "File update failed",
        "0030": "Format error",
        "0031": "Bank not supported",
        "0032": "Completed partially",
        "0033": "Expired card",
        "0034": "Suspected fraud",
        "0035": "Pick up card",
        "0036": "Restricted card",
        "0037": "Call acquirer security",
        "0038": "PIN tries exceeded",
        "0039": "No credit account",
        "0040": "Function not supported",
        "0041": "Lost card",
        "0042": "No universal account",
        "0043": "Stolen card",
        "0044": "No investment account",
        "0051": "Insufficient funds",
        "0052": "No checking account",
        "0053": "No savings account",
        "0054": "Expired card",
        "0055": "Incorrect PIN",
        "0056": "No card record",
        "0057": "Function not permitted to cardholder",
        "0058": "Function not permitted to terminal",
        "0059": "Suspected fraud",
        "0060": "Card acceptor contact acquirer",
        "0061": "Exceeds withdrawal amount limit",
        "0062": "Restricted card",
        "0063": "Security violation",
        "0064": "Original amount incorrect",
        "0065": "Exceeds withdrawal frequency limit",
        "0066": "Card acceptor call acquirer security",
        "0067": "Hard capture",
        "0068": "Response received too late",
        "0070": "Contact card issuer",
        "0071": "PIN not changed",
        "0072": "No messages",
        "0073": "PIN tries exceeded",
        "0074": "Cryptographic error",
        "0075": "Reversal not processed",
        "0076": "Transaction processing error",
        "0077": "Card cancelled",
        "0078": "Blocked card",
        "0079": "Query not answered",
        "0080": "PIN verification not possible",
        "0081": "Cryptographic error in PIN",
        "0082": "Negative CAM, dCVV, iCVV or CVV results",
        "0083": "No reason to deny",
        "0084": "Issuer unavailable",
        "0085": "Not declined",
        "0086": "PIN tries exceeded",
        "0087": "Purchase amount only",
        "0088": "Cryptographic error",
        "0089": "MAC error",
        "0090": "Cutoff in progress",
        "0091": "Issuer unavailable",
        "0092": "Invalid routing",
        "0093": "Violation of law",
        "0094": "Duplicate transaction",
        "0095": "Reconcile error",
        "0096": "System malfunction",
        "0097": "Reconciliation totals reset",
        "0098": "MAC error",
        "0099": "Reserved for national use",
    }
    
    return response_codes.get(response_code, f"Unknown response code: {response_code}")