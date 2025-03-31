from aiogram.fsm.state import StatesGroup, State

class PostCreation(StatesGroup):
    """
    States for post creation process:
    - waiting_for_text: Bot is waiting for post text (optional)
    - waiting_for_image: Bot is waiting for post image (required)
    """
    waiting_for_text = State()
    waiting_for_image = State()

class Feedback(StatesGroup):
    """
    States for feedback process:
    - waiting_for_message: Bot is waiting for user's feedback message
    - waiting_for_response: Admin is preparing response to feedback
    """
    waiting_for_message = State()
    waiting_for_response = State()

class UserManagement(StatesGroup):
    """
    States for user management by admins:
    - waiting_for_block_reason: Admin needs to provide block reason
    - waiting_for_unblock_reason: Admin needs to provide unblock reason
    - waiting_for_user_id: Admin needs to provide user ID for actions
    - waiting_for_rejection_reason: Admin needs to provide rejection reason
    """
    waiting_for_rejection_reason = State()
    waiting_for_block_reason = State()
    waiting_for_unblock_reason = State()
    waiting_for_user_id = State()

class PostModeration(StatesGroup):
    """
    States for post moderation process:
    - waiting_for_rejection_reason: Admin needs to provide rejection reason
    - viewing_post_details: Admin is viewing specific post details
    """
    waiting_for_rejection_reason = State()
    viewing_post_details = State()

class StatisticsView(StatesGroup):
    """
    States for statistics viewing:
    - viewing_top_users: User is viewing top users statistics
    """
    viewing_top_users = State()


class PostReview(StatesGroup):
    """
    States for post review process:
    - waiting_for_rejection_reason: Admin needs to provide rejection reason
    - waiting_for_approval_confirmation: Admin is confirming post approval
    """
    waiting_for_rejection_reason = State()
    waiting_for_approval_confirmation = State()

class MassNotification(StatesGroup):
    waiting_for_message = State()
    confirm_sending = State()
    waiting_for_content = State()