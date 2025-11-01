# database.py - добавляем разделы
from pymongo import MongoClient
import config


def fill_database():
    """Заполняет базу данных вопросами и рекомендациями по двум разделам"""
    client = MongoClient(config.MONGO_URI)
    db = client.family_bot
    
    # Очищаем коллекции
    db.questions.delete_many({})
    db.recommendations.delete_many({})
    # Разделы опросника
    sections = [
        {
            "section_id": "communication",
            "name": "💬 Общение и понимание",
            "description": "Качество общения, эмпатия, разрешение конфликтов"
        },
        {
            "section_id": "intimacy", 
            "name": "💕 Близость и интимность",
            "description": "Эмоциональная и физическая близость, доверие"
        }
    ]
    
    # Вопросы для раздела "Общение и понимание"
    communication_questions = [
        {
            "question_id": "comm_understanding",
            "section": "communication",
            "question": "💬 Насколько хорошо вы понимаете чувства друг друга?",
            "options": [
                {"text": "Полностью понимаем", "value": "full_understanding", "score": 5},
                {"text": "В основном понимаем", "value": "good_understanding", "score": 4},
                {"text": "Иногда недопонимаем", "value": "sometimes_misunderstand", "score": 3},
                {"text": "Часто не понимаем", "value": "often_misunderstand", "score": 2},
                {"text": "Почти не понимаем", "value": "rarely_understand", "score": 1}
            ],
            "order": 1
        },
        {
            "question_id": "comm_conflicts",
            "section": "communication", 
            "question": "⚡ Как вы решаете конфликты?",
            "options": [
                {"text": "Обсуждаем спокойно и находим решение", "value": "calm_resolution", "score": 5},
                {"text": "Спорим, но приходим к согласию", "value": "argue_but_agree", "score": 4},
                {"text": "Часто спорим без результата", "value": "argue_no_result", "score": 3},
                {"text": "Избегаем конфликтов", "value": "avoid_conflicts", "score": 2},
                {"text": "Конфликты переходят в ссоры", "value": "conflicts_fight", "score": 1}
            ],
            "order": 2
        },
        # ... еще 8 вопросов для раздела общения
    ]
    
    # Вопросы для раздела "Близость и интимность"  
    intimacy_questions = [
        {
            "question_id": "intimacy_emotional",
            "section": "intimacy",
            "question": "💖 Как часто вы делитесь сокровенными мыслями?",
            "options": [
                {"text": "Ежедневно", "value": "daily_sharing", "score": 5},
                {"text": "Несколько раз в неделю", "value": "weekly_sharing", "score": 4},
                {"text": "Раз в неделю", "value": "once_week", "score": 3},
                {"text": "Раз в месяц", "value": "once_month", "score": 2},
                {"text": "Почти никогда", "value": "rarely_share", "score": 1}
            ],
            "order": 1
        },
        {
            "question_id": "intimacy_physical",
            "section": "intimacy",
            "question": "🔥 Устраивает ли вас интимная жизнь?",
            "options": [
                {"text": "Полностью устраивает", "value": "fully_satisfied", "score": 5},
                {"text": "В основном устраивает", "value": "mostly_satisfied", "score": 4},
                {"text": "Иногда не устраивает", "value": "sometimes_unsatisfied", "score": 3},
                {"text": "Часто не устраивает", "value": "often_unsatisfied", "score": 2},
                {"text": "Совсем не устраивает", "value": "completely_unsatisfied", "score": 1}
            ],
            "order": 2
        },
        # ... еще 8 вопросов для раздела близости
    ]
    
    # Рекомендации по разделам
    communication_recommendations = [
        {
            "title": "Активное слушание",
            "description": "Техники настоящего понимания партнера",
            "content": "Учитесь слушать не только слова, но и эмоции...",
            "category": "💬 Общение",
            "section": "communication",
            "priority": 9
        },
        # ... 9 других рекомендаций по общению
    ]
    
    intimacy_recommendations = [
        {
            "title": "Эмоциональная близость", 
            "description": "Как создавать глубокую эмоциональную связь",
            "content": "Практики для укрепления доверия и открытости...",
            "category": "💕 Близость",
            "section": "intimacy", 
            "priority": 8
        },
        # ... 9 других рекомендаций по близости
    ]
    db.questions.insert_many(intimacy_questions)
    db.questions.insert_many(communication_questions)
    db.recommendations.insert_many(communication_recommendations)
    db.recommendations.insert_many(intimacy_recommendations)
    
    print(f"✅ Добавлено {len(intimacy_questions)} вопросов")
    print(f"✅ Добавлено {len(intimacy_recommendations)} рекомендаций")
    print("🎉 База данных заполнена!")

if __name__ == "__main__":
    fill_database()