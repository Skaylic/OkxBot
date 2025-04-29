import asyncio
import os
import sys
import traceback

from dotenv import load_dotenv
from skay.Bot import Bot
from skay.Logger import setup_logger

load_dotenv()
logger = setup_logger(os.getenv('BOT_NAME'))

def main():
    logger.info('Starting bot...')
    try:
        bot = Bot()
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.debug("Keyboard Interrupt...")
    except Exception as e:
        logger.error("Exception " + str(e))
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
