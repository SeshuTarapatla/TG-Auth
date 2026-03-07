__all__ = ["tg"]

from async_typer import AsyncTyper

from tg_auth.controller import Telegram

tg = AsyncTyper(
    name="tg",
    help="Telegram CLI to manage session in USER environment.",
    no_args_is_help=True,
    add_completion=False,
)


@tg.async_command(name="login", help="Login to telegram and save session.")
async def tg_login():
    await Telegram.login()


@tg.async_command(name="logout", help="Logout from telegram and remove saved session.")
async def tg_logout():
    raise NotImplementedError("Logout method is not yet implement.")


@tg.async_command(name="verify", help="Verify current env session connectivity.")
async def tg_verify():
    raise NotImplementedError("Verify method is redundant. Please use login.")
