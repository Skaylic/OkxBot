import asyncio
from time import sleep
from dotenv import load_dotenv
from skay.Logger import setup_logger
from skay.Bot import Bot
from websockets.exceptions import ConnectionClosedError

load_dotenv()

logger = setup_logger()


def run():
    try:
        bot = Bot()
        asyncio.run(bot.start())
    except KeyboardInterrupt:
        logger.info("Бот остановлен в ручную!")
    except TimeoutError:
        logger.error("TimeoutError")
        sleep(60)
        run()
    except ConnectionClosedError:
        logger.error("ConnectionClosedError")
        sleep(60)
        run()


if __name__ == '__main__':
    run()
