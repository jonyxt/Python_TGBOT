from telebot import types
from telebot.types import Message, CallbackQuery

from bot_connect import bot
from bot_modules import (registration, require_registration, study,
                         States, HELP_TEXT, clear_inline_keyboard)
from db_modules import (add_base_words, create_user, add_word, delete_word,
                        get_user_by_id, rename_user, get_word_by_id)

# Загружаем базовые слова
add_base_words('base_words.json')

@bot.message_handler(commands=['start'])
def start_message(message: Message) -> None:
    """
    Обрабатывает команду /start.
    Приветствует пользователя и показывает меню в зависимости от регистрации.
    """
    user_id = message.from_user.id
    user = get_user_by_id(user_id)
    if user:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton(text='Сменить имя', callback_data='change_name_call'),
            types.InlineKeyboardButton(text='Справка по боту', callback_data='help_call'),
            types.InlineKeyboardButton(text='Начать обучение', callback_data='study_call')
        )
        bot.send_message(message.chat.id, f'С возвращением, {user.username}', reply_markup=markup)
    else:
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton(text = 'Регистрация', callback_data='reg_call'))
        bot.send_message(message.chat.id,
                         'Добро пожаловать! Для начала обучение, пройдите регистрацию.', reply_markup=markup)

@bot.message_handler(commands=['help'])
def help_message(message: Message) -> None:
    """
    Обрабатывает команду /help.
    Отправляет справочный текст.
    """
    bot.send_message(message.chat.id, HELP_TEXT, parse_mode='HTML',
                     reply_markup=types.ReplyKeyboardRemove())

@bot.callback_query_handler(func=lambda call: call.data == 'help_call')
def help_call(call: CallbackQuery) -> None:
    """
    Отправляет справку по боту при нажатии на inline кнопку.
    """
    clear_inline_keyboard(call)
    bot.send_message(call.message.chat.id, HELP_TEXT, parse_mode='HTML',
                     reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(commands=['register'])
def register_message(message: Message) -> None:
    """
    Обрабатывает команду /register.
    Запускает процесс регистрации.
    """
    registration(message.from_user.id, message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == 'reg_call')
def registration_call(call: CallbackQuery) -> None:
    """
    Запускает регистрацию при нажатии inline кнопки.
    """
    clear_inline_keyboard(call)
    registration(call.from_user.id, call.message.chat.id)

@bot.message_handler(state=States.wait_name)
def set_name(message: Message) -> None:
    """
    Обрабатывает ввод имени при регистрации.
    Создает пользователя и предлагает начать обучение.
    """
    user_id = message.from_user.id
    username = message.text
    result = create_user(user_id, username)
    if result:
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton(text='Обучение',
                                              callback_data='study_call'))
        bot.send_message(message.chat.id,
                         'Регистрация пройдена. Можете приступать к обучению.',
                         reply_markup=markup)
    else:
        bot.send_message(message.chat.id,
                         'Возникла ошибка, профиль не создан')
    bot.delete_state(message.from_user.id, message.chat.id)

@bot.message_handler(commands=['id'])
@require_registration
def get_message(message: Message) -> None:
    """
    Показывает ID Telegram и имя пользователя.
    """
    user_id = message.from_user.id
    user = get_user_by_id(user_id)
    username = user.username
    bot.send_message(message.chat.id, f'Ваш Телеграмм ID - {user_id}\n'
                                      f'Ваше имя - {username}')

@bot.message_handler(commands=['change_name'])
@require_registration
def change_name_message(message: Message) -> None:
    """
    Запрашивает новое имя пользователя.
    """
    bot.set_state(message.from_user.id, States.wait_rename, message.chat.id)
    bot.send_message(message.chat.id, 'Введите Ваше новое имя:')

@bot.callback_query_handler(func=lambda call: call.data == 'change_name_call')
def change_name_call(call: CallbackQuery) -> None:
    """
    Запрашивает новое имя через inline кнопку.
    """
    clear_inline_keyboard(call)
    bot.set_state(call.from_user.id, States.wait_rename, call.message.chat.id)
    bot.send_message(call.message.chat.id, 'Введите Ваше новое имя:')

@bot.message_handler(state=States.wait_rename)
def set_new_name(message: Message) -> None:
    """
    Обрабатывает ввод нового имени и обновляет его в базе.
    """
    user_id = message.from_user.id
    new_name = message.text
    rename_user(user_id, new_name)
    bot.delete_state(message.from_user.id, message.chat.id)
    bot.send_message(message.chat.id,
                     f'Ваше имя было заменено на "{new_name}"')
    start_message(message)

@bot.message_handler(commands=['study'])
@require_registration
def start_study(message: Message) -> None:
    """
    Запускает процесс обучения пользователя.
    """
    study(message.from_user.id, message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == 'study_call')
def start_study_call(call: CallbackQuery) -> None:
    """
    Запускает обучение при нажатии inline кнопки.
    """
    clear_inline_keyboard(call)
    study(call.from_user.id, call.message.chat.id)

@bot.callback_query_handler(func=lambda call:
call.data in ['next_call', 'add_word_call', 'delete_word_call'])
def control_buttons(call: CallbackQuery) -> None:
    """
    Обрабатывает кнопки управления в процессе обучения:
    - next_call: пропустить слово
    - add_word_call: добавить слово
    - delete_word_call: удалить слово
    """
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    clear_inline_keyboard(call)

    if call.data == 'next_call':
        bot.delete_state(user_id, chat_id)
        study(user_id, chat_id)
    if call.data == 'add_word_call':
        bot.set_state(user_id, States.add_value, chat_id)
        bot.send_message(call.message.chat.id, 'Введите слово на русском:')
    if call.data == 'delete_word_call':
        with bot.retrieve_data(user_id, chat_id) as data:
            word_id = data['word_id']
            delete_word(user_id, word_id)
            bot.send_message(call.message.chat.id,
                             f'Слово удалено из словаря')
            study(user_id, chat_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('answer_'))
def check_answer(call: CallbackQuery) -> None:
    """
    Проверяет ответ пользователя на слово.
    Отправляет сообщение о правильности ответа и продолжает обучение.
    """
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    parts = call.data.split('_')
    clear_inline_keyboard(call)
    if parts[2] == 'correct':
        bot.send_message(chat_id, 'Верный ответ')
    else:
        word, translation = get_word_by_id(int(parts[1]))
        bot.send_message(chat_id,
                         f'Неверный ответ. Правильный: {translation}')

    bot.delete_state(user_id, chat_id)
    study(user_id, chat_id)

@bot.message_handler(state=States.add_value)
def adding_value(message: Message) -> None:
    """
    Обрабатывает ввод нового слова на русском языке.
    """
    with bot.retrieve_data(message.from_user.id, message.chat.id) as new_word:
        new_word['word'] = message.text
    bot.set_state(message.from_user.id, States.add_translation, message.chat.id)
    bot.send_message(message.chat.id, 'Введите перевод слова на английский:')

@bot.message_handler(state=States.add_translation)
def adding_translation(message: Message) -> None:
    """
    Обрабатывает ввод перевода нового слова и добавляет его в словарь.
    """
    with bot.retrieve_data(message.from_user.id, message.chat.id) as new_word:
        new_word['translation'] = message.text
    user_id = message.from_user.id
    if add_word(user_id, new_word['word'], new_word['translation']):
        bot.send_message(message.chat.id, 'Слово добавлено')
    else:
        bot.send_message(message.chat.id, 'Слово не добавлено')
    bot.delete_state(message.from_user.id, message.chat.id)
    study(user_id, message.chat.id)

# Запуск бота
bot.infinity_polling()