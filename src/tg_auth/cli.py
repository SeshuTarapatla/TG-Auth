__all__ = ["tg_auth"]

from async_typer import AsyncTyper
from my_modules.console import console

from tg_auth.controller import TelegramSecret

tg_auth = AsyncTyper(
    name="tg_auth",
    help="A CLI tool to manage telegram session and deploy to kubernetes.",
    no_args_is_help=True,
    add_completion=False,
)


@tg_auth.async_command(
    "login", help="Login to telegram session and save it as kubernetes secret."
)
async def tg_login(secret_name: str = "tg-auth"):
    await TelegramSecret.login()


@tg_auth.async_command(
    "logout", help="Logout any existing telegram session and clear kubernetes secrets."
)
async def tg_logout():
    console.error("[red]Logout[/] is not implemented yet.", kill=1)


@tg_auth.async_command(
    "verify", help="Verify any existing kubernetes secret for active telegram session."
)
async def tg_verify():
    await TelegramSecret.verify()
