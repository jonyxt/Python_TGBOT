from datetime import datetime
from typing import Tuple

from models import User, Words, Users_words
from config import Session


def add_base_words(path: str) -> None:
    """
    Загружает базовые слова из JSON-файла и добавляет их в таблицу Words.
    Если базовые слова уже есть, ничего не делает.

    Args:
        path (str): Путь к JSON-файлу с базовыми словами.
    """
    with Session() as session:
        if session.query(Words).filter_by(base_word=True).first():
            return
        import json
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                word = Words(value=item['word'],
                             translation=item['translation'],
                             base_word=True)
                session.add(word)
            session.commit()

def create_user(tg_id: int, username: str) -> bool:
    """
    Создаёт нового пользователя и добавляет ему все базовые слова.

    Args:
        tg_id (int): Telegram ID пользователя.
        username (str): Имя пользователя.

    Returns:
        bool: True если пользователь создан, False если уже существует.
    """
    with Session() as session:
        if session.query(User).filter_by(tg_id=tg_id).first():
            return False
        user = User(tg_id=tg_id, username=username)
        session.add(user)
        session.commit()
        words = session.query(Words).filter_by(base_word=True).all()
        for word in words:
            user_word = Users_words(user_id=user.id, word_id=word.id)
            session.add(user_word)
        session.commit()
        return True

def rename_user(tg_id: int, username: str) -> bool:
    """
   Изменяет имя пользователя.

   Args:
       tg_id (int): Telegram ID пользователя.
       username (str): Новое имя пользователя.

   Returns:
       bool: Всегда True (успешно изменено).
   """
    with Session() as session:
        user = session.query(User).filter_by(tg_id=tg_id).first()
        user.username = username
        session.commit()
        return True

def add_word(tg_id: int, value: str, translation: str) -> bool:
    """
    Добавляет новое слово пользователю. Если слово уже есть, добавляет связь с пользователем.

    Args:
        tg_id (int): Telegram ID пользователя.
        value (str): Слово на русском.
        translation (str): Перевод на английский.

    Returns:
        bool: True если слово добавлено или уже есть, False если пользователь не найден.
    """
    with Session() as session:
        user = session.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            return False
        word = session.query(Words).filter_by(value=value,
                                              translation=translation).first()
        if word:
            user_word = session.query(Users_words).filter_by(user_id=user.id, word_id=word.id).first()
            if user_word:
                return True
            session.add(Users_words(user_id=user.id, word_id=word.id))
            session.commit()
            return True
        else:
            word = Words(value=value, translation=translation, base_word=False)
            session.add(word)
            session.flush()
            session.add(Users_words(user_id=user.id, word_id=word.id))
            session.commit()
            return True

def delete_word(tg_id: int, word_id: int) -> bool:
    """
    Удаляет слово из словаря пользователя. Если слово не используется другими
    пользователями и не является базовым, удаляет его полностью.

    Args:
        tg_id (int): Telegram ID пользователя.
        word_id (int): ID слова.

    Returns:
        bool: True если слово удалено или не найдено у пользователя, False если пользователь не найден.
    """
    with Session() as session:
        user = session.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            return False
        user_word = (session.query(Users_words).join(Words)
                     .filter(Words.id == word_id).first())
        if not user_word:
            return False
        session.delete(user_word)
        check = session.query(Users_words).filter_by(word_id=word_id).count()
        word = session.query(Words).filter_by(id=word_id).first()
        if word and not word.base_word and check==0:
            session.delete(word)
        return True

def get_study_word(tg_id: int) -> Tuple:
    """
    Возвращает слово для изучения пользователя (наиболее давно не показываемое).

    Args:
        tg_id (int): Telegram ID пользователя.

    Returns:
        Tuple:
            - слово на русском (str),
            - перевод (str),
            - ID слова (int)

    Если не найден пользователь, либо у него нет слов для изучения:
        Tuple:
            - None,
            - None,
            - None
    """
    with Session() as session:
        user = session.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            return None, None, None
        user_word = (
            session.query(Users_words).join(Words).filter(Users_words.user_id == user.id)
            .order_by(Users_words.last_shown.asc().nullsfirst()).first()
        )
        if not user_word:
            return None, None, None
        user_word.last_shown = datetime.utcnow()
        session.commit()
        return user_word.word.value, user_word.word.translation, user_word.word.id

def get_user_by_id(tg_id: int):
    """
    Возвращает объект пользователя по Telegram ID.

    Args:
        tg_id (int): Telegram ID пользователя.

    Returns:
        Объект User или None, если пользователь не найден.
    """
    with Session() as session:
        user = session.query(User).filter_by(tg_id=tg_id).first()
        return user

def get_word_by_id(word_id: int) -> tuple:
    """
    Возвращает слово и перевод по ID слова.

    Args:
        word_id (int): ID слова.

    Returns:
        Tuple[str, str]: слово и перевод, или (None, None), если не найдено.
    """
    with Session() as session:
        word = session.query(Words).filter_by(id=word_id).first()
        if not word:
            return None, None
        return word.value, word.translation
