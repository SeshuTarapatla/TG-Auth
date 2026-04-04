__all__ = ["TelegramSecret"]

from asyncio import wait_for
from base64 import b64decode
from pathlib import Path
from re import fullmatch
from typing import Literal, overload

from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException
from my_modules.console import console
from my_modules.helpers import handle_await
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator
from telethon import TelegramClient
from telethon.sessions import StringSession

from tg_auth.exceptions import SecretNotFound


class Telegram(TelegramClient):
    def __init__(
        self,
        secret: "TelegramSecret",
        *,
        bot: bool,
    ) -> None:
        self.session: StringSession = StringSession(
            secret.TELEGRAM_BOT_SESSION if bot else secret.TELEGRAM_SESSION
        )
        self.api_id = int(secret.TELEGRAM_API_ID)
        self.api_hash = secret.TELEGRAM_API_HASH
        self.bot = bot
        self.phone_number = secret.TELEGRAM_NUMBER
        self.bot_token = secret.TELEGRAM_BOT_TOKEN
        super().__init__(self.session, self.api_id, self.api_hash)

    async def start(self) -> TelegramClient:  # type: ignore[override]
        if self.bot:
            _start = super().start(bot_token=self.bot_token)
        else:
            _start = super().start(phone=self.phone_number)
        return await handle_await(_start)

    @classmethod
    def get_client(cls, mode: Literal["user", "bot"] = "user") -> "Telegram":
        return cls(TelegramSecret.get(), bot=True if mode == "bot" else False)


class TelegramSecret(BaseModel):
    TELEGRAM_API_ID: str = ""
    TELEGRAM_API_HASH: str = ""
    TELEGRAM_NUMBER: str = ""
    TELEGRAM_SESSION: str = ""
    TELEGRAM_BOT_NAME: str = ""
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_BOT_SESSION: str = ""

    model_config = ConfigDict({"validate_assignment": True, "validate_default": True})

    @field_validator("TELEGRAM_API_ID")
    @classmethod
    def api_id_valdiator(cls, value: str) -> str:
        if value == "" or fullmatch(r"[0-9]{8}", value):
            return value
        raise ValueError(f"{value} is not a valid Telegram API ID.")

    @field_validator("TELEGRAM_API_HASH")
    @classmethod
    def api_hash_validator(cls, value: str) -> str:
        if value == "" or fullmatch(r"[0-9a-f]{32}", value):
            return value
        raise ValueError(f"{value} is not a valid Telegram API HASH.")

    @field_validator("TELEGRAM_NUMBER")
    @classmethod
    def number_validator(cls, value: str) -> str:
        if len(value) == 10 and value.isdecimal():
            value = "+91" + value
        if value == "" or fullmatch(r"\+[0-9]{12}", value):
            return value
        raise ValueError(f"{value} is not a valid Telegram Number.")

    @field_validator("TELEGRAM_BOT_TOKEN")
    @classmethod
    def bot_token_validator(cls, value: str) -> str:
        if value == "" or fullmatch(r"[0-9]{10}:[0-9a-zA-Z]{35}", value):
            return value
        raise ValueError(f"{value} is not a valid Telegram Bot Token.")

    @field_validator("TELEGRAM_SESSION", "TELEGRAM_BOT_SESSION")
    @classmethod
    def session_string_validator(cls, value: str) -> str:
        if value == "" or fullmatch(r"[0-9a-zA-Z\-_=]{353}", value):
            return value
        raise ValueError(f"{value} is not a valid Telegram Session String.")

    @overload
    @classmethod
    def get(
        cls, secret_name: str = "tg-auth", *, strict: Literal[True] = True
    ) -> "TelegramSecret": ...

    @overload
    @classmethod
    def get(
        cls, secret_name: str = "tg-auth", *, strict: Literal[False]
    ) -> tuple["TelegramSecret", bool]: ...

    @classmethod
    def get(
        cls, secret_name: str = "tg-auth", *, strict: bool = True
    ) -> "TelegramSecret | tuple['TelegramSecret', bool]":
        try:
            config.load_kube_config()
        except ConfigException:
            console.error("No kubernetes configuration found", kill=1)
        v1 = client.CoreV1Api()
        namespace = "default"
        secrets = [
            secret.metadata.name
            for secret in v1.list_namespaced_secret(namespace="default").items
        ]
        if secret_name in secrets:
            secret_data: dict[str, str] = getattr(
                v1.read_namespaced_secret(secret_name, namespace), "data"
            )
            decoded_data = {
                key: b64decode(value).decode() for key, value in secret_data.items()
            }
            secret, new = cls.model_validate(decoded_data), False
        elif strict:
            raise SecretNotFound("No telegram session secret found in kubernetes.")
        else:
            console.info("No existing session secret found. Creating a blank secret...")
            secret, new = cls(), True
            try:
                secret.TELEGRAM_API_ID = console.log_input(
                    "Please enter your Telegram API ID"
                )
                secret.TELEGRAM_API_HASH = console.log_input(
                    "Please enter your Telegram API HASH"
                )
                secret.TELEGRAM_NUMBER = console.log_input(
                    "Please enter your Telegram Number"
                )
                secret.TELEGRAM_BOT_NAME = console.log_input(
                    "Please enter your Telegram Bot Name"
                )
                secret.TELEGRAM_BOT_TOKEN = console.log_input(
                    "Please enter your Telegram Bot Token"
                )
            except ValidationError as e:
                console.error(
                    e.errors()[0]["msg"],
                    kill=1,
                )
        return secret if strict else (secret, new)

    def dump_env(self, file: Path = Path("./.env")) -> None:
        data = "\n".join(f"{key}='{value}'" for key, value in self.model_dump().items())
        file.write_text(data)

    def model_dump_env(self) -> list[str]:
        return [f"ENV {key}='{value}'" for key, value in self.model_dump().items()]

    @classmethod
    async def login(cls):
        secret, new = cls.get(strict=False)

        tl = Telegram(secret, bot=False)
        await tl.start()
        if new:
            console.info("New user session. [dim green]CONNECTED![/]")
        else:
            console.info("User session verified. [dim green]CONNECTED![/]")
        secret.TELEGRAM_SESSION = tl.session.save()

        bot_tl = Telegram(secret, bot=True)
        await bot_tl.start()
        if new:
            console.info("New bot  session. [dim green]CONNECTED![/]")
        else:
            console.info("Bot  session verified. [dim green]CONNECTED![/]")
        secret.TELEGRAM_BOT_SESSION = bot_tl.session.save()

        namespace, secret_name = "default", "tg-auth"
        v1 = client.CoreV1Api()
        secret_body = client.V1Secret(
            metadata=client.V1ObjectMeta(name=secret_name),
            string_data=secret.model_dump(),
        )
        if new:
            v1.create_namespaced_secret(namespace=namespace, body=secret_body)
            console.info("New secret [cyan]tg-auth[/] is deployed.")
        else:
            v1.patch_namespaced_secret(
                name=secret_name, namespace=namespace, body=secret_body
            )
            console.info("Existing secret patched with latest session strings.")

    @classmethod
    async def verify(cls):
        try:
            secret = cls.get(strict=True)
        except SecretNotFound:
            console.error("No secret found for [red]tg-auth[/].", kill=1)
        tl = Telegram(secret, bot=False)
        bot_tl = Telegram(secret, bot=True)

        try:
            await wait_for(tl.start(), timeout=3)
            console.info("User session verified. [dim green]CONNECTED![/]")
        except TimeoutError:
            console.info("User session: [dim red]DISCONNECTED![/]")

        try:
            await wait_for(bot_tl.start(), timeout=3)
            console.info("Bot  session verified. [dim green]CONNECTED![/]")
        except TimeoutError:
            console.info("Bot session: [dim red]DISCONNECTED![/]")
