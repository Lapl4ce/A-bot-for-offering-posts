from aiogram.utils.keyboard import InlineKeyboardBuilder  # Add this import
from aiogram import Router, F, Bot
from aiogram.types import (
    Message, 
    CallbackQuery, 
    ReplyKeyboardMarkup, 
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.filters import Command  # Add this import
from aiogram.fsm.context import FSMContext

from states import UserManagement, Feedback, MassNotification
from database import Database
from keyboards import (
    get_admin_keyboard,
    get_post_actions_keyboard,
    get_user_profile_keyboard,
    get_feedback_response_keyboard,
    get_cancel_keyboard,
    get_cancelFeedback_keyboard,
    get_mass_notification_keyboard,
    get_cancel_Notify_keyboard,
    get_main_keyboard
)
from config import ADMIN_IDS
import logging
from utils import format_datetime

router = Router()
logger = logging.getLogger(__name__)

async def send_post_details(message: Message, post_id: int):
    """Send detailed post information with proper formatting"""
    try:
        post = Database.get_post_with_details(post_id)
        if not post:
            await message.answer("Пост не найден.")
            return

        # Prepare basic info
        response = (
            f"📝 <b>Детали поста</b>\n\n"
            f"🆔 <b>ID:</b> {post['post_id']}\n"
            f"👤 <b>Автор:</b> @{post['user_username'] or 'нет'} (ID: {post['user_telegram_id']})\n"
            f"📅 <b>Дата:</b> {format_datetime(post['created_at'])}\n"
            f"🔹 <b>Статус:</b> {post['status']}\n"
        )

        # Add review info if available
        if post['reviewed_at']:
            response += f"📅 <b>Модерация:</b> {format_datetime(post['reviewed_at'])}\n"
        if post['admin_username']:
            response += f"👨‍💻 <b>Модератор:</b> @{post['admin_username']}\n"
        if post['rejection_reason']:
            response += f"📝 <b>Причина отказа:</b> {post['rejection_reason']}\n"

        # Add text content (with proper escaping)
        post_text = post['text_content'] or "Текст отсутствует"
        response += f"\n📄 <b>Текст:</b>\n<code>{escape_html(post_text[:1000])}</code>"

        # Send message with or without photo
        if post['image_file_id']:
            try:
                await message.answer_photo(
                    post['image_file_id'],
                    caption=response,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Error sending photo: {e}")
                await message.answer(
                    "🖼 <b>Изображение:</b> (не удалось отправить)\n\n" + response,
                    parse_mode="HTML"
                )
        else:
            await message.answer(
                "🖼 <b>Изображение:</b> отсутствует\n\n" + response,
                parse_mode="HTML"
            )

    except Exception as e:
        logger.error(f"Error in send_post_details: {e}")
        await message.answer("Произошла ошибка при загрузке поста.")

@router.message(F.text.regexp(r'^/post \d+$'))
async def handle_post_view_request(message: Message):
    try:
        post_id = int(message.text.split(' ')[1])
        post = Database.get_post_with_details(post_id)
        
        if not post:
            await message.answer("Пост не найден")
            return
        
        user = Database.get_user(message.from_user.id)
        if not user or user['role'] != 'admin':
            await message.answer("❌ У вас нет доступа к командам администрации")
            return
        # Convert Row to dict if needed
        if hasattr(post, '_asdict'):
            post = post._asdict()
        elif not isinstance(post, dict):
            post = dict(post)

        response = (
            f"📝 Детали поста:\n\n"
            f"🆔 ID: {post.get('post_id', 'N/A')}\n"
            f"👤 Автор: @{post.get('user_username', 'N/A')} (ID: {post.get('user_telegram_id', 'N/A')})\n"
            f"📅 Дата отправки: {post.get('created_at', 'N/A')}\n"
            f"🔹 Статус: {post.get('status', 'N/A')}\n"
        )
        
        if post.get('reviewed_at'):
            response += f"📅 Дата модерации: {post.get('reviewed_at')}\n"
        if post.get('admin_username'):
            response += f"👨‍💻 Модератор: @{post.get('admin_username')}\n"
        if post.get('rejection_reason') and post.get('status') == 'rejected':
            response += f"📝 Причина отклонения: {post.get('rejection_reason')}\n"
            
        if post.get('image_file_id'):
            await message.answer_photo(
                post['image_file_id'],
                caption=response + f"\n📝 Текст: {post.get('text_content', 'не указан')}",
                reply_markup=get_post_actions_keyboard(post['post_id']) if post.get('status') == 'pending' else None
            )
        else:
            await message.answer(
                response + f"\n📝 Текст: {post.get('text_content', 'не указан')}",
                reply_markup=get_post_actions_keyboard(post['post_id']) if post.get('status') == 'pending' else None
            )

        # Return the admin keyboard after the post details
        await message.answer("Для просмотра профиля отправителя поста введите /user ID", reply_markup=get_admin_keyboard())

    except ValueError:
        await message.answer("Неверный формат. Используйте: /post ID")
    except Exception as e:
        logger.error(f"Error in handle_post_view_request: {e}")
        await message.answer("Произошла ошибка при просмотре поста")


async def show_pending_posts(message: Message, bot: Bot):
    """Show all pending posts for moderation"""
    try:
        posts = Database.get_posts_by_status('pending')
        if not posts:
            await message.answer("ℹ️ Нет постов, ожидающих модерации.")
            return

        for post in posts:
            caption = (
                f"🆔 ID поста: {post['post_id']}\n"
                f"👤 Автор: @{post['username']} (ID: {post['telegram_id']})\n"
                f"📅 Дата: {format_datetime(post['created_at'])}\n"
                f"📝 Текст: {post['text_content'] or 'отсутствует'}"
            )

            if post['image_file_id']:
                await bot.send_photo(
                    chat_id=message.chat.id,
                    photo=post['image_file_id'],
                    caption=caption,
                    reply_markup=get_post_actions_keyboard(post['post_id'])
                )
            else:
                await message.answer(
                    caption,
                    reply_markup=get_post_actions_keyboard(post['post_id'])
                )

        # Return the admin keyboard after showing pending posts
        await message.answer("Для просмотра профиля отправителя поста введите /user ID", reply_markup=get_admin_keyboard())

    except Exception as e:
        logger.error(f"Error showing pending posts: {e}")
        await message.answer("❌ Ошибка при загрузке постов.")


# ======================
# ADMIN PANEL
# ======================

@router.message(F.text == "👨‍💻 Админ-панель")
async def admin_panel(message: Message):
    """Show admin panel"""
    try:
        user = Database.get_user(message.from_user.id)
        if not user or user['role'] != 'admin':
            await message.answer("❌ У вас нет доступа к админ-панели")
            return
        
        await message.answer(
            "👨‍💻 Панель администратора",
            reply_markup=get_admin_keyboard()
        )
    except Exception as e:
        logger.error(f"Error in admin_panel: {e}")
        await message.answer("❌ Ошибка доступа к админ-панели")

# ======================
# USER MANAGEMENT
# ======================

@router.message(F.text == "👥 Пользователи")
async def show_users_list(message: Message):
    """Show list of all users"""
    try:
        users = Database.get_all_users()
        if not users:
            await message.answer("ℹ️ В базе нет пользователей")
            return
        user = Database.get_user(message.from_user.id)
        if not user or user['role'] != 'admin':
            await message.answer("❌ У вас нет доступа к командам администрации")
            return
        response = "👥 Список пользователей:\n\n"
        for user in users:
            status = "🔴" if user['status'] == 'blocked' else "🟢"
            role = "👑" if user['role'] == 'admin' else "👤"
            response += (
                f"{status}{role} ID: {user['internal_id']}\n"
                f"👤 @{user['username'] or 'нет'}\n"
                f"📅 Рег.: {format_datetime(user['created_at'])}\n"
                f"📊 Постов: {user['submitted_posts']} | "
                f"✅ {user['approved_posts']} | ❌ {user['rejected_posts']}\n"
                f"────────────────────\n"
            )
        
        await message.answer(
            response,
            reply_markup=ReplyKeyboardRemove()
        )
        await message.answer(
            "Для управления введите /user [ID]\n"
            "Пример: /user 1",
            reply_markup=get_admin_keyboard()
        )
    except Exception as e:
        logger.error(f"Error in show_users_list: {e}")
        await message.answer("❌ Ошибка загрузки пользователей")

@router.message(Command("user"))
async def show_user_profile(message: Message):
    """Show detailed user profile"""
    try:
        args = message.text.split()
        if len(args) < 2:
            await message.answer("ℹ️ Используйте: /user [ID]")
            return
        user = Database.get_user(message.from_user.id)
        if not user or user['role'] != 'admin':
            await message.answer("❌ У вас нет доступа к командам администратора")
            return
            
        user_id = int(args[1])
        user = Database.get_user_by_id(user_id)
        
        if not user:
            await message.answer("❌ Пользователь не найден")
            return
            
        status = "🔴 Заблокирован" if user['status'] == 'blocked' else "🟢 Активен"
        role = "👑 Админ" if user['role'] == 'admin' else "👤 Пользователь"
        
        response = (
            f"👤 Профиль пользователя:\n\n"
            f"🆔 ID: {user['internal_id']}\n"
            f"📱 Telegram ID: {user['telegram_id']}\n"
            f"👤 Имя: {user['full_name'] or 'Не указано'}\n"
            f"🔹 Ник: @{user['username'] or 'нет'}\n"
            f"👥 Роль: {role}\n"
            f"🔹 Статус: {status}\n"
            f"📅 Регистрация: {format_datetime(user['created_at'])}\n\n"
            f"📊 Статистика:\n"
            f"📤 Отправлено: {user['submitted_posts']}\n"
            f"✅ Одобрено: {user['approved_posts']}\n"
            f"❌ Отклонено: {user['rejected_posts']}"
        )
        
        await message.answer(
            response,
            reply_markup=get_user_profile_keyboard(
                user['internal_id'],
                user['status'] == 'blocked'
            )
        )
    except ValueError:
        await message.answer("❌ Неверный ID. Введите число")
    except Exception as e:
        logger.error(f"Error in show_user_profile: {e}")
        await message.answer("❌ Ошибка загрузки профиля")

@router.callback_query(F.data.startswith("block_user:"))
async def block_user(callback: CallbackQuery, state: FSMContext):
    """Initiate user blocking"""
    try:
        user_id = int(callback.data.split(":")[1])
        await state.set_state(UserManagement.waiting_for_block_reason)
        await state.update_data(user_id=user_id)
        await callback.message.answer(
            "✏️ Введите причину блокировки:",
            reply_markup=get_cancel_keyboard()
        )
    except Exception as e:
        logger.error(f"Error in block_user: {e}")
        await callback.answer("❌ Ошибка блокировки")

@router.message(UserManagement.waiting_for_block_reason)
async def process_block_reason(message: Message, state: FSMContext, bot: Bot):
    """Process user blocking"""
    try:
        if not message.text:
            await message.answer("❌ Введите причину")
            return
            
        data = await state.get_data()
        await state.clear()
        
        Database.block_user(
            user_id=data['user_id'],
            admin_id=message.from_user.id,
            reason=message.text
        )
        
        # Notify user
        user = Database.get_user_by_id(data['user_id'])
        if user:
            try:
                await bot.send_message(
                    chat_id=user['telegram_id'],
                    text=f"❌ Вы были заблокированы!\nПричина: {message.text}"
                )
            except Exception as e:
                logger.error(f"Failed to notify user: {e}")
        
        await message.answer(
            "✅ Пользователь заблокирован",
            reply_markup=get_admin_keyboard()
        )
    except Exception as e:
        logger.error(f"Error in process_block_reason: {e}")
        await message.answer("❌ Ошибка блокировки")

@router.callback_query(F.data.startswith("unblock_user:"))
async def unblock_user(callback: CallbackQuery, state: FSMContext):
    """Initiate user unblocking"""
    try:
        user_id = int(callback.data.split(":")[1])
        await state.set_state(UserManagement.waiting_for_unblock_reason)
        await state.update_data(user_id=user_id)
        await callback.message.answer(
            "✏️ Введите причину разблокировки:",
            reply_markup=get_cancel_keyboard()
        )
    except Exception as e:
        logger.error(f"Error in unblock_user: {e}")
        await callback.answer("❌ Ошибка разблокировки")

@router.message(UserManagement.waiting_for_unblock_reason)
async def process_unblock_reason(message: Message, state: FSMContext, bot: Bot):
    """Process user unblocking"""
    try:
        if not message.text:
            await message.answer("❌ Введите причину")
            return
            
        data = await state.get_data()
        await state.clear()
        
        Database.unblock_user(
            user_id=data['user_id'],
            admin_id=message.from_user.id,
            reason=message.text
        )
        
        # Notify user
        user = Database.get_user_by_id(data['user_id'])
        if user:
            try:
                await bot.send_message(
                    chat_id=user['telegram_id'],
                    text=f"✅ Вы были разблокированы!\nПричина: {message.text}"
                )
            except Exception as e:
                logger.error(f"Failed to notify user: {e}")
        
        await message.answer(
            "✅ Пользователь разблокирован",
            reply_markup=get_admin_keyboard()
        )
    except Exception as e:
        logger.error(f"Error in process_unblock_reason: {e}")
        await message.answer("❌ Ошибка разблокировки")

# ======================
# POST MODERATION
# ======================

@router.message(F.text == "📝 Нерассмотренные посты")
async def show_pending_posts(message: Message, bot: Bot):
    """Show all pending posts with moderation buttons"""
    try:
        posts = Database.get_posts_by_status('pending')
        if not posts:
            await message.answer("ℹ️ Нет постов, ожидающих модерации.")
            return
        user = Database.get_user(message.from_user.id)
        if not user or user['role'] != 'admin':
            await message.answer("❌ У вас нет доступа к командам администрации")
            return
        for post in posts:
            caption = (
                f"🆔 ID поста: {post['post_id']}\n"
                f"👤 Автор: @{post['username']} (ID: {post['telegram_id']})\n"
                f"📅 Дата: {format_datetime(post['created_at'])}\n"
                f"📝 Текст: {post['text_content'] or 'отсутствует'}"
            )

            if post['image_file_id']:
                await bot.send_photo(
                    chat_id=message.chat.id,
                    photo=post['image_file_id'],
                    caption=caption,
                    reply_markup=get_post_actions_keyboard(post['post_id'])
                )
            else:
                await message.answer(
                    caption,
                    reply_markup=get_post_actions_keyboard(post['post_id'])
                )
    except Exception as e:
        logger.error(f"Error showing pending posts: {e}")
        await message.answer("❌ Ошибка при загрузке постов.")

@router.message(F.text == "✅ Одобренные посты")
async def show_approved_posts(message: Message):
    """Show approved posts"""
    user = Database.get_user(message.from_user.id)
    if not user or user['role'] != 'admin':
        await message.answer("❌ У вас нет доступа к командам администрации", reply_markup=get_main_keyboard())
        return
    await show_posts_by_status(message, 'approved')
    await message.answer("\nВведите <b>/post ID</b> для просмотра (например: /post 1)", reply_markup=get_admin_keyboard())  # Возвращаем клавиатуру

@router.message(F.text == "❌ Отклоненные посты")
async def show_rejected_posts(message: Message):
    """Show rejected posts"""
    user = Database.get_user(message.from_user.id)
    if not user or user['role'] != 'admin':
        await message.answer("❌ У вас нет доступа к командам администрации", reply_markup=get_main_keyboard())
        return
    await show_posts_by_status(message, 'rejected')
    await message.answer("\nВведите <b>/post ID</b> для просмотра (например: /post 1)", reply_markup=get_admin_keyboard())  # Возвращаем клавиатуру

async def show_posts_by_status(message: Message, status: str):
    try:
        posts = Database.get_posts_by_status(status)
        if not posts:
            await message.answer(f"ℹ️ Нет постов со статусом '{status}'")
            return
            
        response = f"📋 <b>Посты ({status}):</b>\n\n"
        for post in posts:
            response += (
                f"🆔 <b>post_{post['post_id']}</b>\n"
                f"👤 @{post['username'] or 'нет'}\n"
                f"📅 {format_datetime(post['created_at'])}\n"
                f"────────────────────\n"
            )
        
        await message.answer(
            response,
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )
    except Exception as e:
        logger.error(f"Error showing {status} posts: {e}")
        await message.answer("❌ Ошибка при загрузке постов")

@router.callback_query(F.data.startswith("approve_post:"))
async def approve_post(callback: CallbackQuery, bot: Bot):
    """Handle post approval"""
    try:
        post_id = int(callback.data.split(":")[1])
        Database.update_post_status(
            post_id=post_id,
            status='approved',
            admin_id=callback.from_user.id
        )

        # Notify user
        post = Database.get_post(post_id)
        if post:
            await notify_post_status(
                user_id=post['user_id'],
                post_id=post_id,
                status='approved',
                bot=bot
            )

        await callback.answer("✅ Пост одобрен!")

        # Проверяем, есть ли message в callback
        if callback.message:
            await callback.message.edit_reply_markup(reply_markup=None)
        else:
            logger.warning("callback.message is None")
    except Exception as e:
        logger.error(f"Error approving post: {e}")
        await callback.answer("❌ Ошибка при одобрении поста")


@router.callback_query(F.data.startswith("reject_post:"))
async def reject_post(callback: CallbackQuery, state: FSMContext):
    """Initiate post rejection process"""
    post_id = int(callback.data.split(":")[1])
    await state.set_state(UserManagement.waiting_for_rejection_reason)
    await state.update_data(post_id=post_id)
    await callback.message.answer(
        "✏️ Укажите причину отклонения поста:",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.message(UserManagement.waiting_for_rejection_reason)
async def complete_reject_post(message: Message, state: FSMContext, bot: Bot):
    """Complete post rejection with reason"""
    try:
        data = await state.get_data()
        await state.clear()
        
        Database.update_post_status(
            post_id=data['post_id'],
            status='rejected',
            admin_id=message.from_user.id,
            rejection_reason=message.text
        )
        
        # Notify user
        post = Database.get_post(data['post_id'])
        if post:
            await notify_post_status(
                user_id=post['user_id'],
                post_id=data['post_id'],
                status='rejected',
                bot=bot,
                reason=message.text
            )
        
        await message.answer(
            "✅ Пост отклонен! Пользователь уведомлен.",
            reply_markup=get_admin_keyboard()
        )
    except Exception as e:
        logger.error(f"Error rejecting post: {e}")
        await message.answer("❌ Ошибка при отклонении поста")
        
@router.message(UserManagement.waiting_for_rejection_reason)
async def process_rejection(message: Message, state: FSMContext, bot: Bot):
    """Complete post rejection with reason"""
    try:
        data = await state.get_data()
        await state.clear()
        
        post_id = data['post_id']
        Database.update_post_status(
            post_id=post_id,
            status='rejected',
            admin_id=message.from_user.id,
            rejection_reason=message.text
        )
        
        # Notify user
        post = Database.get_post(post_id)
        if post:
            await notify_post_status(
                user_id=post['user_id'],
                post_id=post_id,
                status='rejected',
                bot=bot,
                reason=message.text
            )
        
        await message.answer(
            "✅ Пост отклонен! Пользователь уведомлен.",
            reply_markup=get_admin_keyboard()
        )
    except Exception as e:
        logger.error(f"Error rejecting post: {e}")
        await message.answer("❌ Ошибка при отклонении поста")

# Notification Utility
async def notify_post_status(user_id: int, post_id: int, status: str, bot: Bot, reason: str = None):
    """Notify user about their post status change"""
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
            f"ℹ️ *Статус вашего поста изменен*\n\n"
            f"🆔 ID: {post_id}\n"
            f"📅 Дата: {post['created_at']}\n"
            f"🔹 Новый статус: {status_text}\n"
        )

        if post['reviewed_by']:
            admin = Database.get_user(post['reviewed_by'])
            if admin:
                message += f"👨‍💻 Модератор: @{admin['username']}\n"

        if status == 'rejected':
            message += f"📝 Причина: {reason or post.get('rejection_reason', 'не указана')}\n"

        await bot.send_message(
            chat_id=user['telegram_id'],
            text=message,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Failed to notify user about post status: {e}")

# ======================
# FEEDBACK MANAGEMENT
# ======================

@router.message(F.text == "📩 Обратная связь")
async def show_pending_feedback(message: Message):
    """Show pending feedback"""
    try:
        user = Database.get_user(message.from_user.id)
        if not user or user['role'] != 'admin':
            await message.answer("❌ У вас нет доступа к командам администрации")
            return
    
        feedback_list = Database.get_pending_feedback()
        if not feedback_list:
            await message.answer("ℹ️ Нет новых сообщений")
            return
        
        for feedback in feedback_list:
            response = (
                f"📩 Сообщение #{feedback['feedback_id']}\n\n"
                f"👤 От: @{feedback['username']}\n"
                f"📅 Дата: {format_datetime(feedback['created_at'])}\n\n"
                f"📝 Текст:\n{feedback['message']}"
            )
            
            await message.answer(
                response,
                reply_markup=get_feedback_response_keyboard(feedback['feedback_id'])
            )
    except Exception as e:
        logger.error(f"Error in show_pending_feedback: {e}")
        await message.answer("❌ Ошибка загрузки сообщений")

@router.callback_query(F.data.startswith("respond_feedback:"))
async def respond_to_feedback(callback: CallbackQuery, state: FSMContext):
    """Initiate feedback response"""
    try:
        feedback_id = int(callback.data.split(":")[1])
        await state.set_state(Feedback.waiting_for_response)
        await state.update_data(feedback_id=feedback_id)
        await callback.message.answer(
            "✏️ Введите ответ пользователю:",
            reply_markup=get_cancel_keyboard()
        )
    except Exception as e:
        logger.error(f"Error in respond_to_feedback: {e}")
        await callback.answer("❌ Ошибка ответа")

@router.message(Feedback.waiting_for_response)
async def process_feedback_response(message: Message, state: FSMContext, bot: Bot):
    """Process feedback response"""
    try:
        if not message.text:
            await message.answer("❌ Введите текст ответа")
            return
            
        data = await state.get_data()
        await state.clear()
        
        feedback_id = data['feedback_id']
        Database.respond_to_feedback(
            feedback_id=feedback_id,
            admin_id=message.from_user.id,
            response=message.text
        )
        
        # Notify user
        await notify_user_about_feedback(feedback_id, message.text, bot)
        
        await message.answer(
            "✅ Ответ отправлен пользователю",
            reply_markup=get_admin_keyboard()
        )
    except Exception as e:
        logger.error(f"Error in process_feedback_response: {e}")
        await message.answer("❌ Ошибка отправки ответа")

# ======================
# NOTIFICATION FUNCTIONS
# ======================

async def notify_user_about_post(post_id: int, status: str, bot: Bot):
    """Notify user about post status change"""
    try:
        post = Database.get_post(post_id)
        if not post:
            return
            
        user = Database.get_user_by_id(post['user_id'])
        if not user:
            return
            
        status_text = {
            'approved': 'одобрен ✅',
            'rejected': 'отклонен ❌'
        }.get(status, status)
        
        message = (
            f"ℹ️ Статус вашего поста изменен:\n\n"
            f"🆔 ID: {post_id}\n"
            f"📅 Дата: {format_datetime(post['created_at'])}\n"
            f"🔹 Статус: {status_text}\n"
        )
        
        if post['reviewed_by']:
            admin = Database.get_user(post['reviewed_by'])
            if admin:
                message += f"👨‍💻 Администратор: @{admin['username']}\n"
        
        await bot.send_message(
            chat_id=user['telegram_id'],
            text=message
        )
    except Exception as e:
        logger.error(f"Failed to notify user about post: {e}")

async def notify_user_about_feedback(feedback_id: int, response: str, bot: Bot):
    """Notify user about feedback response"""
    try:
        feedback = Database.get_feedback(feedback_id)
        if not feedback:
            return
            
        await bot.send_message(
            chat_id=feedback['telegram_id'],
            text=f"📩 Ответ от администрации:\n\n{response}"
        )
    except Exception as e:
        logger.error(f"Failed to notify user about feedback: {e}")

async def notify_post_status(user_id: int, post_id: int, status: str, bot: Bot, reason: str = None):
    """Notify user about their post status"""
    try:
        user = Database.get_user_by_id(user_id)
        if not user:
            return
            
        status_text = {
            'approved': 'одобрен ✅',
            'rejected': 'отклонен ❌'
        }.get(status, status)

        message = (
            f"ℹ️ Статус вашего поста #{post_id} изменен:\n"
            f"🔹 Новый статус: {status_text}\n"
        )
        
        if status == 'rejected' and reason:
            message += f"📝 Причина: {reason}\n"
        
        await bot.send_message(
            chat_id=user['telegram_id'],
            text=message
        )
    except Exception as e:
        logger.error(f"Failed to notify user {user_id}: {e}")


@router.message(F.text == "📢 Массовая рассылка")
async def start_mass_notification(message: Message, state: FSMContext):
    user = Database.get_user(message.from_user.id)
    if not user or user['role'] != 'admin':
        await message.answer("❌ У вас нет доступа к этой команде.")
        return
    
    await state.set_state(MassNotification.waiting_for_content)
    await message.answer(
        "✍️ Отправьте текст сообщения\n\n"
        "Используйте кнопку '❌ Отмена' для выхода",
        reply_markup=get_cancel_Notify_keyboard()
    )

@router.message(MassNotification.waiting_for_content)
async def process_notification_content(message: Message, state: FSMContext):
    if not message.text and not message.photo:
        await message.answer("❌ Сообщение должно содержать текст")
        return
    
    content = {
        'text': message.text if message.text else None,
        'image': message.photo[-1].file_id if message.photo else None
    }
    
    await state.update_data(content=content)
    await state.set_state(MassNotification.confirm_sending)
    
    # Create preview
    preview_text = "📢 Предпросмотр рассылки:\n\n"
    if content['text']:
        preview_text += f"📝 Текст:\n{content['text']}\n\n"
    if content['image']:
        preview_text += "🖼 Приложено изображение\n"
    
    preview_text += "\nОтправить всем пользователям?"
    
    if content['image']:
        await message.answer_photo(
            content['image'],
            caption=preview_text,
            reply_markup=get_mass_notification_keyboard()
        )
    else:
        await message.answer(
            preview_text,
            reply_markup=get_mass_notification_keyboard()
        )

@router.message(MassNotification.confirm_sending, F.text == "✅ Да, отправить")
async def confirm_mass_notification(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.clear()
    
    users = Database.get_all_users()
    total_users = len(users)
    success_count = 0
    fail_count = 0
    
    await message.answer(f"⏳ Начинаю рассылку для {total_users} пользователей...")
    
    for user in users:
        try:
            # Prefix text with "Массовая рассылка от администрации"
            message_text = f"🚨📢 Массовая рассылка от администрации:\n\n{data['content']['text']}" if data['content']['text'] else "Массовая рассылка от администрации"
            
            # Check if image exists and send accordingly
            if data['content']['image']:
                await bot.send_photo(
                    chat_id=user['telegram_id'],
                    photo=data['content']['image'],
                    caption=message_text
                )
            else:
                await bot.send_message(
                    chat_id=user['telegram_id'],
                    text=message_text
                )
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to send to {user['telegram_id']}: {e}")
            fail_count += 1
            continue
    
    # Send statistics
    stats_message = (
        "📊 Статистика рассылки:\n\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"✅ Успешно отправлено: {success_count}\n"
        f"❌ Не удалось отправить: {fail_count}\n"
        f"📈 Процент доставки: {round((success_count/total_users)*100 if total_users > 0 else 0)}%"
    )
    
    await message.answer(
        stats_message,
        reply_markup=get_admin_keyboard()
    )

@router.message(MassNotification.confirm_sending, F.text == "❌ Нет, отменить")
async def cancel_mass_notification(message: Message, state: FSMContext):
    user = Database.get_user(message.from_user.id)
    if not user or user['role'] != 'admin':
        await message.answer("❌ У вас нет доступа к этой команде.")
        return
    await state.clear()
    await message.answer(
        "❌ Рассылка отменена",
        reply_markup=get_admin_keyboard()
    )
