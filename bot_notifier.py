from aiogram import Bot
from typing import Optional
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BotNotifier:
    _bot: Optional[Bot] = None

    @classmethod
    def set_bot(cls, bot: Bot):
        """Инициализация бота для уведомлений"""
        cls._bot = bot
        logger.info("BotNotifier: Бот успешно инициализирован")

    @classmethod
    async def send_message(cls, chat_id: int, text: str):
        """Отправка сообщения с улучшенным логированием"""
        if cls._bot is None:
            logger.error("BotNotifier: Бот не инициализирован!")
            return False

        try:
            logger.info(f"Попытка отправки сообщения для {chat_id}")
            await cls._bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="HTML"
            )
            logger.info(f"Сообщение успешно отправлено в чат {chat_id}")
            return True
        except Exception as e:
            logger.error(f"Ошибка отправки в чат {chat_id}: {str(e)}", exc_info=True)
            return False