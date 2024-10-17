import asyncio
from asyncio.exceptions import CancelledError, IncompleteReadError
from websockets.exceptions import ConnectionClosed, ConnectionClosedError
from skay.Bot import Bot
from dotenv import load_dotenv
from skay.Logger import setup_logger
from time import sleep, strftime
from httpx import TimeoutException

logger = setup_logger()

load_dotenv()


async def start():
    bot = Bot()
    try:
        await bot.run()
    except (KeyboardInterrupt, CancelledError):
        logger.info("Соединение остановлено вручную " + strftime('%Y-%m-%d %H:%M:%S'))
    except IncompleteReadError as e:
        logger.info("IncompleteReadError " + strftime('%Y-%m-%d %H:%M:%S'))
        sleep(90)
        await start()
    except (ConnectionClosed, ConnectionClosedError) as e:
        logger.info("ConnectionClosed " + strftime('%Y-%m-%d %H:%M:%S'))
        sleep(90)
        await start()
    except TimeoutException as e:
        logger.info("TimeoutException " + strftime('%Y-%m-%d %H:%M:%S'))
        sleep(90)
        await start()
    except TimeoutError as e:
        logger.info("TimeoutError " + strftime('%Y-%m-%d %H:%M:%S'))
        sleep(90)
        await start()


if __name__ == '__main__':
    asyncio.run(start())
