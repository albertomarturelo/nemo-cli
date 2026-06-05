import json
from dataclasses import asdict
from datetime import date, timedelta

import typer
from rich.console import Console
from rich.table import Table

from nemo_cli.portfolio.movements import (
    Movements,
    MovementsSummary,
    get_movements,
)
from nemo_cli.portfolio.summary import (
    Portfolio,
    PortfolioTotals,
    get_portfolio_summary,
)

app = typer.Typer(
    help="Inspect your portfolio.",
    no_args_is_help=True,
)


@app.command("summary")
def summary(
    account_id: int = typer.Option(
        0, "--account-id", help="Account id to filter on (0 = all accounts)."
    ),
    currency: str = typer.Option(
        "CLP", "--currency", help="Base currency for balances (codMonedaSld)."
    ),
    with_dividends: bool = typer.Option(
        True,
        "--with-dividends/--no-dividends",
        help="Include dividends in the summary (conDividendos).",
    ),
    as_json: bool = typer.Option(
        False, "--json", help="Emit JSON (holdings + totals) instead of a table."
    ),
) -> None:
    """Show the portfolio summary: holdings, P&L, and totals by classification."""
    try:
        portfolio = get_portfolio_summary(
            account_id=account_id,
            currency=currency,
            with_dividends=with_dividends,
        )
    except Exception as error:
        typer.secho(str(error), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from error

    if as_json:
        _print_json(portfolio)
    else:
        _print_table(portfolio)


def _print_table(portfolio: Portfolio) -> None:
    console = Console()
    title = f"Portfolio summary — {portfolio.query_date or 'n/a'} ({portfolio.currency})"
    if not portfolio.holdings:
        console.print(f"[yellow]{title}: no holdings returned.[/yellow]")
        return

    holdings_table = Table(title=title)
    holdings_table.add_column("Nemotécnico", style="cyan", no_wrap=True)
    holdings_table.add_column("Descripción")
    holdings_table.add_column("Subclasificación", style="yellow")
    holdings_table.add_column("Cantidad", justify="right")
    holdings_table.add_column("Costo", justify="right")
    holdings_table.add_column("Mercado", justify="right")
    holdings_table.add_column("P&L", justify="right")
    holdings_table.add_column("P&L %", justify="right")

    for holding in portfolio.holdings:
        color = "green" if holding.pnl >= 0 else "red"
        holdings_table.add_row(
            holding.nemotecnico,
            holding.descripcion,
            holding.sub_classification,
            f"{holding.quantity:,.2f}",
            f"{holding.cost_basis:,.0f}",
            f"{holding.market_value:,.0f}",
            f"[{color}]{holding.pnl:+,.0f}[/{color}]",
            f"[{color}]{holding.pnl_pct * 100:+.2f}%[/{color}]",
        )
    console.print(holdings_table)
    console.print()

    _print_totals(console, portfolio.totals, portfolio.currency)


def _print_totals(console: Console, totals: PortfolioTotals, currency: str) -> None:
    by_class_table = Table(title=f"By classification ({currency})")
    by_class_table.add_column("Clasificación", style="bold")
    by_class_table.add_column("Mercado", justify="right")
    by_class_table.add_column("Costo", justify="right")
    by_class_table.add_column("P&L", justify="right")
    by_class_table.add_column("P&L %", justify="right")

    for classification in totals.by_classification:
        color = "green" if classification.pnl >= 0 else "red"
        by_class_table.add_row(
            classification.classification,
            f"{classification.market_value:,.0f}",
            f"{classification.cost_basis:,.0f}",
            f"[{color}]{classification.pnl:+,.0f}[/{color}]",
            f"[{color}]{classification.pnl_pct * 100:+.2f}%[/{color}]",
        )
    console.print(by_class_table)
    console.print()

    color = "green" if totals.pnl >= 0 else "red"
    console.print(
        f"[bold]Total:[/bold] {totals.market_value:,.0f} {currency}  "
        f"(cost {totals.cost_basis:,.0f})  "
        f"P&L [{color}]{totals.pnl:+,.0f}[/{color}] "
        f"([{color}]{totals.pnl_pct * 100:+.2f}%[/{color}])"
    )


def _print_json(portfolio: Portfolio) -> None:
    payload = {
        "currency": portfolio.currency,
        "query_date": portfolio.query_date,
        "totals": asdict(portfolio.totals),
        "holdings": [asdict(h) for h in portfolio.holdings],
    }
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))


def _default_desde() -> str:
    return (date.today() - timedelta(days=365)).isoformat()


def _default_hasta() -> str:
    return date.today().isoformat()


@app.command("movements")
def movements(
    desde: str = typer.Option(
        None,
        "--desde",
        help="Start date YYYY-MM-DD. Default: 1 year ago.",
    ),
    hasta: str = typer.Option(
        None,
        "--hasta",
        help="End date YYYY-MM-DD. Default: today.",
    ),
    account_id: int = typer.Option(
        0, "--account-id", help="Account id to filter on (0 = all accounts)."
    ),
    as_json: bool = typer.Option(
        False,
        "--json",
        help="Emit JSON (full movements + summaries) instead of a panel.",
    ),
) -> None:
    """List cash movements over a date range, classified per kind.

    Movement descriptions are parsed into structured `kind` values
    (`dividend`, `buy`, `sell`, `commission`, `cash_in`, `cash_out`,
    `other`) plus per-nemotécnico aggregates — handy for dividend yield
    analysis. Default window is the last 365 days.
    """
    desde_value = desde or _default_desde()
    hasta_value = hasta or _default_hasta()

    try:
        result = get_movements(
            desde=desde_value,
            hasta=hasta_value,
            account_id=account_id,
        )
    except Exception as error:
        typer.secho(str(error), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from error

    if as_json:
        _print_json_movements(result)
    else:
        _print_movements_panel(result)


def _print_movements_panel(result: Movements) -> None:
    console = Console()
    title = f"Movements — {result.desde} → {result.hasta}"
    if not result.buckets:
        console.print(f"[yellow]{title}: no movements returned.[/yellow]")
        return

    summary = result.summary
    bucket_currencies = sorted({b.movements[0].currency for b in result.buckets if b.movements})
    currency_label = " / ".join(bucket_currencies) or "—"

    totals_table = Table(title=f"{title} ({currency_label})")
    totals_table.add_column("Flow", style="bold")
    totals_table.add_column("Amount", justify="right")
    totals_table.add_row("Cash in", f"[green]+{summary.total_cash_in:,.0f}[/green]")
    totals_table.add_row("Cash out", f"[red]-{summary.total_cash_out:,.0f}[/red]")
    totals_table.add_row(
        "Dividends",
        f"[green]+{summary.total_dividends:,.0f}[/green]",
    )
    totals_table.add_row("Commissions", f"[red]-{summary.total_commissions:,.0f}[/red]")
    totals_table.add_row("Buys", f"[red]-{summary.total_buys:,.0f}[/red]")
    totals_table.add_row("Sells", f"[green]+{summary.total_sells:,.0f}[/green]")
    console.print(totals_table)
    console.print()

    if summary.by_dividend:
        div_table = Table(title="Dividends by instrument")
        div_table.add_column("Nemotécnico", style="cyan", no_wrap=True)
        div_table.add_column("Events", justify="right")
        div_table.add_column("Total received", justify="right")
        for item in summary.by_dividend:
            div_table.add_row(
                item.nemotecnico,
                str(item.occurrences),
                f"[green]+{item.total_received:,.0f}[/green]",
            )
        console.print(div_table)
        console.print()

    if summary.by_trade:
        trade_table = Table(title="Trades by instrument")
        trade_table.add_column("Nemotécnico", style="cyan", no_wrap=True)
        trade_table.add_column("Side", style="magenta")
        trade_table.add_column("Events", justify="right")
        trade_table.add_column("Total amount", justify="right")
        for item in summary.by_trade:
            color = "red" if item.side == "buy" else "green"
            sign = "-" if item.side == "buy" else "+"
            trade_table.add_row(
                item.nemotecnico,
                item.side,
                str(item.occurrences),
                f"[{color}]{sign}{item.total_amount:,.0f}[/{color}]",
            )
        console.print(trade_table)


def _print_json_movements(result: Movements) -> None:
    payload: dict[str, object] = {
        "desde": result.desde,
        "hasta": result.hasta,
        "summary": _summary_to_dict(result.summary),
        "buckets": [
            {
                "bucket_id": bucket.bucket_id,
                "name": bucket.name,
                "summary": _summary_to_dict(bucket.summary),
                "movements": [asdict(m) for m in bucket.movements],
            }
            for bucket in result.buckets
        ],
    }
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))


def _summary_to_dict(summary: MovementsSummary) -> dict[str, object]:
    return {
        "total_cash_in": summary.total_cash_in,
        "total_cash_out": summary.total_cash_out,
        "total_dividends": summary.total_dividends,
        "total_commissions": summary.total_commissions,
        "total_buys": summary.total_buys,
        "total_sells": summary.total_sells,
        "by_dividend": [asdict(item) for item in summary.by_dividend],
        "by_trade": [asdict(item) for item in summary.by_trade],
    }
