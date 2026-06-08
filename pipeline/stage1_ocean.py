"""
Stage 1: Ocean.io — Lookalike Company Discovery

Takes a seed domain and returns a list of similar companies
using Ocean.io's AI-driven lookalike matching.

API: POST https://api.ocean.io/v3/companies/lookalike
Auth: X-Api-Token header
"""

import config
from pipeline.models import Company
from utils.http_client import create_session, handle_response
from utils import logger


def find_lookalike_companies(seed_domain: str, max_results: int = 10) -> list[Company]:
    """
    Find companies similar to the seed domain using Ocean.io.

    Args:
        seed_domain: The seed company domain (e.g., 'intercom.com').
        max_results: Maximum number of lookalike companies to return.

    Returns:
        List of Company objects.
    """
    logger.info(f"Searching for companies similar to [cyan]{seed_domain}[/cyan]...")

    session = create_session()

    url = f"{config.OCEAN_BASE_URL}/companies/lookalike"
    headers = {
        "X-Api-Token": config.OCEAN_API_TOKEN,
        "Content-Type": "application/json",
    }
    payload = {
        "seedDomains": [seed_domain],
        "size": max_results,
        "fields": [
            "domain",
            "name",
            "companySize",
            "primaryCountry",
            "industries",
        ],
    }

    try:
        response = session.post(url, json=payload, headers=headers, timeout=config.REQUEST_TIMEOUT)
        data = handle_response(response, "Ocean.io")
    except Exception as e:
        logger.error(f"Ocean.io API call failed: {e}")
        return []

    # Parse response — Ocean.io returns results in various formats
    companies = _parse_response(data, seed_domain)

    if companies:
        logger.success(f"Found [bold]{len(companies)}[/bold] lookalike companies")
    else:
        logger.warning("No lookalike companies found. Check your seed domain.")

    return companies


def _parse_response(data: dict, seed_domain: str) -> list[Company]:
    """
    Parse Ocean.io response into Company objects.
    Handles multiple response formats gracefully.
    """
    companies = []

    # The response format may vary — try common structures
    results = []
    if isinstance(data, list):
        results = data
    elif isinstance(data, dict):
        # Try common keys
        for key in ("results", "companies", "data", "hits"):
            if key in data and isinstance(data[key], list):
                results = data[key]
                break

        # If the dict itself looks like a single result set with domain info
        if not results and "domain" in data:
            results = [data]

    for item in results:
        if not isinstance(item, dict):
            continue

        domain = item.get("domain", "") or item.get("website", "") or ""
        if not domain:
            continue

        # Normalize domain
        domain = domain.strip().lower()
        if domain.startswith("http"):
            from urllib.parse import urlparse
            domain = urlparse(domain).netloc or domain
        domain = domain.lstrip("www.").rstrip("/")

        # Skip the seed domain itself
        if domain == seed_domain.lower():
            continue

        # Extract industry
        industries = item.get("industries", [])
        industry = ""
        if isinstance(industries, list) and industries:
            industry = industries[0] if isinstance(industries[0], str) else str(industries[0])
        elif isinstance(industries, str):
            industry = industries

        company = Company(
            domain=domain,
            name=item.get("name", "") or item.get("companyName", "") or "",
            industry=industry,
            size=item.get("companySize") or item.get("employeeCount"),
            size_range=item.get("companySizeRange", "") or item.get("employeeRange", ""),
            country=item.get("primaryCountry", "") or item.get("country", ""),
        )
        companies.append(company)

    return companies
