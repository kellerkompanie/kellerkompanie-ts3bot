import argparse
import asyncio
import logging
import sys
from pathlib import Path

from keko.ts3bot.config import CONFIG_PATH, Settings
from keko.ts3bot.keko_bot import TS3Bot

logger = logging.getLogger(__name__)


def load_settings(config_path: Path) -> Settings:
    if not config_path.exists():
        logger.error("Config file not found: %s", config_path)
        sys.exit(1)

    try:
        return Settings.from_yaml(config_path)
    except Exception as e:
        logger.error("Failed to load config file %s: %s", config_path, e)
        sys.exit(1)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(description="Kellerkompanie TeamSpeak 3 Bot")
    parser.add_argument(
        "--config",
        type=Path,
        default=CONFIG_PATH,
        help=f"Path to config file (default: {CONFIG_PATH})",
    )
    args = parser.parse_args()

    settings = load_settings(args.config)

    ts3bot = TS3Bot(settings)
    asyncio.run(ts3bot.start_bot())


if __name__ == "__main__":
    main()
