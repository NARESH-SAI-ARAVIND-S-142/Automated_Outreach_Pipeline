#!/usr/bin/env python3
"""
Automated Outreach Pipeline — Main CLI Entry Point

Usage:
    python outreach.py intercom.com
    python outreach.py intercom.com --max-companies 10 --max-contacts 3
    python outreach.py intercom.com --dry-run
    python outreach.py intercom.com --skip-checkpoint

One input. Four stages. A full outreach engine.
"""

import argparse
import csv
import sys
import time
from datetime import datetime
from pathlib import Path

# We import config first — it validates API keys and fails fast
try:
    import config
except SystemExit:
    sys.exit(1)

from pipeline.stage1_ocean import find_lookalike_companies
from pipeline.mock_ocean import get_mock_companies
from pipeline.stage2_prospeo import find_decision_makers
from pipeline.stage3_eazyreach import resolve_emails
from pipeline.stage4_brevo import send_outreach_emails
from pipeline.models import Company, Contact, EmailResult
from utils.dedup import dedup_companies, dedup_contacts, normalize_domain
from utils import logger


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="outreach",
        description="Automated cold-outreach pipeline — one domain in, personalized emails out.",
        epilog="Example: python outreach.py intercom.com --max-companies 5 --dry-run",
    )
    parser.add_argument(
        "domain",
        type=str,
        help="Seed company domain (e.g., 'intercom.com')",
    )
    parser.add_argument(
        "--max-companies",
        type=int,
        default=config.DEFAULT_MAX_COMPANIES,
        help=f"Max lookalike companies to find (default: {config.DEFAULT_MAX_COMPANIES})",
    )
    parser.add_argument(
        "--max-contacts",
        type=int,
        default=config.DEFAULT_MAX_CONTACTS_PER_COMPANY,
        help=f"Max contacts per company (default: {config.DEFAULT_MAX_CONTACTS_PER_COMPANY})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run stages 1-3 only — do NOT send any emails",
    )
    parser.add_argument(
        "--skip-checkpoint",
        action="store_true",
        help="Skip the safety checkpoint before sending emails (for demo speed)",
    )
    parser.add_argument(
        "--mock-ocean",
        action="store_true",
        help="Use curated mock data for Stage 1 instead of Ocean.io API (for free/demo mode)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./output",
        help="Directory to save CSV reports (default: ./output)",
    )
    return parser.parse_args()


def save_companies_csv(companies: list[Company], output_dir: Path, timestamp: str):
    """Save Stage 1 results to CSV."""
    path = output_dir / f"stage1_companies_{timestamp}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["domain", "name", "industry", "size", "size_range", "country"])
        writer.writeheader()
        for c in companies:
            writer.writerow(c.model_dump())
    logger.dim(f"  Saved → {path}")
    return path


def save_contacts_csv(contacts: list[Contact], output_dir: Path, timestamp: str, stage: str):
    """Save Stage 2/3 results to CSV."""
    path = output_dir / f"{stage}_contacts_{timestamp}.csv"
    fields = ["full_name", "first_name", "last_name", "title", "seniority",
              "linkedin_url", "email", "email_status", "company_domain", "company_name"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for c in contacts:
            row = c.model_dump()
            writer.writerow({k: row.get(k, "") for k in fields})
    logger.dim(f"  Saved → {path}")
    return path


def save_results_csv(results: list[EmailResult], output_dir: Path, timestamp: str):
    """Save Stage 4 results to CSV."""
    path = output_dir / f"stage4_results_{timestamp}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["contact_email", "contact_name", "company_name", "message_id", "status", "error"])
        writer.writeheader()
        for r in results:
            writer.writerow(r.model_dump())
    logger.dim(f"  Saved → {path}")
    return path


def main():
    """Run the complete outreach pipeline."""
    args = parse_args()

    # Set the mock-ocean flag globally so other modules can read it
    if args.mock_ocean:
        config.MOCK_OCEAN = True

    # Normalize seed domain
    seed_domain = normalize_domain(args.domain)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ── Banner ──────────────────────────────────────────────
    logger.banner()
    logger.console.print()
    logger.info(f"Seed domain: [bold cyan]{seed_domain}[/bold cyan]")
    logger.info(f"Max companies: {args.max_companies}")
    logger.info(f"Max contacts/company: {args.max_contacts}")
    if args.dry_run:
        logger.warning("DRY RUN mode — emails will NOT be sent")
    if args.mock_ocean:
        logger.warning("MOCK OCEAN mode — Stage 1 uses curated demo data")
    logger.console.print()

    pipeline_start = time.time()

    # ── Stage 1: Ocean.io — Find Lookalike Companies ────────
    if args.mock_ocean:
        logger.stage_header(1, "Ocean.io [MOCK]", "Using curated mock data (--mock-ocean)")
        companies = get_mock_companies(seed_domain, max_results=args.max_companies)
    else:
        logger.stage_header(1, "Ocean.io", "Finding lookalike companies from seed domain")
        companies = find_lookalike_companies(seed_domain, max_results=args.max_companies)

    companies = dedup_companies(companies, seed_domain)

    if not companies:
        logger.error("No companies found. Pipeline cannot continue.")
        if args.mock_ocean:
            logger.info("This shouldn't happen in mock mode — check mock_ocean.py.")
        else:
            logger.info("Check that your seed domain is valid and your Ocean.io API key works.")
        sys.exit(1)

    logger.companies_table(companies)
    save_companies_csv(companies, output_dir, timestamp)

    # ── Stage 2: Prospeo — Find Decision-Makers ─────────────
    logger.stage_header(2, "Prospeo", "Finding C-suite & VP-level decision-makers")

    contacts = find_decision_makers(companies, max_contacts_per_company=args.max_contacts)

    if not contacts:
        logger.error("No decision-makers found. Pipeline cannot continue.")
        sys.exit(1)

    save_contacts_csv(contacts, output_dir, timestamp, "stage2")

    # ── Stage 3: Eazyreach — Resolve Work Emails ────────────
    logger.stage_header(3, "Eazyreach", "Resolving LinkedIn profiles to verified work emails")

    contacts = resolve_emails(contacts)
    contacts = dedup_contacts(contacts)

    # Filter to only contacts with verified emails for the final list
    verified_contacts = [c for c in contacts if c.has_verified_email]

    logger.contacts_table(verified_contacts if verified_contacts else contacts)
    save_contacts_csv(contacts, output_dir, timestamp, "stage3")

    if not verified_contacts:
        logger.error("No contacts with verified emails found. Cannot send outreach.")
        logger.info("The contact data has been saved to CSV for manual review.")
        sys.exit(1)

    # ── Dry Run Exit ────────────────────────────────────────
    if args.dry_run:
        logger.console.print()
        logger.success(
            f"[bold]DRY RUN complete![/bold] "
            f"Found {len(companies)} companies, {len(verified_contacts)} verified contacts."
        )
        logger.info(f"CSV reports saved to: {output_dir}")
        elapsed = time.time() - pipeline_start
        logger.dim(f"Total time: {elapsed:.1f}s")
        return

    # ── Safety Checkpoint ───────────────────────────────────
    if not args.skip_checkpoint:
        if not logger.checkpoint_prompt(verified_contacts):
            logger.warning("Aborted by user. No emails sent.")
            logger.info(f"Contact data saved to: {output_dir}")
            return

    # ── Stage 4: Brevo — Send Outreach Emails ───────────────
    logger.stage_header(4, "Brevo", "Sending personalized outreach emails")

    results = send_outreach_emails(verified_contacts)
    logger.email_results_table(results)
    save_results_csv(results, output_dir, timestamp)

    # ── Summary ─────────────────────────────────────────────
    elapsed = time.time() - pipeline_start
    sent = len([r for r in results if r.status == "sent"])
    logger.console.print()
    logger.success(
        f"[bold]Pipeline complete![/bold] "
        f"{len(companies)} companies → {len(contacts)} contacts → {sent} emails sent"
    )
    logger.info(f"Reports saved to: {output_dir}")
    logger.dim(f"Total time: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
