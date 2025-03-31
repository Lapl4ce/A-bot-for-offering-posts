from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove  # Fixed import
)
from config import USER_ROLE_ADMIN
from aiogram.utils.keyboard import InlineKeyboardBuilder  # Add this import

# [Rest of your keyboard functions remain the same]
def get_main_keyboard(is_admin: bool = False):
    buttons = [
        [KeyboardButton(text="📤 Предложить пост")],
        [KeyboardButton(text="📨 Связь с администрацией")],
        [KeyboardButton(text="📜 История моих постов")],
        [KeyboardButton(text="📊 Статистика")]
    ]
    
    if is_admin:
        buttons.append([KeyboardButton(text="👨‍💻 Админ-панель")])
    
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )

def get_admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Пользователи")],
            [KeyboardButton(text="📝 Нерассмотренные посты")],
            [KeyboardButton(text="✅ Одобренные посты")],
            [KeyboardButton(text="❌ Отклоненные посты")],
            [KeyboardButton(text="📩 Обратная связь")],
            [KeyboardButton(text="📢 Массовая рассылка")],
            [KeyboardButton(text="🔙 Главное меню")]
        ],
        resize_keyboard=True
    )

def get_post_actions_keyboard(post_id: int):
    """Create moderation buttons for a post"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Одобрить",
            callback_data=f"approve_post:{post_id}"
        ),
        InlineKeyboardButton(
            text="❌ Отклонить",
            callback_data=f"reject_post:{post_id}"
        )
    )
    return builder.as_markup()
def get_user_profile_keyboard(user_id: int, is_blocked: bool):
    if is_blocked:
        buttons = [[InlineKeyboardButton(text="🔓 Разблокировать", callback_data=f"unblock_user:{user_id}")]]
    else:
        buttons = [[InlineKeyboardButton(text="🔒 Блокировать", callback_data=f"block_user:{user_id}")]]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_feedback_response_keyboard(feedback_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Ответить", callback_data=f"respond_feedback:{feedback_id}")]
    ])

def get_cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )
    
def get_cancelFeedback_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Назад")]],
        resize_keyboard=True
    )

def get_statistics_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏆 Топ по одобренным", callback_data="top_approved"),
            InlineKeyboardButton(text="💢 Топ по отклоненным", callback_data="top_rejected")
        ]
    ])

def get_mass_notification_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Да, отправить")],
            [KeyboardButton(text="❌ Нет, отменить")]
        ],
        resize_keyboard=True
    )

def get_cancel_Notify_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отменить")]],
        resize_keyboard=True
    )

