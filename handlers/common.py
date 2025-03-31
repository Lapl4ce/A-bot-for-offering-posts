from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import logging

from config import ADMIN_IDS
from database import Database
from keyboards import get_main_keyboard

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command for new and existing users"""
    try:
        # Add/update user in database
        Database.add_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name
        )
        
        # Check if user is admin and update role if needed
        if message.from_user.id in ADMIN_IDS:
            Database.update_user(
                telegram_id=message.from_user.id,
                updates={"role": "admin"}
            )

        welcome_message = (
            "👋 *Добро пожаловать в Ботонутую предложку!*\n\n"
            "📌 *Основные функции:*\n"
            "📤 Предложить пост - создать публикацию\n"
            "📨 Связь с администрацией - задать вопрос\n"
            "📜 История постов - ваши публикации\n"
            "📊 Статистика - активность пользователей\n\n"
            "❗ *Требования к постам:*\n"
            "- Изображение обязательно\n"
            "- Текст по желанию\n"
        )

        await message.answer(
            welcome_message,
            reply_markup=get_main_keyboard(message.from_user.id in ADMIN_IDS),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error in cmd_start: {e}")
        await message.answer("❌ Произошла ошибка при запуске бота.")

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    try:
        help_message = (
            "ℹ️ *Справка по командам:*\n\n"
            "📌 *Основные команды:*\n"
            "/start - перезапустить бота\n"
            "/help - показать эту справку\n\n"
            "📌 *Работа с постами:*\n"
            "1. Нажмите '📤 Предложить пост'\n"
            "2. Добавьте текст (по желанию)\n"
            "3. Прикрепите изображение\n\n"
            "📌 *Обратная связь:*\n"
            "Вы можете задать вопрос через '📨 Связь с администрацией'"
        )

        await message.answer(
            help_message,
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
    except Exception as e:
        logger.error(f"Error in cmd_help: {e}")
        await message.answer("❌ Не удалось показать справку.")

@router.message(F.text == "🔙 Главное меню")
async def return_to_main_menu(message: Message, state: FSMContext):
    try:
        await state.clear()
        user = Database.get_user(message.from_user.id)
        if not user:
            await message.answer("Ошибка: пользователь не найден")
            return
            
        # Convert Row to dict if needed
        if hasattr(user, '_asdict'):
            user = user._asdict()
        elif not isinstance(user, dict):
            user = dict(user)
            
        is_admin = user.get('role') == 'admin'
        await message.answer(
            "Вы вернулись в главное меню",
            reply_markup=get_main_keyboard(is_admin)
        )
    except Exception as e:
        logger.error(f"Error in return_to_main_menu: {e}")
        await message.answer("Произошла ошибка при возврате в меню")
        
@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Admin command handler"""
    try:
        user = Database.get_user(message.from_user.id)
        if not user or (user.get('role') != 'admin' and message.from_user.id not in ADMIN_IDS):
            await message.answer(
                "❌ Эта команда доступна только администраторам.",
                reply_markup=ReplyKeyboardRemove()
            )
            return

        admin_help = (
            "👨‍💻 *Административные команды:*\n\n"
            "👥 Пользователи - список всех пользователей\n"
            "📝 Нерассмотренные посты - новые публикации\n"
            "✅ Одобренные посты - принятые публикации\n"
            "❌ Отклоненные посты - отклоненные публикации\n"
            "📩 Обратная связь - вопросы от пользователей"
        )

        await message.answer(
            admin_help,
            parse_mode="Markdown",
            reply_markup=get_main_keyboard(True)
        )
    except Exception as e:
        logger.error(f"Error in cmd_admin: {e}")
        await message.answer("❌ Ошибка выполнения команды.")

@router.message(Command("id"))
async def cmd_id(message: Message):
    """Show user ID"""
    try:
        await message.answer(
            f"🆔 Ваш ID: `{message.from_user.id}`",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
    except Exception as e:
        logger.error(f"Error in cmd_id: {e}")
        await message.answer("❌ Не удалось получить ID.")

# Error handler for unauthorized commands
@router.message(F.text.startswith('/admin'))
async def handle_admin_unauthorized(message: Message):
    """Block admin commands for regular users"""
    try:
        user = Database.get_user(message.from_user.id)
        if not user or (user.get('role') != 'admin' and message.from_user.id not in ADMIN_IDS):
            await message.answer(
                "❌ У вас нет доступа к административным командам.",
                reply_markup=get_main_keyboard(False)
            )
    except Exception as e:
        logger.error(f"Error in handle_admin_unauthorized: {e}")