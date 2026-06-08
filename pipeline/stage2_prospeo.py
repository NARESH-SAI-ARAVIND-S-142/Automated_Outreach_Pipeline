"""
Stage 2: Prospeo — Find Decision-Makers

Takes a list of company domains and finds C-suite / VP-level contacts
using Prospeo's Search Person API, then enriches them to get verified emails.

Two-step process per company:
  1. Search Person — find people by company domain + seniority filter
  2. Enrich Person — get verified email from person_id or LinkedIn URL

API: POST https://api.prospeo.io/search-person
     POST https://api.prospeo.io/enrich-person
Auth: X-KEY header
"""

import time
from pipeline.models import Company, Contact
from utils.http_client import create_session, handle_response
from utils import logger
import config


# Seniority levels we care about for outreach
TARGET_SENIORITIES = ["C-Suite", "Vice President", "Founder/Owner", "Director"]


def find_decision_makers(
    companies: list[Company],
    max_contacts_per_company: int = 5,
) -> list[Contact]:
    """
    Find decision-makers at each company and enrich with verified emails.

    Args:
        companies: List of companies from Stage 1.
        max_contacts_per_company: Max contacts to fetch per company.

    Returns:
        List of Contact objects (some may lack verified emails).
    """
    all_contacts = []
    session = create_session()

    with logger.get_progress() as progress:
        task = progress.add_task(
            "Searching for decision-makers...",
            total=len(companies),
        )

        for company in companies:
            contacts = _search_and_enrich_company(
                session, company, max_contacts_per_company,
            )
            all_contacts.extend(contacts)
            progress.advance(task)

            # Small delay between companies to be respectful of rate limits
            time.sleep(0.5)

    verified = [c for c in all_contacts if c.has_verified_email]
    logger.success(
        f"Found [bold]{len(all_contacts)}[/bold] contacts, "
        f"[bold green]{len(verified)}[/bold green] with verified emails"
    )

    return all_contacts


def _search_and_enrich_company(
    session,
    company: Company,
    max_contacts: int,
) -> list[Contact]:
    """Search for decision-makers at a single company, then enrich top results."""

    # Step 1: Search for persons at this company
    persons = _search_persons(session, company.domain, max_contacts)

    if not persons:
        logger.dim(f"  No decision-makers found at {company.domain}")
        return []

    # Step 2: Enrich each person to get their verified email
    contacts = []
    for person in persons[:max_contacts]:
        contact = _enrich_person(session, person, company)
        if contact:
            contacts.append(contact)
            # Small delay between enrichment calls
            time.sleep(0.3)

    return contacts


def _search_persons(session, domain: str, max_results: int) -> list[dict]:
    """
    Search for decision-makers at a company using Prospeo Search Person API.
    Returns raw person data (no email/mobile — that requires enrichment).
    """
    url = f"{config.PROSPEO_BASE_URL}/search-person"
    headers = {
        "X-KEY": config.PROSPEO_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "page": 1,
        "filters": {
            "company": {
                "websites": {"include": [domain]}
            },
            "person_seniority": {
                "include": TARGET_SENIORITIES
            },
        },
    }

    try:
        response = session.post(url, json=payload, headers=headers, timeout=config.REQUEST_TIMEOUT)
        data = handle_response(response, "Prospeo/SearchPerson")
    except Exception as e:
        logger.warning(f"Prospeo search failed for {domain}: {e}")
        return []

    if data.get("error"):
        error_code = data.get("error_code", "UNKNOWN")
        if error_code == "NO_RESULTS":
            return []
        logger.warning(f"Prospeo search error for {domain}: {error_code}")
        return []

    results = data.get("results", [])
    return results[:max_results]


def _enrich_person(session, person_data: dict, company: Company) -> Contact | None:
    """
    Enrich a person record to get their verified email.
    Tries person_id first, falls back to LinkedIn URL.
    """
    person = person_data.get("person", person_data)

    person_id = person.get("person_id", "")
    linkedin_url = person.get("linkedin_url", "")
    full_name = person.get("full_name", "")
    first_name = person.get("first_name", "")
    last_name = person.get("last_name", "")
    title = person.get("current_job_title", "") or person.get("title", "")

    # Build enrichment request — prefer person_id, fallback to linkedin_url
    enrich_data = {}
    if person_id:
        enrich_data = {"person_id": person_id}
    elif linkedin_url:
        enrich_data = {"linkedin_url": linkedin_url}
    elif first_name and last_name:
        enrich_data = {
            "first_name": first_name,
            "last_name": last_name,
            "company_website": company.domain,
        }
    else:
        # Not enough data to enrich
        return Contact(
            first_name=first_name,
            last_name=last_name,
            full_name=full_name,
            title=title,
            linkedin_url=linkedin_url,
            company_domain=company.domain,
            company_name=company.name,
            person_id=person_id,
        )

    url = f"{config.PROSPEO_BASE_URL}/enrich-person"
    headers = {
        "X-KEY": config.PROSPEO_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "only_verified_email": True,
        "data": enrich_data,
    }

    try:
        response = session.post(url, json=payload, headers=headers, timeout=config.REQUEST_TIMEOUT)
        data = handle_response(response, "Prospeo/EnrichPerson")
    except Exception as e:
        logger.dim(f"  Enrichment failed for {full_name or linkedin_url}: {e}")
        return Contact(
            first_name=first_name,
            last_name=last_name,
            full_name=full_name,
            title=title,
            linkedin_url=linkedin_url,
            company_domain=company.domain,
            company_name=company.name,
            person_id=person_id,
        )

    if data.get("error"):
        # NO_MATCH is common — not a real error
        return Contact(
            first_name=first_name,
            last_name=last_name,
            full_name=full_name,
            title=title,
            linkedin_url=linkedin_url,
            company_domain=company.domain,
            company_name=company.name,
            person_id=person_id,
        )

    # Extract enriched data
    enriched_person = data.get("person", {})
    enriched_company = data.get("company", {})

    email_data = enriched_person.get("email", {}) or {}
    email_address = email_data.get("email", "")
    email_status = email_data.get("status", "")

    # If email is masked (contains *), it wasn't revealed
    if email_address and "***" in email_address:
        email_address = ""
        email_status = "MASKED"

    seniority = ""
    job_history = enriched_person.get("job_history", [])
    if job_history:
        current_jobs = [j for j in job_history if j.get("current")]
        if current_jobs:
            seniority = current_jobs[0].get("seniority", "")

    return Contact(
        first_name=enriched_person.get("first_name", first_name),
        last_name=enriched_person.get("last_name", last_name),
        full_name=enriched_person.get("full_name", full_name),
        title=enriched_person.get("current_job_title", title),
        seniority=seniority,
        linkedin_url=enriched_person.get("linkedin_url", linkedin_url),
        email=email_address,
        email_status=email_status,
        company_domain=company.domain,
        company_name=enriched_company.get("name", company.name) if enriched_company else company.name,
        person_id=enriched_person.get("person_id", person_id),
    )
