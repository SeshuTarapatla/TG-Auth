__all__ = ["tg_auth", "TelegramSecret"]

from tg_auth.cli import tg_auth
from tg_auth.controller import TelegramSecret

if __name__ == "__main__":
    tg_auth()
