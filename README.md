# Automated Outreach Pipeline

> One domain in, personalized emails out — zero humans in the loop.

A fully automated cold-outreach CLI pipeline that takes a single seed company domain and executes four stages end-to-end:

1. **Ocean.io** — Find lookalike companies from the seed domain
2. **Prospeo** — Find C-suite / VP decision-makers at those companies
3. **Eazyreach** — Resolve LinkedIn profiles to verified work emails
4. **Brevo** — Send personalized outreach emails automatically

```
python outreach.py intercom.com
```

## Architecture

```
┌──────────┐    ┌───────────┐    ┌──────────┐    ┌──────┐    ┌───────┐
│  Human   │───▶│  Ocean.io │───▶│ Prospeo  │───▶│Eazy- │───▶│ Brevo │
│  Input   │    │ Lookalike │    │ Decision │    │reach │    │ Email │
│ (domain) │    │ Companies │    │  Makers  │    │Email │    │ Send  │
└──────────┘    └───────────┘    └──────────┘    └──────┘    └───────┘
                     │                │              │            │
                     ▼                ▼              ▼            ▼
                 CSV report       CSV report     CSV report   CSV report
```

Each stage feeds the next automatically. A **safety checkpoint** pauses before emails fire.

## Quick Start

### 1. Prerequisites

- Python 3.10+
- **Required:** [Prospeo](https://app.prospeo.io) (free — 100 credits/month) + [Brevo](https://app.brevo.com) (free — 300 emails/day)
- **Optional:** [Ocean.io](https://ocean.io) (requires company email — use `--mock-ocean` if unavailable), [Eazyreach](https://eazyreach.app) (auto-fallback to Prospeo)

### 2. Install

```bash
# Clone and enter the project
cd sde-assignment

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure

```bash
# Copy the env template
cp .env.example .env

# Fill in your API keys
nano .env   # or your preferred editor
```

Environment variables:

| Variable | Required? | Source |
|---|---|---|
| `OCEAN_API_TOKEN` | No* | Ocean.io → Account Settings → API Tokens |
| `PROSPEO_API_KEY` | **Yes** | [app.prospeo.io/api](https://app.prospeo.io/api) (FREE: 100 credits/month) |
| `EAZYREACH_API_KEY` | No | Eazyreach dashboard — leave blank to auto-fallback to Prospeo |
| `BREVO_API_KEY` | **Yes** | [app.brevo.com/settings/keys/api](https://app.brevo.com/settings/keys/api) (FREE: 300 emails/day) |
| `SENDER_EMAIL` | **Yes** | Your verified sender email (Gmail works for demo) |
| `SENDER_NAME` | **Yes** | Display name for outreach emails |

*\*Not required when using `--mock-ocean` mode.*

### 4. Run

```bash
# Full pipeline
python outreach.py intercom.com

# Dry run (no emails sent)
python outreach.py intercom.com --dry-run

# Custom limits
python outreach.py intercom.com --max-companies 5 --max-contacts 2

# Skip safety checkpoint (for demo)
python outreach.py intercom.com --skip-checkpoint

# 🆓 FREE MODE — no Ocean.io required! Mock Stage 1, live Stages 2-4
python outreach.py intercom.com --mock-ocean --dry-run --max-companies 3 --max-contacts 1
```

## CLI Options

| Flag | Default | Description |
|---|---|---|
| `domain` | — | Seed company domain (required) |
| `--max-companies` | 10 | Max lookalike companies to find |
| `--max-contacts` | 5 | Max contacts per company |
| `--dry-run` | false | Run stages 1–3 only, skip emails |
| `--skip-checkpoint` | false | Auto-approve safety checkpoint |
| `--mock-ocean` | false | Use curated mock data for Stage 1 (no Ocean.io API needed) |
| `--output-dir` | `./output` | Directory for CSV reports |

## Output

Each run produces timestamped CSV files in the `output/` directory:

```
output/
├── stage1_companies_20240607_143022.csv    # Lookalike companies
├── stage2_contacts_20240607_143022.csv     # Decision-makers (pre-enrichment)
├── stage3_contacts_20240607_143022.csv     # Contacts with verified emails
└── stage4_results_20240607_143022.csv      # Email send results
```

## Project Structure

```
├── outreach.py              # CLI entry point — orchestrates all stages
├── config.py                # Environment config + validation
├── pipeline/
│   ├── models.py            # Pydantic data models (Company, Contact, EmailResult)
│   ├── stage1_ocean.py      # Ocean.io lookalike company search
│   ├── mock_ocean.py        # Curated mock data for --mock-ocean mode
│   ├── stage2_prospeo.py    # Prospeo decision-maker search + enrichment
│   ├── stage3_eazyreach.py  # Eazyreach email resolution (+ Prospeo fallback)
│   └── stage4_brevo.py      # Brevo transactional email sending
├── utils/
│   ├── http_client.py       # Shared HTTP session with retry/backoff
│   ├── logger.py            # Rich CLI output (tables, progress bars)
│   └── dedup.py             # De-duplication for domains, emails, LinkedIn URLs
├── templates/
│   └── outreach_email.html  # Personalized HTML email template
├── output/                  # Runtime CSV reports (gitignored)
├── requirements.txt         # Python dependencies
├── .env.example             # API key template
└── .gitignore
```

## Edge Cases Handled

- **Rate limits** — Automatic retry with exponential backoff (429, 500, 502, 503, 504)
- **Missing contacts** — Graceful skip, pipeline continues
- **Undeliverable emails** — Only sends to VERIFIED status emails
- **De-duplication** — Companies by domain, contacts by email/LinkedIn URL
- **Partial failures** — Each stage logs failures but doesn't crash the run
- **Masked emails** — Detects `***` in Prospeo responses and skips them
- **Safety checkpoint** — Shows summary table before emails fire (disable with `--skip-checkpoint`)

## Design Decisions

1. **Raw `requests` over SDKs** — All APIs called via plain HTTP for maximum transparency. Important for interview code walkthrough.
2. **Prospeo fallback for Eazyreach** — Since Eazyreach has no public API docs, the pipeline automatically falls back to Prospeo's `enrich-person` endpoint (which also resolves LinkedIn URLs to emails).
3. **Mock Ocean mode** — Ocean.io requires a company email on a custom domain. The `--mock-ocean` flag provides curated real-company data so Stages 2–4 can run end-to-end with live APIs.
4. **One stage = one module** — Each stage is a single file with a clear entry function. Easy to test, extend, or swap.
5. **Pydantic models** — Type-safe data contracts between stages catch issues early.
6. **CSV at every stage** — Intermediate outputs are saved for debugging and interview demo.
