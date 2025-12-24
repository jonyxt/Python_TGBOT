import random

from faker import Faker
from telebot import types
from telebot.handler_backends import State, StatesGroup
from telebot.types import CallbackQuery

from db_modules import get_user_by_id, get_study_word
from bot_connect import bot


class States(StatesGroup):
    """Состояния бота для управления процессом регистрации и обучения."""
    wait_name = State()
    wait_rename = State()
    learning = State()
    add_value = State()
    add_translation = State()

class Commands:
    """Текст команд, отображаемых на кнопках inline-клавиатуры."""
    ADD_WORD: str = 'Добавить слово'
    DELETE_WORD: str = 'Удалить слово'
    NEXT: str = 'Дальше'

def require_registration(func):
    """
    Декоратор, проверяющий регистрацию пользователя перед выполнением функции.
    Если пользователь не зарегистрирован — отправляет сообщение с кнопкой регистрации.
    """
    def wrapper(message, *args, **kwargs):
        user = get_user_by_id(message.from_user.id)
        if not user:
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(types.InlineKeyboardButton(text='Регистрация',
                                                  callback_data='reg_call'))
            bot.send_message(message.chat.id,
                             'Вы не зарегистрированы. Пройдите регистрацию.',
                             reply_markup=markup)
            return None
        return func(message, *args, **kwargs)
    return wrapper

def registration(user_id: int, chat_id: int) -> None:
    """
    Начало регистрации пользователя.

    Устанавливает состояние ожидания имени и отправляет сообщение.

    Args:
        user_id (int): Telegram ID пользователя.
        chat_id (int): ID чата, куда отправлять сообщения.
    """
    if get_user_by_id(user_id):
        bot.send_message(chat_id, 'Вы уже зарегистрированы')
        return
    bot.set_state(user_id, States.wait_name, chat_id)
    bot.send_message(chat_id, 'Введите ваше имя')

def study(user_id: int, chat_id: int) -> None:
    """
    Начало или продолжение учебы пользователя.

    Показывает слово на изучение и варианты перевода, включая случайные "фейковые" переводы.
    Добавляет кнопки управления: Дальше, Добавить слово, Удалить слово.

    Args:
        user_id (int): Telegram ID пользователя.
        chat_id (int): ID чата, куда отправлять сообщение.
    """
    word, translation, word_id = get_study_word(user_id)
    if not word or not translation:
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton(text='Добавить слово',
                                              callback_data='add_word_call'))
        bot.send_message(chat_id, f'Нет слов для изучения',
                         reply_markup=markup)
        return
    buttons = []
    fake_translation = [str(item) for item in fake.words(nb=3)]
    buttons.append(types.InlineKeyboardButton(text=translation, callback_data=f'answer_{word_id}_correct'))
    for i, fake_t in enumerate(fake_translation):
        buttons.append(types.InlineKeyboardButton(text=fake_t,
                                                  callback_data=f'answer_{word_id}_fake{i}'))
    random.shuffle(buttons)
    buttons.extend([
        types.InlineKeyboardButton(text=Commands.NEXT, callback_data='next_call'),
        types.InlineKeyboardButton(text=Commands.ADD_WORD, callback_data='add_word_call'),
        types.InlineKeyboardButton(text=Commands.DELETE_WORD, callback_data='delete_word_call')
    ])
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(*buttons)
    bot.send_message(chat_id, f'Какой перевод у слова {word}?',
                     reply_markup=markup)
    bot.set_state(user_id, States.learning, chat_id)
    with bot.retrieve_data(user_id, chat_id) as data:
            data['word_id'] = word_id

def clear_inline_keyboard(call: CallbackQuery) -> None:
    """
    Убирает inline-клавиатуру у сообщения.

    Args:
        call (CallbackQuery): Объект callback запроса от Telegram.
    """
    bot.answer_callback_query(call.id)
    bot.edit_message_reply_markup(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=None
    )

fake = Faker()

HELP_TEXT: str = (
        "<b>Справка по боту</b>\n\n"
        "/start - Начать работу с ботом, приветствие\n"
        "/help - Показать эту справку\n"
        "/register - Зарегистрироваться в боте\n"
        "/id - Узнать ваш Telegram ID и имя\n"
        "/change_name - Изменить имя пользователя\n"
        "/study - Начать учебу: бот покажет слово и варианты перевода\n\n"
        "Во время учебы доступны кнопки:\n"
        f"  • {Commands.NEXT} - Пропустить слово и перейти к следующему\n"
        f"  • {Commands.ADD_WORD} - Добавить новое слово в словарь\n"
        f"  • {Commands.DELETE_WORD} - Удалить текущее слово из словаря"
    )