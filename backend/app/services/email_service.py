"""
EMAIL SERVICE (The "Post Office")
====================================
This service sends email notifications when contracts are expiring.

HOW EMAIL WORKS ON THE INTERNET:
=================================
Sending an email from code works just like sending a physical letter:

1. You write the letter (compose the email: subject, body, recipient)
2. You put it in an envelope (format it as an email message)
3. You take it to the post office (connect to an SMTP server)
4. The post office delivers it (SMTP server routes it to the recipient)

SMTP = Simple Mail Transfer Protocol
It's the "language" that email servers speak to each other.
When you send an email from Gmail, your computer talks SMTP to Google's server.

CONFIGURATION:
We use environment variables so email settings aren't hardcoded:
- SMTP_HOST: The email server address (e.g., smtp.gmail.com)
- SMTP_PORT: The "door number" on the server (587 for TLS)
- SMTP_USER: Your email address (for authentication)
- SMTP_PASSWORD: Your email password or "app password"
- SMTP_FROM: The "From" address on outgoing emails

WHY ENVIRONMENT VARIABLES?
Passwords should NEVER be in code files. Environment variables are like
a locked cabinet — the server knows them, but they don't appear in your
source code. If someone sees your code, they don't see passwords.

TESTING WITHOUT REAL EMAIL:
For development, we log emails to the console instead of actually sending them.
Set SMTP_HOST to empty or don't set it at all — the system will print
the email content so you can verify it works without needing a real mail server.
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

# Read email settings from environment variables.
# If not set, we'll use "dev mode" (log to console instead of sending).
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "noreply@vendormanagement.com")


def send_expiry_notification_email(
    recipient_email: str,
    contract_title: str,
    vendor_name: str,
    days_remaining: int,
    end_date_str: str,
    notification_type: str,
) -> bool:
    """
    Send an email about an expiring contract.

    Returns True if the email was sent (or logged) successfully.
    Returns False if something went wrong.

    THE EMAIL STRUCTURE:
    - Subject: "[URGENT] Contract Expiring: Annual IT Support"
    - Body: HTML formatted with contract details and a call to action
    """

    # Determine urgency for the subject line
    if days_remaining <= 0:
        urgency_tag = "EXPIRED"
        urgency_color = "#dc3545"  # Red
    elif days_remaining <= 30:
        urgency_tag = "URGENT"
        urgency_color = "#dc3545"  # Red
    elif days_remaining <= 60:
        urgency_tag = "REMINDER"
        urgency_color = "#fd7e14"  # Orange
    else:
        urgency_tag = "NOTICE"
        urgency_color = "#0066cc"  # Blue

    subject = f"[{urgency_tag}] Contract Expiring: {contract_title}"

    # Build an HTML email body (nicer-looking than plain text)
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; max-width: 600px;">
        <div style="background-color: {urgency_color}; color: white; padding: 16px; border-radius: 8px 8px 0 0;">
            <h2 style="margin: 0;">Contract Expiration {urgency_tag.title()}</h2>
        </div>
        <div style="border: 1px solid #e0e0e0; border-top: none; padding: 24px; border-radius: 0 0 8px 8px;">
            <p>Hello,</p>
            <p>This is an automated notification about an upcoming contract expiration:</p>

            <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
                <tr>
                    <td style="padding: 8px; font-weight: bold; color: #666;">Contract:</td>
                    <td style="padding: 8px;">{contract_title}</td>
                </tr>
                <tr style="background-color: #f8f9fa;">
                    <td style="padding: 8px; font-weight: bold; color: #666;">Vendor:</td>
                    <td style="padding: 8px;">{vendor_name}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold; color: #666;">End Date:</td>
                    <td style="padding: 8px;">{end_date_str}</td>
                </tr>
                <tr style="background-color: #f8f9fa;">
                    <td style="padding: 8px; font-weight: bold; color: #666;">Days Remaining:</td>
                    <td style="padding: 8px;">
                        <strong style="color: {urgency_color};">
                            {"EXPIRED" if days_remaining <= 0 else f"{days_remaining} days"}
                        </strong>
                    </td>
                </tr>
            </table>

            <p><strong>Recommended Actions:</strong></p>
            <ul>
                <li>Review the contract terms and conditions</li>
                <li>Contact the vendor about renewal options</li>
                <li>Discuss with your team whether to renew, renegotiate, or terminate</li>
            </ul>

            <p style="color: #888; font-size: 12px; margin-top: 24px;">
                This is an automated message from the Vendor Management Platform.
            </p>
        </div>
    </body>
    </html>
    """

    # --- DEV MODE: Log to console if no SMTP server configured ---
    if not SMTP_HOST:
        logger.info("=" * 60)
        logger.info("EMAIL (Dev Mode - Not Actually Sent)")
        logger.info(f"  To: {recipient_email}")
        logger.info(f"  Subject: {subject}")
        logger.info(f"  Contract: {contract_title}")
        logger.info(f"  Vendor: {vendor_name}")
        logger.info(f"  Days Remaining: {days_remaining}")
        logger.info("=" * 60)
        return True  # Pretend it was sent successfully

    # --- PRODUCTION MODE: Actually send the email ---
    try:
        # Build the email message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_FROM
        msg["To"] = recipient_email
        msg.attach(MIMEText(html_body, "html"))

        # Connect to the SMTP server and send
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()  # Encrypt the connection (TLS)
            if SMTP_USER and SMTP_PASSWORD:
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, recipient_email, msg.as_string())

        logger.info(f"Email sent to {recipient_email}: {subject}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {recipient_email}: {e}")
        return False


def send_batch_notifications(notifications: list[dict]) -> dict:
    """
    Send emails for a batch of new notifications.

    Takes the list returned by check_expiring_contracts() and sends
    an email for each one that has a recipient_email.

    Returns a summary: {"sent": 3, "failed": 1, "skipped": 2}
    """
    results = {"sent": 0, "failed": 0, "skipped": 0}

    for notif in notifications:
        if not notif.get("recipient_email"):
            results["skipped"] += 1
            continue

        success = send_expiry_notification_email(
            recipient_email=notif["recipient_email"],
            contract_title=notif["contract_title"],
            vendor_name=notif["vendor_name"],
            days_remaining=notif["days_remaining"],
            end_date_str=str(notif.get("end_date", "N/A")),
            notification_type=notif["type"],
        )

        if success:
            results["sent"] += 1
        else:
            results["failed"] += 1

    return results
