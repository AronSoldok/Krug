import asyncio
import logging

from config import config, bot, dp
from app.handlers import router as handlers

async def main():
    dp.include_routers(handlers)
    await dp.start_polling(bot)
    


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except:
        print('Exit')
