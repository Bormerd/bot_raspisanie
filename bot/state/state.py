"""модуль для машинных состояние"""
from aiogram.fsm.state import State, StatesGroup

class User(StatesGroup):
    """Название машинных состояний"""
    role=State()
    reg_end=State()
    group_add=State()
    discipline=State()