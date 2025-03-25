from aiogram import Bot
from typing import Optional

class BotNotifier:
    _bot: Optional[Bot] = None

    @classmethod
    def set_bot(cls, bot: Bot):
        cls._bot = bot

    @classmethod
    async def send_message(cls, chat_id: int, text: str):
        if cls._bot:
            try:
                await cls._bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode="HTML"
                )
            except Exception as e:
                print(f"Ошибка при отправке уведомления {chat_id}: {e}")