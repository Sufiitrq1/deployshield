import os
import logging
from twilio.rest import Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DeployShield.Notifier")

def send_whatsapp_alert(to_number: str, deployment_name: str, status: str, report_path: str = None) -> bool:
    """
    Dispatches a structured operational alert via Twilio WhatsApp API.
    Falls back to console logging if environment variables are missing.
    """
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    from_number = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

    # Format the message body with actionable clear markers
    if status.upper() == "SUCCESS":
        message_body = (
            f"✅ *DeployShield: Deployment Passed*\n\n"
            f"• *Deployment:* {deployment_name}\n"
            f"• *Status:* Verification Successful\n"
            f"• *Action:* Traffic route verified healthy."
        )
    else:
        message_body = (
            f"🚨 *DeployShield: Emergency Rollback Triggered*\n\n"
            f"• *Deployment:* {deployment_name}\n"
            f"• *Status:* Anomaly Detected\n"
            f"• *Action:* Infrastructure automatically reverted to previous stable ReplicaSet.\n"
            f"• *Trace Report:* {report_path if report_path else 'Generated locally'}"
        )

    # Fallback Mechanism if Credentials are Empty
    if not account_sid or not auth_token:
        logger.warning("Twilio credentials missing. Falling back to local console dispatch simulation:")
        print(f"\n--- [SIMULATED WHATSAPP ALERT TO {to_number}] ---\n{message_body}\n-----------------------------------------\n")
        return True

    try:
        client = Client(account_sid, auth_token)
        
        # Ensure 'whatsapp:' prefixing conforms to Twilio requirements
        formatted_to = to_number if to_number.startswith("whatsapp:") else f"whatsapp:{to_number}"
        
        client.messages.create(
            body=message_body,
            from_=from_number,
            to=formatted_to
        )
        logger.info("WhatsApp alert dispatched successfully via Twilio.")
        return True
    except Exception as e:
        logger.error(f"Failed to transmit WhatsApp payload via Twilio API: {e}")
        # Secondary fallback to terminal to protect core runtime loop execution
        print(f"\n--- [CRITICAL FALLBACK ALERT TO {to_number}] ---\n{message_body}\n-----------------------------------------\n")
        return False