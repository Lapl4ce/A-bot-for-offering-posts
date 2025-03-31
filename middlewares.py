from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable

from database import Database

class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user = Database.get_user(event.from_user.id)
        if user and user['status'] == 'blocked':
            await event.answer("Извините, вы были заблокированы в боте.")
            return
        
        return await handler(event, data)