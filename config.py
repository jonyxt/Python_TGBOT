import os
from dotenv import load_dotenv
import sqlalchemy as sq
from sqlalchemy.orm import sessionmaker
from models import create_tables

load_dotenv()

# Загружаем переменные окружения
DB_DRIVER = os.getenv('DB_DRIVER')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_LOGIN = os.getenv('DB_LOGIN')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_TABLE_NAME')
BOT_TOKEN = os.getenv('BOT_TOKEN')

if not all([DB_DRIVER, DB_HOST, DB_PORT, DB_LOGIN, DB_PASSWORD, DB_NAME, BOT_TOKEN]):
    raise ValueError("Не все переменные окружения заданы!")

# Формируем строку подключения к базе данных
DSN = f'{DB_DRIVER}://{DB_LOGIN}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

# Создаем SQLAlchemy engine
engine = sq.create_engine(DSN)

# Создаем таблицы в базе данных, если их нет
create_tables(engine)

# Создаем фабрику сессий
Session = sessionmaker(bind=engine)
