"""
Stage 4: Brevo — Send Personalized Outreach Emails

Takes contacts with verified emails and sends personalized outreach
emails using Brevo's transactional email API.

API: POST https://api.brevo.com/v3/smtp/email
Auth: api-key header
"""

import time
from pathlib import Path
from pipeline.models import Contact, EmailResult
from utils.http_client import create_session, handle_response
from utils import logger
import config


# Load email template
_TEMPLATE_PATH = Path(__file__).parent.parent / "templates" / "outreach_email.html"


def send_outreach_emails(contacts: list[Contact]) -> list[EmailResult]:
    """
    Send personalized outreach emails to all contacts with verified emails.

    Args:
        contacts: List of contacts from Stage 3 (must have verified emails).

    Returns:
        List of EmailResult objects with send status.
    """
    # Filter to only contacts with verified emails
    sendable = [c for c in contacts if c.has_verified_email]
    skipped = [c for c in contacts if not c.has_verified_email]

    if skipped:
        logger.warning(f"Skipping {len(skipped)} contacts without verified emails")

    if not sendable:
        logger.error("No contacts with verified emails to send to!")
        return []

    logger.info(f"Sending outreach to [bold]{len(sendable)}[/bold] contacts...")

    # Load email template
    template = _load_template()
    session = create_session()
    results = []

    with logger.get_progress() as progress:
        task = progress.add_task(
            "Sending emails...",
            total=len(sendable),
        )

        for contact in sendable:
            result = _send_single_email(session, contact, template)
            results.append(result)
            progress.advance(task)

            # Rate limit: ~10/second max for Brevo free tier
            time.sleep(0.15)

    sent = [r for r in results if r.status == "sent"]
    failed = [r for r in results if r.status == "failed"]
    logger.success(
        f"Outreach complete: [green]{len(sent)} sent[/green], "
        f"[red]{len(failed)} failed[/red]"
    )

    return results


def _load_template() -> str:
    """Load the HTML email template."""
    if _TEMPLATE_PATH.exists():
        return _TEMPLATE_PATH.read_text(encoding="utf-8")

    # Fallback: inline template if file doesn't exist
    logger.warning("Email template file not found — using default template")
    return _default_template()


def _personalize_email(template: str, contact: Contact) -> tuple[str, str]:
    """
    Personalize the email template for a specific contact.

    Returns:
        Tuple of (subject, html_body).
    """
    first_name = contact.first_name or contact.display_name.split()[0]

    # Personalize subject
    subject = f"Quick question for {first_name} at {contact.company_name}"

    # Replace template variables
    html = template.replace("{{first_name}}", first_name)
    html = html.replace("{{full_name}}", contact.display_name)
    html = html.replace("{{title}}", contact.title)
    html = html.replace("{{company_name}}", contact.company_name)
    html = html.replace("{{company_domain}}", contact.company_domain)
    html = html.replace("{{sender_name}}", config.SENDER_NAME)
    html = html.replace("{{sender_email}}", config.SENDER_EMAIL)

    return subject, html


def _send_single_email(session, contact: Contact, template: str) -> EmailResult:
    """Send a single personalized email via Brevo."""
    subject, html_body = _personalize_email(template, contact)

    url = f"{config.BREVO_BASE_URL}/smtp/email"
    headers = {
        "api-key": config.BREVO_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
        "sender": {
            "email": config.SENDER_EMAIL,
            "name": config.SENDER_NAME,
        },
        "to": [
            {
                "email": contact.email,
                "name": contact.display_name,
            }
        ],
        "subject": subject,
        "htmlContent": html_body,
    }

    try:
        response = session.post(url, json=payload, headers=headers, timeout=config.REQUEST_TIMEOUT)
        data = handle_response(response, "Brevo")

        message_id = data.get("messageId", "")
        return EmailResult(
            contact_email=contact.email,
            contact_name=contact.display_name,
            company_name=contact.company_name,
            message_id=message_id,
            status="sent",
        )

    except Exception as e:
        return EmailResult(
            contact_email=contact.email,
            contact_name=contact.display_name,
            company_name=contact.company_name,
            status="failed",
            error=str(e)[:200],
        )


def _default_template() -> str:
    """Fallback email template if the HTML file is missing."""
    return """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #333; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 20px;">
  <p>Hi {{first_name}},</p>

  <p>I came across {{company_name}} and was impressed by what your team is building. As {{title}}, you're likely thinking about how to scale operations efficiently.</p>

  <p>We help companies like yours automate their outbound outreach — from finding the right prospects to sending personalized messages — saving teams 20+ hours per week.</p>

  <p>Would you be open to a quick 15-minute chat this week to see if there's a fit?</p>

  <p>Best,<br>
  {{sender_name}}</p>

  <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
  <p style="font-size: 12px; color: #999;">
    You're receiving this because of your role at {{company_name}}.
    Reply "unsubscribe" to opt out.
  </p>
</body>
</html>"""
