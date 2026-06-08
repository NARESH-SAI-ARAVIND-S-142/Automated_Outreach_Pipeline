"""
De-duplication utilities for domains, emails, and LinkedIn URLs.
"""

from urllib.parse import urlparse


def normalize_domain(domain: str) -> str:
    """
    Normalize a domain string for comparison.
    Strips protocol, www prefix, trailing slashes, and lowercases.

    Examples:
        'https://www.Intercom.com/' → 'intercom.com'
        'HTTP://intercom.COM'       → 'intercom.com'
        'intercom.com'              → 'intercom.com'
    """
    domain = domain.strip().lower()

    # Strip protocol if present
    if "://" in domain:
        parsed = urlparse(domain)
        domain = parsed.netloc or parsed.path
    
    # Strip www prefix
    if domain.startswith("www."):
        domain = domain[4:]

    # Strip trailing slash
    domain = domain.rstrip("/")

    return domain


def normalize_linkedin_url(url: str) -> str:
    """
    Normalize a LinkedIn URL for comparison.
    Ensures consistent format: 'https://www.linkedin.com/in/username'

    Examples:
        'https://linkedin.com/in/john-doe/'  → 'https://www.linkedin.com/in/john-doe'
        'http://www.linkedin.com/in/john-doe' → 'https://www.linkedin.com/in/john-doe'
    """
    url = url.strip().lower().rstrip("/")

    # Extract path from URL
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")

    return f"https://www.linkedin.com{path}"


def normalize_email(email: str) -> str:
    """Normalize an email for comparison (lowercase, strip whitespace)."""
    return email.strip().lower()


def dedup_companies(companies: list, seed_domain: str = "") -> list:
    """
    Remove duplicate companies by normalized domain.
    Also removes the seed domain from results.
    """
    seen = set()
    seed_norm = normalize_domain(seed_domain) if seed_domain else ""
    unique = []

    for company in companies:
        norm = normalize_domain(company.domain)
        if norm and norm != seed_norm and norm not in seen:
            seen.add(norm)
            unique.append(company)

    return unique


def dedup_contacts(contacts: list) -> list:
    """
    Remove duplicate contacts by normalized email (primary)
    or LinkedIn URL (fallback for contacts without email).
    """
    seen_emails = set()
    seen_linkedin = set()
    unique = []

    for contact in contacts:
        # Primary de-dup by email
        if contact.email:
            norm_email = normalize_email(contact.email)
            if norm_email in seen_emails:
                continue
            seen_emails.add(norm_email)
        # Fallback de-dup by LinkedIn URL
        elif contact.linkedin_url:
            norm_url = normalize_linkedin_url(contact.linkedin_url)
            if norm_url in seen_linkedin:
                continue
            seen_linkedin.add(norm_url)

        unique.append(contact)

    return unique
