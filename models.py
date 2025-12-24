import sqlalchemy as sq

from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Words(Base):
    """
    Модель слова в базе данных.

    Attributes:
        id (int): PK слова.
        value (str): Слово.
        translation (str): Перевод слова на изучаемый язык.
        base_word (bool): Флаг, является ли слово базовым.
        user_words: Связь с таблицей Users_words.
    """
    __tablename__ = 'word'

    id = sq.Column(sq.Integer, primary_key=True)
    value = sq.Column(sq.String(length=248), nullable=False)
    translation = sq.Column(sq.String(length=248), nullable=False)
    base_word = sq.Column(sq.Boolean, nullable=False)

    user_words = relationship('Users_words', back_populates='word')

class User(Base):
    """
    Модель пользователя в базе данных.

    Attributes:
        id (int): PK пользователя.
        tg_id (int): Telegram ID пользователя.
        username (Optional[str]): Имя пользователя.
        user_words: Связь с таблицей Users_words.
    """
    __tablename__ = 'user'

    id = sq.Column(sq.Integer, primary_key=True)
    tg_id = sq.Column(sq.BigInteger, unique=True, nullable=False)
    username = sq.Column(sq.String(length=248))

    user_words = relationship('Users_words', back_populates='user')

class Users_words(Base):
    """
    Связующая таблица пользователь-слово.

    Attributes:
        id (int): PK связи.
        user_id (int): FK на пользователя.
        word_id (int): FK на слово.
        last_shown (Optional[datetime]): Дата и время последнего показа слова пользователю.
        user: Связь с моделью User.
        word: Связь с моделью Words.
    """
    __tablename__ = 'users_words'

    id = sq.Column(sq.Integer, primary_key=True)
    user_id = sq.Column(sq.Integer, sq.ForeignKey('user.id'), nullable=False)
    word_id = sq.Column(sq.Integer, sq.ForeignKey('word.id'), nullable=False)
    last_shown = sq.Column(sq.DateTime, nullable=True, index=True)

    user = relationship(User, back_populates='user_words')
    word = relationship(Words, back_populates='user_words')

    __table_args__ = (
        UniqueConstraint('user_id', 'word_id', name='uix_user_word'),
    )

def create_tables(engine):
    """
    Создаёт все таблицы в базе данных.

    Args:
        engine (Engine): SQLAlchemy Engine для подключения к базе.
    """
    Base.metadata.create_all(engine)