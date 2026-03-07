import asyncio
from atexit import register
from os import getenv
from re import fullmatch

from my_modules.console import console
from my_modules.env import UserEnv
from my_modules.helpers import handle_await
from telethon import TelegramClient
from telethon.sessions import StringSession


class TelegramEnv:
    def __init__(self):
        self.update_flag = False
        self.TELEGRAM_API_ID = getenv("TELEGRAM_API_ID", "")
        self.TELEGRAM_API_HASH = getenv("TELEGRAM_API_HASH", "")
        self.TELEGRAM_NUMBER = getenv("TELEGRAM_NUMBER", "")
        self.TELEGRAM_SESSION = getenv("TELEGRAM_SESSION", "")
        self.TELEGRAM_BOT_TOKEN = getenv("TELEGRAM_BOT_TOKEN", "")
        self.TELEGRAM_BOT_SESSION = getenv("TELEGRAM_BOT_SESSION", "")
        self.ensure_api_id_and_hash()

    def ensure_api_id_and_hash(self):
        if not self.TELEGRAM_API_ID:
            api_id = console.log_input(
                "Telegram API ID is missing from the environment. [dim red]REQUIRED![/] Please enter API ID. ",
                tag="WARNING",
                color="yellow",
            )
            if not bool(fullmatch(r"[0-9]{8}", api_id)):
                console.error(
                    f"[red]{api_id}[/] is not a valid Telegram API ID.", kill=1
                )
            self.TELEGRAM_API_ID = api_id
            self.update()
        if not self.TELEGRAM_API_HASH:
            api_hash = console.log_input(
                "Telegram API HASH is missing from the environment. [dim red]REQUIRED![/] Please enter API HASH. ",
                tag="WARNING",
                color="yellow",
            )
            if not bool(fullmatch(r"[0-9a-fA-F]{32}", api_hash)):
                console.error(
                    f"[red]{api_hash}[/] is not a valid Telegram API HASH.", kill=1
                )
            self.TELEGRAM_API_HASH = api_hash
            self.update()

    def ensure_phone_number(self) -> str:
        if not self.TELEGRAM_NUMBER:
            phone_number = console.log_input(
                "Please enter Telegram registered phone number. [dim red]REQUIRED![/]"
            )
            if not bool(fullmatch(r"[0-9]{10}", phone_number)):
                console.error(
                    f"[red]+91{phone_number}[/] is not a valid phone number.", kill=1
                )
            self.TELEGRAM_NUMBER = "+91" + phone_number
            self.update()
        return self.TELEGRAM_NUMBER

    def ensure_bot_token(self) -> str:
        if not self.TELEGRAM_BOT_TOKEN:
            bot_token = console.log_input(
                "Please enter Telegram registered bot token. [dim blue]OPTIONAL![/]"
            )
            if not bot_token:
                return ""
            if not bool(fullmatch(r"[0-9]{10}:[0-9a-zA-Z]{35}", bot_token)):
                console.error(f"[red]{bot_token}[/] is not a valid bot token.", kill=1)
            self.TELEGRAM_BOT_TOKEN = bot_token
            self.update()
        return self.TELEGRAM_BOT_TOKEN

    def update(self):
        for key, value in self.__dict__.items():
            if key.startswith("TELEGRAM") and value != getenv(key):
                UserEnv.setx(key, value)
                register(self.restart_prompt)

    def restart_prompt(self):
        if not self.update_flag:
            console.print()
            console.info(
                "Environment variables updated. Please restart your temrinal for changes to take effect.\n"
            )
        self.update_flag = True


class Telegram(TelegramClient):
    def __init__(self, bot: bool = False):
        self.bot = bot
        self.fetch_session_vars()
        super().__init__(self.session, self.api_id, self.api_hash)

    def fetch_session_vars(self):
        self.env = TelegramEnv()
        if not (self.env.TELEGRAM_API_ID, self.env.TELEGRAM_API_HASH):
            raise EnvironmentError(
                "Telegram API ID and HASH are missing from the environment."
            )
        self.api_id = int(self.env.TELEGRAM_API_ID)
        self.api_hash = self.env.TELEGRAM_API_HASH
        self.session = StringSession(
            self.env.TELEGRAM_BOT_SESSION if self.bot else self.env.TELEGRAM_SESSION
        )

    async def start(self):  # type: ignore[override]:
        if not self.bot:
            self.phone_number = self.env.ensure_phone_number()
            _start = super().start(phone=self.phone_number)
        else:
            self.bot_token = self.env.ensure_bot_token()
            _start = super().start(bot_token=self.bot_token)
        _start = await handle_await(_start)
        _session = self.session.save()
        if not self.bot and self.env.TELEGRAM_SESSION != _session:
            self.env.TELEGRAM_SESSION = _session
            self.env.update()
        if self.bot and self.env.TELEGRAM_BOT_SESSION != _session:
            self.env.TELEGRAM_BOT_SESSION = _session
            self.env.update()
        return _start

    async def verify(self, timeout: float = 3) -> bool:
        if not self.session.save():
            return False
        try:
            await asyncio.wait_for(self.start(), timeout=timeout)
            return True
        except TimeoutError:
            return False

    @classmethod
    async def login(cls):
        tl = cls()
        if not await tl.verify():
            await tl.start()
            console.info("Saved User session in environment.")
        else:
            console.info("User session exists in environment. [dim green]CONNECTED![/]")
        bot_tl = cls(bot=True)
        if bot_tl.env.TELEGRAM_BOT_TOKEN and await bot_tl.verify():
            console.info("Bot token exists in environment. [dim green]CONNECTED![/]")
        else:
            if bot_tl.env.ensure_bot_token():
                await bot_tl.start()
                console.info(
                    "Bot token verified successfully. [dim green]CONNECTED![/]"
                )
