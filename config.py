import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017//telegram_222')
YOOKASSA_SHOP_ID = os.getenv('YOOKASSA_SHOP_ID')
YOOKASSA_SECRET_KEY = os.getenv('YOOKASSA_SECRET_KEY')
BOT_USERNAME= "ykassa11102025_bot"

# Настройки подписки
SUBSCRIPTION_DAYS = 1
SUBSCRIPTION_PRICE = 10.0  # рублей
SUBSCRIPTION_DURATION=SUBSCRIPTION_DAYS 
DATABASE_NAME="family_bot"

SECTIONS_CONFIG = {
    'communication': {
        'name': '💬 Общение',
        'description': 'Эффективная коммуникация в отношениях',
        'priority': 1,
        'questions_count': 10,
        'icon': '💬'
    },
    'intimacy': {
        'name': '💕 Близость', 
        'description': 'Эмоциональная и физическая близость',
        'priority': 2,
        'questions_count': 8,
        'icon': '💕'
    },
    'conflict': {
        'name': '⚡ Решение конфликтов',
        'description': 'Конструктивное разрешение разногласий',
        'priority': 3,
        'questions_count': 8,
        'icon': '⚡'
    },
    'trust': {
        'name': '🤝 Доверие',
        'description': 'Построение и поддержание доверия',
        'priority': 4,
        'questions_count': 7,
        'icon': '🤝'
    },
    'goals': {
        'name': '🎯 Общие цели',
        'description': 'Совместное планирование и цели',
        'priority': 5,
        'questions_count': 6,
        'icon': '🎯'
    },
    'finance': {
        'name': '💰 Финансы',
        'description': 'Финансовые вопросы в отношениях',
        'priority': 7,
        'questions_count': 7,
        'icon': '💰'
    },
    'family': {
        'name': '👨‍👩‍👧‍👦 Семейные вопросы',
        'description': 'Отношения с родственниками и детьми',
        'priority': 8,
        'questions_count': 8,
        'icon': '👨‍👩‍👧‍👦'
    }
}