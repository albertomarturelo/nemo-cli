import json
from dataclasses import asdict

import typer
from rich.console import Console
from rich.table import Table

from nemo_cli.instruments.international import (
    InternationalAssetsPage,
    list_international_assets,
)
from nemo_cli.instruments.local import (
    DEFAULT_SUBCLASSES,
    LocalInstrumentsPage,
    list_local_instruments,
)
from nemo_cli.instruments.prices import (
    PriceHistory,
    get_price_history,
)

app = typer.Typer(
    help="Browse instruments — local Chilean and international markets.",
    no_args_is_help=True,
)


@app.command("local")
def local(
    search: str = typer.Option("", "--search", "-s", help="Substring filter on nemotecnico."),
    classes: str = typer.Option(
        ",".join(DEFAULT_SUBCLASSES),
        "--classes",
        help="Comma-separated subclasses (ACC, ACC_INT, CFI, ETF, OPC, …).",
    ),
    page: int = typer.Option(1, "--page", min=1),
    limit: int = typer.Option(30, "--limit", min=1, max=200),
    as_json: bool = typer.Option(False, "--json", help="Emit JSON instead of a table."),
) -> None:
    """List local Chilean instruments via the FiltrarInstrumentos endpoint."""
    subclasses = tuple(c.strip() for c in classes.split(",") if c.strip())
    try:
        page_result = list_local_instruments(
            search=search,
            subclasses=subclasses,
            page=page,
            limit=limit,
        )
    except Exception as error:
        typer.secho(str(error), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from error

    if as_json:
        _print_json_local(page_result, page=page, limit=limit)
    else:
        _print_table_local(page_result, page=page, limit=limit)


@app.command("international")
def international(
    search: str = typer.Option("", "--search", "-s", help="Substring filter on symbol/name."),
    exchange: str = typer.Option("", "--exchange", help="Restrict to an exchange (NASDAQ, NYSE)."),
    page: int = typer.Option(1, "--page", min=1),
    page_size: int = typer.Option(30, "--page-size", min=1, max=200),
    as_json: bool = typer.Option(False, "--json", help="Emit JSON instead of a table."),
) -> None:
    """List international (US equities) assets via the frontoffice/Asset endpoint."""
    try:
        page_result = list_international_assets(
            search=search,
            exchange=exchange,
            page=page,
            page_size=page_size,
        )
    except Exception as error:
        typer.secho(str(error), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from error

    if as_json:
        _print_json_international(page_result, page=page, page_size=page_size)
    else:
        _print_table_international(page_result, page=page, page_size=page_size)


def _print_table_local(page_result: LocalInstrumentsPage, *, page: int, limit: int) -> None:
    console = Console()
    table = Table(title=f"Local instruments — page {page} ({page_result.total} total)")
    table.add_column("Nemotécnico", style="cyan", no_wrap=True)
    table.add_column("Descripción", style="white")
    table.add_column("Subclase", style="magenta")
    table.add_column("Familia", style="yellow")
    table.add_column("Moneda")
    table.add_column("ISIN", style="dim")

    for instrument in page_result.items:
        table.add_row(
            instrument.nemotecnico,
            instrument.descripcion,
            instrument.cod_sub_clase,
            instrument.codigo_familia,
            instrument.cod_moneda,
            instrument.isin or "—",
        )
    console.print(table)
    _print_pagination_hint(total=page_result.total, page=page, page_size=limit)


def _print_table_international(
    page_result: InternationalAssetsPage,
    *,
    page: int,
    page_size: int,
) -> None:
    console = Console()
    table = Table(title=f"International assets — page {page} ({page_result.total} total)")
    table.add_column("Symbol", style="cyan", no_wrap=True)
    table.add_column("Name", style="white")
    table.add_column("Exchange", style="magenta")
    table.add_column("Class", style="yellow")
    table.add_column("Tradable", justify="center")
    table.add_column("Volume", justify="right")

    for asset in page_result.items:
        table.add_row(
            asset.symbol,
            asset.name,
            asset.exchange,
            asset.asset_class,
            "✓" if asset.tradable else "✗",
            f"{asset.volume:,}",
        )
    console.print(table)
    _print_pagination_hint(total=page_result.total, page=page, page_size=page_size)


def _print_pagination_hint(*, total: int, page: int, page_size: int) -> None:
    if total <= page * page_size:
        return
    remaining = total - page * page_size
    console = Console()
    console.print(
        f"[dim]… {remaining} more. Use --page {page + 1} to continue.[/dim]"
    )


def _print_json_local(
    page_result: LocalInstrumentsPage,
    *,
    page: int,
    limit: int,
) -> None:
    payload = {
        "market": "local",
        "page": page,
        "page_size": limit,
        "total": page_result.total,
        "items": [asdict(item) for item in page_result.items],
    }
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))


def _print_json_international(
    page_result: InternationalAssetsPage,
    *,
    page: int,
    page_size: int,
) -> None:
    payload = {
        "market": "international",
        "page": page,
        "page_size": page_size,
        "total": page_result.total,
        "items": [asdict(item) for item in page_result.items],
    }
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))


@app.command("prices")
def prices(
    instrument_id: int = typer.Option(
        ...,
        "--id",
        help=(
            "Local instrument id (idInstrumento). Find it via "
            "`nemo instruments local --search NEMO --json`."
        ),
    ),
    as_json: bool = typer.Option(
        False, "--json", help="Emit JSON (stats + full point series) instead of a stats panel."
    ),
) -> None:
    """Show ~1 year of daily price history for a local Chilean instrument.

    Note: this endpoint is **not available for international assets** —
    use it only with `idInstrumento` values from `nemo instruments local`.
    """
    try:
        history = get_price_history(instrument_id=instrument_id)
    except Exception as error:
        typer.secho(str(error), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from error

    if as_json:
        _print_json_prices(history)
    else:
        _print_prices_panel(history)


def _print_prices_panel(history: PriceHistory) -> None:
    console = Console()
    if not history.points or history.stats is None:
        console.print(
            f"[yellow]No price data for instrument {history.instrument_id}. "
            f"Note: this endpoint only serves local Chilean instruments.[/yellow]"
        )
        return

    stats = history.stats
    color = "green" if stats.total_return_pct >= 0 else "red"

    table = Table(title=f"Price history — instrument {history.instrument_id}")
    table.add_column("Field", style="bold")
    table.add_column("Value", justify="right")
    table.add_row("Period", f"{stats.first_date} → {stats.last_date}")
    table.add_row("Days", f"{stats.days}")
    table.add_row("First", f"{stats.first_price:,.2f}")
    table.add_row("Last", f"{stats.last_price:,.2f}")
    table.add_row(
        "Total return",
        f"[{color}]{stats.total_return_pct * 100:+.2f}%[/{color}]",
    )
    table.add_row("Min", f"{stats.min_price:,.2f}  ({stats.min_date})")
    table.add_row("Max", f"{stats.max_price:,.2f}  ({stats.max_date})")
    table.add_row("Mean", f"{stats.mean_price:,.2f}")
    table.add_row(
        "Daily return σ",
        f"{stats.daily_return_std_pct * 100:.3f}%  (not annualised)",
    )
    console.print(table)
    console.print()

    sparkline = _sparkline([p.price for p in history.points])
    console.print(f"[bold]Trend:[/bold] {sparkline}")


def _sparkline(prices: list[float], width: int = 80) -> str:
    if not prices:
        return ""
    chars = "▁▂▃▄▅▆▇█"
    if len(prices) > width:
        step = len(prices) / width
        sampled = [prices[int(i * step)] for i in range(width)]
    else:
        sampled = prices
    pmin, pmax = min(sampled), max(sampled)
    if pmax == pmin:
        return chars[3] * len(sampled)
    out: list[str] = []
    for value in sampled:
        idx = int((value - pmin) / (pmax - pmin) * (len(chars) - 1))
        out.append(chars[idx])
    return "".join(out)


def _print_json_prices(history: PriceHistory) -> None:
    payload: dict[str, object] = {
        "instrument_id": history.instrument_id,
        "stats": asdict(history.stats) if history.stats is not None else None,
        "points": [asdict(p) for p in history.points],
    }
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
