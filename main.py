import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from database import init_db
from handlers import common, user, admin

async def main():
    # Initialize database
    init_db()
    
    # Initialize bot with default properties
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Include routers
    dp.include_router(common.router)
    dp.include_router(user.router)
    dp.include_router(admin.router)
    
    # Start polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
async def main():
    try:
        # Validate token first
        if not BOT_TOKEN:
            raise ValueError("BOT_TOKEN is not set in config.py")
        
        # Initialize database
        init_db()
        logger.info("Database initialized successfully")
        
        # Initialize bot with default properties
        bot = Bot(
            token=BOT_TOKEN,
            default=DefaultBotProperties(
                parse_mode=ParseMode.HTML,
                link_preview_is_disabled=True
            )
        )
        
        # Create storage and dispatcher
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # Register middlewares
        dp.update.middleware(AdminProtectionMiddleware())
        
        # Include routers
        dp.include_router(common.router)
        dp.include_router(user.router)
        dp.include_router(admin.router)
        
        # Set bot commands
        await set_default_commands(bot)
        
        # Notify admins about bot start
        await notify_admins(bot, "🤖 Бот успешно запущен!")
        
        # Start polling
        logger.info("Starting bot polling...")
        await dp.start_polling(bot)
        
    except TokenValidationError:
        logger.error("Invalid bot token provided")
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}", exc_info=True)
    finally:
        await bot.session.close() if 'bot' in locals() else None
        logger.info("Bot stopped")

async def set_default_commands(bot: Bot):
    """Set default bot commands"""
    from aiogram.types import BotCommand
    commands = [
        BotCommand(command="start", description="Начать работу с ботом"),
        BotCommand(command="help", description="Помощь и инструкции"),
        BotCommand(command="profile", description="Просмотр профиля (для админов)")
    ]
    await bot.set_my_commands(commands)

async def notify_admins(bot: Bot, message: str):
    """Send notification to all admins"""
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, message)
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {str(e)}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by keyboard interrupt")
    except Exception as e:
        logger.critical(f"Unexpected error: {str(e)}", exc_info=True)