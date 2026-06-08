"""
Rich console logger — provides beautiful, consistent CLI output
with status updates, tables, and progress indicators.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich import box

console = Console()


def banner():
    """Print the pipeline banner."""
    console.print(
        Panel.fit(
            "[bold cyan]⚡ Automated Outreach Pipeline[/bold cyan]\n"
            "[dim]Sourcing → Decision-Makers → Emails → Outreach[/dim]",
            border_style="cyan",
            padding=(1, 4),
        )
    )


def stage_header(stage_num: int, title: str, description: str = ""):
    """Print a stage header."""
    console.print()
    console.rule(f"[bold yellow]Stage {stage_num}[/bold yellow]  {title}", style="yellow")
    if description:
        console.print(f"  [dim]{description}[/dim]")
    console.print()


def success(message: str):
    console.print(f"  [green]✓[/green] {message}")


def warning(message: str):
    console.print(f"  [yellow]⚠[/yellow] {message}")


def error(message: str):
    console.print(f"  [red]✗[/red] {message}")


def info(message: str):
    console.print(f"  [blue]ℹ[/blue] {message}")


def dim(message: str):
    console.print(f"  [dim]{message}[/dim]")


def companies_table(companies: list) -> None:
    """Display a table of discovered companies."""
    table = Table(
        title="Lookalike Companies", box=box.ROUNDED,
        title_style="bold cyan", border_style="dim",
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Domain", style="cyan")
    table.add_column("Company Name", style="white")
    table.add_column("Industry", style="dim")
    table.add_column("Size", justify="right", style="green")
    table.add_column("Country", style="dim")

    for i, c in enumerate(companies, 1):
        table.add_row(
            str(i), c.domain, c.name, c.industry,
            str(c.size or c.size_range or "—"), c.country,
        )
    console.print(table)


def contacts_table(contacts: list) -> None:
    """Display a table of decision-makers with emails."""
    table = Table(
        title="Decision-Makers", box=box.ROUNDED,
        title_style="bold cyan", border_style="dim",
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Name", style="white")
    table.add_column("Title", style="dim", max_width=30)
    table.add_column("Company", style="cyan")
    table.add_column("Email", style="green")
    table.add_column("Status", style="yellow")

    for i, c in enumerate(contacts, 1):
        email_display = c.email or "[dim]—[/dim]"
        status = c.email_status or "—"
        status_style = "green" if status.upper() == "VERIFIED" else "yellow"
        table.add_row(
            str(i), c.display_name, c.title,
            c.company_name, email_display, f"[{status_style}]{status}[/{status_style}]",
        )
    console.print(table)


def email_results_table(results: list) -> None:
    """Display a table of email send results."""
    table = Table(
        title="Outreach Results", box=box.ROUNDED,
        title_style="bold cyan", border_style="dim",
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Recipient", style="white")
    table.add_column("Company", style="cyan")
    table.add_column("Email", style="dim")
    table.add_column("Status", style="green")
    table.add_column("Message ID", style="dim", max_width=20)

    for i, r in enumerate(results, 1):
        status_style = "green" if r.status == "sent" else "red"
        table.add_row(
            str(i), r.contact_name, r.company_name, r.contact_email,
            f"[{status_style}]{r.status}[/{status_style}]",
            r.message_id[:20] if r.message_id else r.error[:20],
        )
    console.print(table)


def checkpoint_prompt(contacts: list) -> bool:
    """Show a safety checkpoint before sending emails. Returns True if user confirms."""
    console.print()
    console.print(
        Panel(
            f"[bold yellow]🛑 SAFETY CHECKPOINT[/bold yellow]\n\n"
            f"You are about to send [bold]{len(contacts)}[/bold] personalized outreach emails.\n"
            f"Review the contacts above carefully.\n\n"
            f"[dim]Type 'y' to proceed, 'n' to abort, or 'e' to export and exit.[/dim]",
            border_style="yellow",
            padding=(1, 2),
        )
    )
    while True:
        choice = console.input("\n  [bold yellow]Proceed? (y/n/e): [/bold yellow]").strip().lower()
        if choice in ("y", "yes"):
            return True
        elif choice in ("n", "no"):
            return False
        elif choice in ("e", "export"):
            return False  # Caller should still export CSV
        else:
            console.print("  [dim]Please enter y, n, or e.[/dim]")


def get_progress() -> Progress:
    """Create a rich progress bar."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    )
