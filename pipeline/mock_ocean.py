"""
Mock Ocean.io Data — Used when --mock-ocean flag is passed.

Returns realistic lookalike companies so Stages 2-4 can run
against live APIs (Prospeo + Brevo) without requiring an Ocean.io account.

These are real company domains from the SaaS/customer-success/support space,
chosen to be similar to common seed domains like intercom.com, freshdesk.com, etc.
"""

from pipeline.models import Company
from utils import logger

# ──────────────────────────────────────────────────────────────────────────────
# Curated dataset of real SaaS companies across different verticals.
# Grouped by "seed archetype" so the mock feels relevant regardless of input.
# ──────────────────────────────────────────────────────────────────────────────

_MOCK_COMPANIES = [
    Company(
        domain="freshworks.com",
        name="Freshworks",
        industry="Customer Service Software",
        size=5200,
        size_range="1001-5000",
        country="United States",
    ),
    Company(
        domain="zendesk.com",
        name="Zendesk",
        industry="Customer Support Platform",
        size=5500,
        size_range="5001-10000",
        country="United States",
    ),
    Company(
        domain="drift.com",
        name="Drift (Salesloft)",
        industry="Conversational Marketing",
        size=600,
        size_range="501-1000",
        country="United States",
    ),
    Company(
        domain="helpscout.com",
        name="Help Scout",
        industry="Customer Service Software",
        size=200,
        size_range="101-250",
        country="United States",
    ),
    Company(
        domain="crisp.chat",
        name="Crisp",
        industry="Business Messaging Platform",
        size=50,
        size_range="11-50",
        country="France",
    ),
    Company(
        domain="hubspot.com",
        name="HubSpot",
        industry="CRM & Marketing Platform",
        size=7400,
        size_range="5001-10000",
        country="United States",
    ),
    Company(
        domain="zoho.com",
        name="Zoho Corporation",
        industry="SaaS / Business Software",
        size=15000,
        size_range="10001+",
        country="India",
    ),
    Company(
        domain="pipedrive.com",
        name="Pipedrive",
        industry="CRM / Sales Software",
        size=900,
        size_range="501-1000",
        country="Estonia",
    ),
    Company(
        domain="loom.com",
        name="Loom",
        industry="Video Communication",
        size=300,
        size_range="201-500",
        country="United States",
    ),
    Company(
        domain="notion.so",
        name="Notion Labs",
        industry="Productivity Software",
        size=500,
        size_range="201-500",
        country="United States",
    ),
    Company(
        domain="clickup.com",
        name="ClickUp",
        industry="Project Management",
        size=1000,
        size_range="501-1000",
        country="United States",
    ),
    Company(
        domain="front.com",
        name="Front",
        industry="Customer Communication Hub",
        size=400,
        size_range="201-500",
        country="United States",
    ),
    Company(
        domain="monday.com",
        name="monday.com",
        industry="Work OS / Project Management",
        size=1900,
        size_range="1001-5000",
        country="Israel",
    ),
    Company(
        domain="gorgias.com",
        name="Gorgias",
        industry="E-commerce Helpdesk",
        size=350,
        size_range="201-500",
        country="United States",
    ),
    Company(
        domain="tidio.com",
        name="Tidio",
        industry="Live Chat & Chatbot Platform",
        size=180,
        size_range="101-250",
        country="Poland",
    ),
]


def get_mock_companies(seed_domain: str, max_results: int = 10) -> list[Company]:
    """
    Return mock lookalike companies, filtering out the seed domain.

    Args:
        seed_domain: The user's seed domain (excluded from results).
        max_results: Maximum number of companies to return.

    Returns:
        List of Company objects with realistic mock data.
    """
    logger.warning("Using [bold yellow]MOCK[/bold yellow] Ocean.io data (--mock-ocean mode)")
    logger.info(
        "Stage 1 returns curated companies — "
        "Stages 2, 3, 4 will run against [bold green]LIVE[/bold green] APIs"
    )
    logger.console.print()

    # Filter out the seed domain itself
    seed = seed_domain.strip().lower().lstrip("www.").rstrip("/")
    results = [c for c in _MOCK_COMPANIES if c.domain.lower() != seed]

    results = results[:max_results]

    logger.success(f"Mock data returned [bold]{len(results)}[/bold] lookalike companies")
    return results
