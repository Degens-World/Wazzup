import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from rich import box
from rich.columns import Columns
from rich.text import Text

from config import load_config, save_config, AUTONOMY_LABELS
from scanner import full_scan
from agent.brain import MarketAgentBrain
from ads.platforms import get_platforms as get_ad_platforms
from social.platforms import get_platforms as get_social_platforms

console = Console()
brain: MarketAgentBrain = None


def header():
    console.print(Panel(
        "[bold cyan]MarketAgent[/bold cyan] — Autonomous SEO & Marketing Assistant",
        style="bold blue",
        box=box.DOUBLE_EDGE,
    ))


def setup_wizard(config: dict) -> dict:
    console.print("\n[bold yellow]First-time setup[/bold yellow]\n")

    config["website"] = Prompt.ask("Enter your website URL", default=config.get("website", ""))
    config["anthropic_api_key"] = Prompt.ask(
        "Anthropic API key", default=config.get("anthropic_api_key", ""), password=True
    )

    console.print("\n[bold]Autonomy level[/bold]")
    for level, label in AUTONOMY_LABELS.items():
        console.print(f"  [cyan]{level}[/cyan] — {label}")
    config["autonomy_level"] = IntPrompt.ask("Choose autonomy level", default=config.get("autonomy_level", 1))

    # Ad platforms
    console.print("\n[bold]Ad Platforms[/bold] (press Enter to skip each)")
    for platform in config["ads"]:
        if Confirm.ask(f"  Enable {platform.replace('_', ' ').title()}?", default=False):
            config["ads"][platform]["enabled"] = True

    # Social platforms
    console.print("\n[bold]Social Media Platforms[/bold]")
    for platform in config["social"]:
        if Confirm.ask(f"  Enable {platform.title()}?", default=False):
            config["social"][platform]["enabled"] = True

    save_config(config)
    console.print("\n[green]✓ Config saved.[/green]\n")
    return config


def show_status(config: dict):
    table = Table(title="MarketAgent Status", box=box.ROUNDED)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Website", config["website"] or "[red]Not set[/red]")
    table.add_row("API Key", "[green]Set[/green]" if config["anthropic_api_key"] else "[red]Not set[/red]")
    table.add_row("Autonomy", f"{config['autonomy_level']} — {AUTONOMY_LABELS[config['autonomy_level']]}")

    enabled_ads = [k for k, v in config["ads"].items() if v.get("enabled")]
    enabled_social = [k for k, v in config["social"].items() if v.get("enabled")]
    table.add_row("Ad Platforms", ", ".join(enabled_ads) if enabled_ads else "[dim]None[/dim]")
    table.add_row("Social Platforms", ", ".join(enabled_social) if enabled_social else "[dim]None[/dim]")

    console.print(table)


def show_scan_results(result: dict):
    hosting = result["hosting"]
    seo = result["seo"]

    # Hosting panel
    console.print(Panel(
        f"[bold]Provider:[/bold] {hosting['provider']}\n"
        f"[bold]IP:[/bold] {hosting.get('ip', 'N/A')}\n"
        f"[bold]Detection:[/bold] {hosting.get('method', 'N/A')}",
        title="[cyan]Hosting[/cyan]",
        box=box.ROUNDED,
    ))

    if "error" in seo:
        console.print(f"[red]SEO scan error: {seo['error']}[/red]")
        return

    score = seo["score"]
    score_color = "green" if score >= 80 else "yellow" if score >= 60 else "red"
    console.print(Panel(
        f"[bold {score_color}]SEO Score: {score}/100[/bold {score_color}]",
        title="[cyan]SEO Audit[/cyan]",
        box=box.ROUNDED,
    ))

    if seo["issues"]:
        console.print("[bold red]Issues:[/bold red]")
        for issue in seo["issues"]:
            console.print(f"  [red]✗[/red] {issue}")

    if seo["recommendations"]:
        console.print("[bold yellow]Recommendations:[/bold yellow]")
        for rec in seo["recommendations"]:
            console.print(f"  [yellow]→[/yellow] {rec}")

    data = seo.get("data", {})
    table = Table(box=box.SIMPLE)
    table.add_column("Property", style="dim")
    table.add_column("Value")

    if data.get("title"):
        table.add_row("Title", data["title"][:60])
    if data.get("h1_count") is not None:
        table.add_row("H1 tags", str(data["h1_count"]))
    if data.get("images_total") is not None:
        table.add_row("Images", f"{data['images_total']} total, {data['images_missing_alt']} missing alt")
    if data.get("page_size_kb"):
        table.add_row("Page size", f"{data['page_size_kb']} KB")
    table.add_row("HTTPS", "[green]Yes[/green]" if data.get("https") else "[red]No[/red]")
    table.add_row("robots.txt", "[green]Found[/green]" if data.get("has_robots_txt") else "[red]Missing[/red]")
    table.add_row("sitemap.xml", "[green]Found[/green]" if data.get("has_sitemap") else "[red]Missing[/red]")

    console.print(table)


def menu() -> str:
    console.print("\n[bold]What would you like to do?[/bold]")
    options = [
        ("1", "Scan website (SEO audit + hosting)"),
        ("2", "Get AI analysis & action plan"),
        ("3", "Chat with MarketAgent"),
        ("4", "Generate social media content"),
        ("5", "View platform status"),
        ("6", "Settings"),
        ("q", "Quit"),
    ]
    for key, label in options:
        console.print(f"  [cyan]{key}[/cyan]  {label}")
    return Prompt.ask("\nChoice", choices=["1", "2", "3", "4", "5", "6", "q"])


def run_cli():
    global brain
    header()

    config = load_config()
    if not config["website"] or not config["anthropic_api_key"]:
        config = setup_wizard(config)

    brain = MarketAgentBrain()
    last_scan = None

    while True:
        choice = menu()

        if choice == "q":
            console.print("[dim]Goodbye.[/dim]")
            break

        elif choice == "1":
            url = config["website"]
            console.print(f"\n[cyan]Scanning {url}...[/cyan]")
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as p:
                p.add_task("Running scan...", total=None)
                last_scan = full_scan(url)
            show_scan_results(last_scan)

        elif choice == "2":
            if not last_scan:
                console.print("[yellow]Run a scan first (option 1).[/yellow]")
                continue
            console.print("\n[cyan]Analyzing with MarketAgent...[/cyan]\n")
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as p:
                p.add_task("Thinking...", total=None)
                analysis = brain.analyze(last_scan)
            console.print(Markdown(analysis))

        elif choice == "3":
            console.print("\n[dim]Type 'back' to return to menu.[/dim]")
            while True:
                user_input = Prompt.ask("[bold cyan]You[/bold cyan]")
                if user_input.lower() == "back":
                    break
                with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as p:
                    p.add_task("Thinking...", total=None)
                    reply = brain.chat(user_input, last_scan)
                console.print(Markdown(f"**MarketAgent:** {reply}"))

        elif choice == "4":
            platforms = [k for k, v in config["social"].items() if v.get("enabled")]
            if not platforms:
                console.print("[yellow]No social platforms enabled. Go to Settings to enable them.[/yellow]")
                continue
            platform = Prompt.ask("Platform", choices=platforms)
            topic = Prompt.ask("What topic or message")
            content = brain.generate_content(platform, topic)
            console.print(Panel(content, title=f"[cyan]{platform.title()} Content[/cyan]", box=box.ROUNDED))

        elif choice == "5":
            ad_platforms = get_ad_platforms(config["ads"])
            social_platforms = get_social_platforms(config["social"])

            table = Table(title="Platform Status", box=box.ROUNDED)
            table.add_column("Platform")
            table.add_column("Type")
            table.add_column("Status")

            for key, p in ad_platforms.items():
                s = p.status()
                status = "[green]Ready[/green]" if s["configured"] and s["enabled"] else \
                         "[yellow]Enabled, not configured[/yellow]" if s["enabled"] else "[dim]Disabled[/dim]"
                table.add_row(s["platform"], "Ads", status)

            for key, p in social_platforms.items():
                s = p.status()
                status = "[green]Ready[/green]" if s["configured"] and s["enabled"] else \
                         "[yellow]Enabled, not configured[/yellow]" if s["enabled"] else "[dim]Disabled[/dim]"
                table.add_row(s["platform"], "Social", status)

            console.print(table)

        elif choice == "6":
            config = setup_wizard(config)
            brain = MarketAgentBrain()
