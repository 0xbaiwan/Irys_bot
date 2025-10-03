import asyncio
import multiprocessing
import signal
import sys
import warnings

from multiprocessing import freeze_support
from loguru import logger

from application import ApplicationManager
from loader import config
from utils import setup_logs


warnings.filterwarnings("ignore")


async def main():
    app = ApplicationManager()

    try:
        await app.initialize()
        await app.run()
    except asyncio.CancelledError:
        logger.info("主任务已取消")
    except Exception as e:
        logger.error(f"发生错误: {e}")


if __name__ == "__main__":
    freeze_support()
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    signal.signal(signal.SIGINT, lambda s, f: asyncio.get_event_loop().stop())
    signal.signal(signal.SIGTERM, lambda s, f: asyncio.get_event_loop().stop())

    try:
        setup_logs(is_main=True)
        asyncio.run(main())
    except Exception as error:
        logger.error(f"发生错误: {error}")

    input("\n按 Enter 键退出...")
