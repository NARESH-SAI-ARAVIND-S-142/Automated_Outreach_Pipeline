"""
Pydantic data models for inter-stage data transfer.
Each stage produces typed output that the next stage consumes.
"""

from typing import Optional
from pydantic import BaseModel, Field


class Company(BaseModel):
    """A company discovered via Ocean.io lookalike search."""
    domain: str = Field(..., description="Company website domain (e.g., 'intercom.com')")
    name: str = Field(default="", description="Company name")
    industry: str = Field(default="", description="Primary industry")
    size: Optional[int] = Field(default=None, description="Employee count")
    size_range: str = Field(default="", description="Employee range (e.g., '51-200')")
    country: str = Field(default="", description="Primary country")


class Contact(BaseModel):
    """A decision-maker found via Prospeo and enriched with email."""
    first_name: str = Field(default="", description="First name")
    last_name: str = Field(default="", description="Last name")
    full_name: str = Field(default="", description="Full name")
    title: str = Field(default="", description="Current job title")
    seniority: str = Field(default="", description="Seniority level (C-Suite, VP, etc.)")
    linkedin_url: str = Field(default="", description="LinkedIn profile URL")
    email: str = Field(default="", description="Verified work email")
    email_status: str = Field(default="", description="Email verification status")
    company_domain: str = Field(default="", description="Company domain")
    company_name: str = Field(default="", description="Company name")
    person_id: str = Field(default="", description="Prospeo person ID for enrichment")

    @property
    def has_verified_email(self) -> bool:
        """Whether this contact has a deliverable email address."""
        return bool(self.email) and self.email_status.upper() in ("VERIFIED", "VALID")

    @property
    def display_name(self) -> str:
        """Best available display name."""
        return self.full_name or f"{self.first_name} {self.last_name}".strip() or "Unknown"


class EmailResult(BaseModel):
    """Result of sending an outreach email via Brevo."""
    contact_email: str
    contact_name: str
    company_name: str
    message_id: str = Field(default="", description="Brevo message ID")
    status: str = Field(default="pending", description="sent | failed | skipped")
    error: str = Field(default="", description="Error message if failed")
