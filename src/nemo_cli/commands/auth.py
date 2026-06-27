"""The `nemo auth` command group (ADR-027).

Assembles the per-verb auth modules (`login`, `logout`, `status`) into a single
Typer sub-app, mirroring `instruments` / `portfolio`. The verb modules stay
one-function-each; this module only wires them together.
"""

import typer

from nemo_cli.commands.login import login
from nemo_cli.commands.logout import logout
from nemo_cli.commands.status import status

app = typer.Typer(
    name="auth",
    help="Authentication: sign in, sign out, and inspect session state.",
    no_args_is_help=True,
)

app.command()(login)
app.command()(logout)
app.command()(status)
