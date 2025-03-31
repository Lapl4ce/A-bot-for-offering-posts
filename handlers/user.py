from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, KeyboardButton, ReplyKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
import logging
from datetime import datetime

from states import PostCreation, Feedback
from database import Database
from keyboards import (
    get_main_keyboard,
    get_cancel_keyboard,
    get_statistics_keyboard,
    get_cancelFeedback_keyboard
)
from config import ADMIN_IDS
from utils import format_datetime
from aiogram.utils.keyboard import InlineKeyboardBuilder  # Add this import

router = Router()
logger = logging.getLogger(__name__)

@router.message(F.text == "❌ Отмена")
async def cancel_post_creation(message: Message, state: FSMContext):
    await state.clear()
    user = Database.get_user(message.from_user.id)
    await message.answer(
        "Создание поста отменено",
        reply_markup=get_main_keyboard(user and user.get('role') == 'admin')
    )
    
@router.message(F.text == "❌ Отменить")
async def cancel_post_creation(message: Message, state: FSMContext):
    await state.clear()
    user = Database.get_user(message.from_user.id)
    await message.answer(
        "Создание массовой рассылки отменено",
        reply_markup=get_main_keyboard(user and user.get('role') == 'admin')
    )
    

@router.message(F.text == "❌ Назад")
async def cancel_feedback_creation(message: Message, state: FSMContext):
    await state.clear()
    user = Database.get_user(message.from_user.id)
    await message.answer(
        "Создание обращения к администрации отменено",
        reply_markup=get_main_keyboard(user and user.get('role') == 'admin')
    )
@router.message(F.text == "📤 Предложить пост")
async def start_post_creation(message: Message, state: FSMContext):
    """Handle post creation initiation"""
    try:
        user = Database.get_user(message.from_user.id)
        if not user:
            await message.answer("Сначала зарегистрируйтесь с помощью /start")
            return
            
        # Fixed: Access Row object properly
        if user['status'] == 'blocked':
            await message.answer("❌ Вы заблокированы и не можете создавать посты.")
            return

        await state.set_state(PostCreation.waiting_for_text)
        await message.answer(
            "✍️ Напишите текст для поста (если не планируете добавлять пояснение к посту - оставьте точку.):\n"
            "❌ Используйте кнопку 'Отмена' для выхода",
            reply_markup=get_cancel_keyboard()
        )
    except Exception as e:
        logger.error(f"Error in start_post_creation: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")


@router.message(PostCreation.waiting_for_text)
async def process_post_text(message: Message, state: FSMContext):
    """Process post text and request image"""
    try:
        text = message.text if message.text and message.text.strip() else None
        await state.update_data(text=text)
        await state.set_state(PostCreation.waiting_for_image)
        
        await message.answer(
            "🖼 Теперь отправьте изображение для поста:",
            reply_markup=ReplyKeyboardRemove()
        )
    except Exception as e:
        logger.error(f"Error in process_post_text: {e}")
        await message.answer("❌ Ошибка обработки текста.")
        await state.clear()


@router.message(PostCreation.waiting_for_image, F.photo)
async def process_post_image(message: Message, state: FSMContext, bot: Bot):
    """Process post with image"""
    try:
        # Get data from state
        data = await state.get_data()
        text = data.get('text') if 'text' in data else None
        await state.clear()
        
        # Get user info
        user = Database.get_user(message.from_user.id)
        if not user:
            await message.answer("❌ Ошибка: пользователь не найден")
            return
            
        # Check if user is blocked (access Row object properly)
        if user['status'] == 'blocked':
            await message.answer("❌ Вы заблокированы и не можете создавать посты.")
            return

        # Create post (using the highest resolution photo)
        post_id = Database.create_post(
            user_id=user['internal_id'],
            text=text,
            image_file_id=message.photo[-1].file_id
        )
        
        # Notify admins
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=f"📨 Новый пост на модерацию!\n"
                         f"ID: {post_id}\n"
                         f"От: @{user['username'] or user['full_name']}\n"
                         f"Текст: {text[:100] if text else 'Нет текста'}"
                )
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")

        await message.answer(
            "✅ Ваш пост успешно отправлен на модерацию!",
            reply_markup=get_main_keyboard(user['role'] == 'admin')
        )
        
    except ValueError as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
    except Exception as e:
        logger.error(f"Error in process_post_image: {e}")
        await message.answer("❌ Произошла ошибка при создании поста.")
        await state.clear()
            
@router.message(PostCreation.waiting_for_image)
async def process_invalid_image(message: Message):
    await message.answer(
        "❌ Пожалуйста, отправьте изображение для поста.",
        reply_markup=get_cancel_keyboard()
    )


# [Rest of your handlers...]


# ======================
# FEEDBACK SYSTEM
# ======================

@router.message(F.text == "📨 Связь с администрацией")
async def start_feedback(message: Message, state: FSMContext):
    """Initiate feedback process"""
    try:
        if message.text == "/cancel":
            await state.clear()
            await message.answer("✅ Отмена. Вы возвращены в главное меню.", reply_markup=get_main_keyboard())
            return

        user = Database.get_user(message.from_user.id)
        if not user:
            await message.answer("ℹ️ Сначала зарегистрируйтесь с помощью /start")
            return
        
        if user['status'] == 'blocked':
            await message.answer("🚫 Вы заблокированы и не можете отправлять сообщения.")
            return

        await state.set_state(Feedback.waiting_for_message)
        await message.answer(
            "✍️ Напишите ваше сообщение администрации:\n\n"
            "ℹ️ Опишите ваш вопрос или проблему подробно\n"
            "❌ Для отмены просто напишите /cancel",
            reply_markup=get_cancelFeedback_keyboard()
        )
    except Exception as e:
        logger.error(f"Error in start_feedback: {e}")
        await message.answer("⚠️ Произошла ошибка. Попробуйте позже.")



@router.message(Feedback.waiting_for_message)
async def process_feedback_message(message: Message, state: FSMContext, bot: Bot):
    """Process user feedback and notify admins"""
    try:
        await state.clear()
        user = Database.get_user(message.from_user.id)
        feedback_id = Database.create_feedback(
            user_id=user['internal_id'],
            message=message.text
        )
        
        # Notify all admins
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=f"📩 Новое сообщение от пользователя!\n\n"
                         f"🆔 ID: {feedback_id}\n"
                         f"👤 От: @{user['username'] or user['full_name']}\n"
                         f"📅 Время: {format_datetime(datetime.now())}\n\n"
                         f"📝 Сообщение:\n{message.text[:300]}..."
                )
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")

        await message.answer(
            "✅ Ваше сообщение отправлено администрации!\n\n"
            "Мы ответим вам в ближайшее время.",
            reply_markup=get_main_keyboard(user['role'] == 'admin')
        )
    except Exception as e:
        logger.error(f"Error in process_feedback_message: {e}")
        await message.answer("⚠️ Ошибка при отправке сообщения. Попробуйте снова.")
        await state.clear()

# ======================
# POST HISTORY
# ======================

@router.message(F.text == "📜 История моих постов")
async def show_user_posts(message: Message):
    """Display user's post history"""
    try:
        user = Database.get_user(message.from_user.id)
        if not user:
            await message.answer("Сначала зарегистрируйтесь с помощью /start")
            return
            
        posts = Database.get_user_posts(user['internal_id'])
        if not posts:
            await message.answer("📭 У вас пока нет отправленных постов.")
            return

        response = "📜 История ваших постов:\n\n"
        for post in posts:
            status_emoji = {
                'pending': '⏳',
                'approved': '✅', 
                'rejected': '❌'
            }.get(post['status'], '❓')
            
            # Use direct dictionary access for sqlite3.Row
            created_at = format_datetime(post['created_at']) if 'created_at' in post else "Неизвестно"
            text_content = post['text_content'][:50] if post['text_content'] else 'Без текста'
            
            response += (
                f"{status_emoji} ID {post['post_id']} - {post['status']}\n"
                f"📅 {created_at}\n"
                f"📝 {text_content}\n"
                f"────────────────────\n"
            )

        await message.answer(response)
    except Exception as e:
        logger.error(f"Error in show_user_posts: {e}")
        await message.answer("❌ Ошибка при загрузке истории постов.")
# ======================
# STATISTICS
# ======================

@router.message(F.text == "📊 Статистика")
async def show_statistics_menu(message: Message):
    """Show statistics menu"""
    try:
        await message.answer(
            "📊 Выберите тип статистики:",
            reply_markup=get_statistics_keyboard()
        )
    except Exception as e:
        logger.error(f"Error in show_statistics_menu: {e}")
        await message.answer("⚠️ Ошибка при загрузке статистики.")

@router.callback_query(F.data == "top_approved")
async def show_top_approved_posts(callback: CallbackQuery):
    """Show top users by approved posts"""
    try:
        top_users = Database.get_top_users('approved_posts')
        if not top_users:
            await callback.answer("😕 Нет данных для отображения")
            return

        response = "🏆 Топ пользователей по одобренным постам:\n\n"
        for idx, user in enumerate(top_users, 1):
            response += f"{idx}. @{user['username']} - {user['approved_posts']} пост(ов)\n"

        await callback.message.edit_text(response)
    except Exception as e:
        logger.error(f"Error in show_top_approved_posts: {e}")
        await callback.answer("⚠️ Ошибка при загрузке статистики")

@router.callback_query(F.data == "top_rejected")
async def show_top_rejected_posts(callback: CallbackQuery):
    """Show top users by rejected posts"""
    try:
        top_users = Database.get_top_users('rejected_posts')
        if not top_users:
            await callback.answer("😕 Нет данных для отображения")
            return

        response = "💢 Топ пользователей по отклоненным постам:\n\n"
        for idx, user in enumerate(top_users, 1):
            response += f"{idx}. @{user['username']} - {user['rejected_posts']} пост(ов)\n"

        await callback.message.edit_text(response)
    except Exception as e:
        logger.error(f"Error in show_top_rejected_posts: {e}")
        await callback.answer("⚠️ Ошибка при загрузке статистики")

# ======================
# NOTIFICATION SYSTEM
# ======================
async def notify_post_status(user_id: int, post_id: int, status: str, bot: Bot, reason: str = None):
    """Notify user about post status change"""
    try:
        user = Database.get_user_by_id(user_id)
        if not user:
            return
            
        post = Database.get_post(post_id)
        if not post:
            return

        status_text = {
            'approved': 'одобрен ✅',
            'rejected': 'отклонен ❌'
        }.get(status, status)

        message = (
            f"ℹ️ Статус вашего поста изменен:\n\n"
            f"🆔 ID: {post_id}\n"
            f"📅 Дата: {format_datetime(post['created_at'])}\n"
            f"🔹 Новый статус: {status_text}\n"
        )

        if post['reviewed_by']:
            admin = Database.get_user(post['reviewed_by'])
            if admin:
                message += f"👨‍💻 Администратор: @{admin['username']}\n"

        if status == 'rejected' and reason:
            message += f"📝 Причина: {reason}\n"

        await bot.send_message(
            chat_id=user['telegram_id'],
            text=message
        )
    except Exception as e:
        logger.error(f"Failed to notify user {user_id}: {e}")
        
async def notify_feedback_response(feedback_id: int, response_text: str, bot: Bot):
    """Notify user about admin response to feedback"""
    try:
        feedback = Database.get_feedback(feedback_id)
        if not feedback:
            return

        await bot.send_message(
            chat_id=feedback['telegram_id'],
            text=f"📩 Ответ от администрации:\n\n{response_text}"
        )
    except Exception as e:
        logger.error(f"Failed to notify user about feedback response: {e}")