"""
Stage 3: Eazyreach — LinkedIn URL → Verified Work Email

Takes contacts with LinkedIn URLs and resolves them to verified work emails.

Primary path:  Eazyreach API (if API key is configured)
Fallback path: Prospeo's enrich-person endpoint (uses LinkedIn URL as input)

NOTE: Eazyreach has no public API documentation as of this writing.
      The API interface below is a best-guess based on their platform.
      Update the endpoint/payload format once actual docs are available.
"""

import time
from pipeline.models import Contact
from utils.http_client import create_session, handle_response
from utils import logger
import config


def resolve_emails(contacts: list[Contact]) -> list[Contact]:
    """
    Resolve verified work emails for contacts that are missing them.
    Contacts that already have verified emails are passed through unchanged.

    Args:
        contacts: List of contacts from Stage 2.

    Returns:
        Same list with emails filled in where possible.
    """
    needs_resolution = [c for c in contacts if not c.has_verified_email and c.linkedin_url]
    already_resolved = [c for c in contacts if c.has_verified_email]

    if not needs_resolution:
        logger.info("All contacts already have verified emails — nothing to resolve.")
        return contacts

    logger.info(
        f"Resolving emails for [bold]{len(needs_resolution)}[/bold] contacts "
        f"([green]{len(already_resolved)}[/green] already verified)"
    )

    # Choose resolution method based on available API key
    if config.EAZYREACH_API_KEY:
        resolved = _resolve_via_eazyreach(needs_resolution)
    else:
        logger.warning(
            "Eazyreach API key not configured — using Prospeo fallback for email resolution"
        )
        resolved = _resolve_via_prospeo_fallback(needs_resolution)

    # Merge results
    all_contacts = already_resolved + resolved

    final_verified = [c for c in all_contacts if c.has_verified_email]
    logger.success(
        f"Email resolution complete: [bold green]{len(final_verified)}[/bold green] "
        f"verified emails out of [bold]{len(all_contacts)}[/bold] contacts"
    )

    return all_contacts


def _resolve_via_eazyreach(contacts: list[Contact]) -> list[Contact]:
    """
    Resolve emails using Eazyreach API.

    NOTE: This is a placeholder implementation. The actual API endpoint,
    request format, and response format need to be updated based on
    Eazyreach's API documentation (available in dashboard).

    Expected API pattern (common for email finder services):
      POST /api/v1/find-email
      Body: {"linkedin_url": "https://linkedin.com/in/..."}
      Response: {"email": "...", "status": "verified"}
    """
    session = create_session()
    resolved = []

    with logger.get_progress() as progress:
        task = progress.add_task(
            "Resolving emails via Eazyreach...",
            total=len(contacts),
        )

        for contact in contacts:
            enriched = _eazyreach_lookup(session, contact)
            resolved.append(enriched)
            progress.advance(task)
            time.sleep(0.5)  # Rate limiting

    return resolved


def _eazyreach_lookup(session, contact: Contact) -> Contact:
    """
    Look up a single contact's email via Eazyreach.

    TODO: Update endpoint and payload format based on actual Eazyreach API docs.
    """
    url = f"{config.EAZYREACH_BASE_URL}/api/v1/find-email"
    headers = {
        "Authorization": f"Bearer {config.EAZYREACH_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "linkedin_url": contact.linkedin_url,
    }

    try:
        response = session.post(url, json=payload, headers=headers, timeout=config.REQUEST_TIMEOUT)
        data = handle_response(response, "Eazyreach")

        email = data.get("email", "") or data.get("work_email", "")
        status = data.get("status", "") or data.get("email_status", "")

        if email and "***" not in email:
            contact = contact.model_copy(update={
                "email": email,
                "email_status": status or "VERIFIED",
            })
    except Exception as e:
        logger.dim(f"  Eazyreach lookup failed for {contact.display_name}: {e}")
        # Don't crash — contact just won't have an email

    return contact


def _resolve_via_prospeo_fallback(contacts: list[Contact]) -> list[Contact]:
    """
    Fallback: resolve emails using Prospeo's enrich-person endpoint.
    This works because enrich-person accepts linkedin_url as input.
    """
    session = create_session()
    resolved = []

    with logger.get_progress() as progress:
        task = progress.add_task(
            "Resolving emails via Prospeo (fallback)...",
            total=len(contacts),
        )

        for contact in contacts:
            enriched = _prospeo_enrich_by_linkedin(session, contact)
            resolved.append(enriched)
            progress.advance(task)
            time.sleep(0.3)  # Rate limiting

    return resolved


def _prospeo_enrich_by_linkedin(session, contact: Contact) -> Contact:
    """
    Enrich a contact using their LinkedIn URL via Prospeo's enrich-person endpoint.
    """
    url = f"{config.PROSPEO_BASE_URL}/enrich-person"
    headers = {
        "X-KEY": config.PROSPEO_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "only_verified_email": True,
        "data": {
            "linkedin_url": contact.linkedin_url,
        },
    }

    try:
        response = session.post(url, json=payload, headers=headers, timeout=config.REQUEST_TIMEOUT)
        data = handle_response(response, "Prospeo/EnrichFallback")

        if data.get("error"):
            return contact

        person = data.get("person", {})
        email_data = person.get("email", {}) or {}
        email = email_data.get("email", "")
        status = email_data.get("status", "")

        # Skip masked emails
        if email and "***" in email:
            return contact

        if email:
            contact = contact.model_copy(update={
                "email": email,
                "email_status": status,
                "first_name": person.get("first_name") or contact.first_name,
                "last_name": person.get("last_name") or contact.last_name,
                "full_name": person.get("full_name") or contact.full_name,
                "title": person.get("current_job_title") or contact.title,
            })

    except Exception as e:
        logger.dim(f"  Prospeo fallback failed for {contact.display_name}: {e}")

    return contact
