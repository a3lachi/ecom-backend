import base64, requests
import logging
from typing import Dict, Optional
from decouple import config

logger = logging.getLogger(__name__)

# PayPal environment variables
BASE = config("PAYPAL_BASE", default="https://api-m.sandbox.paypal.com")
CLIENT_ID = config("PAYPAL_CLIENT_ID", default=None)
SECRET = config("PAYPAL_CLIENT_SECRET", default=None)
WEBHOOK_ID = config("PAYPAL_WEBHOOK_ID", default=None)

class PayPalError(Exception):
    """Custom PayPal API exception"""
    pass

def _get_access_token() -> str:
    """Get OAuth2 access token from PayPal"""
    if not CLIENT_ID or not SECRET:
        raise PayPalError("PayPal credentials not configured")
    
    try:
        # OAuth2 client_credentials
        auth = base64.b64encode(f"{CLIENT_ID}:{SECRET}".encode()).decode()
        r = requests.post(
            f"{BASE}/v1/oauth2/token",
            headers={"Authorization": f"Basic {auth}"},
            data={"grant_type": "client_credentials"},
            timeout=15,
        )
        r.raise_for_status()
        return r.json()["access_token"]
    except requests.RequestException as e:
        logger.error(f"PayPal OAuth error: {e}")
        raise PayPalError(f"Failed to get PayPal access token: {e}")

def create_order(amount: float, currency: str, order_number: str, 
                return_url: Optional[str] = None, cancel_url: Optional[str] = None) -> Dict:
    """Create a PayPal order for payment"""
    try:
        token = _get_access_token()
        payload = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "reference_id": order_number,
                "amount": {"currency_code": currency, "value": f"{amount:.2f}"}
            }],
        }
        # If you use redirect/approval links:
        if return_url and cancel_url:
            payload["application_context"] = {
                "return_url": return_url, 
                "cancel_url": cancel_url,
                "user_action": "PAY_NOW"  # Skip review step
            }

        r = requests.post(
            f"{BASE}/v2/checkout/orders",
            json=payload,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=15,
        )
        if r.status_code != 201:
            error_response = r.text
            logger.error(f"PayPal create order error {r.status_code}: {error_response}")
            raise PayPalError(f"PayPal order creation failed ({r.status_code}): {error_response}")
        
        response_data = r.json()
        logger.info(f"PayPal order created: {response_data.get('id')}")
        return response_data  # contains id + links
    except requests.RequestException as e:
        logger.error(f"PayPal create order error: {e}")
        raise PayPalError(f"Failed to create PayPal order: {e}")

def capture_order(order_id: str) -> Dict:
    """Capture an approved PayPal order"""
    try:
        token = _get_access_token()
        r = requests.post(
            f"{BASE}/v2/checkout/orders/{order_id}/capture",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=15,
        )
        r.raise_for_status()
        response_data = r.json()
        logger.info(f"PayPal order captured: {order_id}")
        return response_data
    except requests.RequestException as e:
        logger.error(f"PayPal capture order error: {e}")
        raise PayPalError(f"Failed to capture PayPal order: {e}")


def get_order_details(order_id: str) -> Dict:
    """Get details of a PayPal order"""
    try:
        token = _get_access_token()
        r = requests.get(
            f"{BASE}/v2/checkout/orders/{order_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        logger.error(f"PayPal get order error: {e}")
        raise PayPalError(f"Failed to get PayPal order details: {e}")


def verify_webhook(headers: dict, body: dict) -> bool:
    """
    Server-side verification via PayPal's verify-webhook-signature endpoint.
    Returns True only when verification_status == 'SUCCESS'.
    """
    if not WEBHOOK_ID:
        raise PayPalError("PayPal webhook ID not configured")
    
    token = _get_access_token()
    payload = {
        "auth_algo": headers.get("PAYPAL-AUTH-ALGO"),
        "cert_url": headers.get("PAYPAL-CERT-URL"),
        "transmission_id": headers.get("PAYPAL-TRANSMISSION-ID"),
        "transmission_sig": headers.get("PAYPAL-TRANSMISSION-SIG"),
        "transmission_time": headers.get("PAYPAL-TRANSMISSION-TIME"),
        "webhook_id": WEBHOOK_ID,           # YOUR webhook id from the dashboard
        "webhook_event": body,              # the exact JSON payload PayPal sent
    }
    r = requests.post(
        f"{BASE}/v1/notifications/verify-webhook-signature",
        json=payload,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=15,
    )
    r.raise_for_status()
    return r.json().get("verification_status") == "SUCCESS"