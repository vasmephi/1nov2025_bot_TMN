from pymongo import MongoClient
from datetime import datetime, timedelta
import config
from typing import List, Dict, Optional, Any

class Database:
    def __init__(self):
        self.client = MongoClient(config.MONGO_URI)
        self.db = self.client.family_bot
        self.users = self.db.users
        self.questions = self.db.questions
        self.recommendations = self.db.recommendations
        self.user_sections = self.db.user_sections
        self.user_recommendations = self.db.user_recommendations
        self.libido_content = self.db.libido_content
        self.books = self.db.books
        self.movies = self.db.movies
        self.activities = self.db.activities
        self.cinema=self.db.cinema
        self.literature=self.db.literature
        self.questions_new=self.db.questions_new
        print("🔍 Проверяем базу данных...")
        self.debug_database()
        self.init_collections()
        self.init_libido_content()
        self.recommendation_collections = ['activities', 'literature', 'cinema', 'questions_new']
    def debug_database(self):
        """Показывает содержимое базы данных для отладки"""
        print("📊 СОДЕРЖИМОЕ БАЗЫ ДАННЫХ:")
        users_count = self.users.count_documents({})
        questions_count = self.questions.count_documents({})
        recs_count = self.recommendations.count_documents({})
        libido_count = self.libido_content.count_documents({})
        sections_count = self.user_sections.count_documents({})
        
        print(f"👥 Пользователей: {users_count}")
        print(f"❓ Вопросов опросника: {questions_count}")
        print(f"🎯 Рекомендаций: {recs_count}")
        print(f"🌺 Контента либидо: {libido_count}")
        print(f"📋 Результатов разделов: {sections_count}")
        
        # Показываем доступные разделы
        available_sections = self.questions.distinct('section')
        print(f"📚 Разделы с вопросами: {available_sections}")
    
    def init_collections(self):
        """Инициализация коллекций и индексов"""
        collections = self.db.list_collection_names()
        
        # Создаем коллекцию user_sections если её нет
        if 'user_sections' not in collections:
            self.db.create_collection('user_sections')
            print("✅ Коллекция user_sections создана")
        
        # Создаем индексы для оптимизации
        self.user_sections.create_index([('user_id', 1), ('section', 1)], unique=True)
        self.user_sections.create_index([('user_id', 1)])
        self.questions.create_index([('section', 1), ('order', 1)])
        self.recommendations.create_index([('section', 1)])
        
        print("✅ Индексы базы данных созданы")
    
    def init_libido_content(self):
        """Инициализирует контент для раздела либидо"""
        if self.libido_content.count_documents({}) == 0:
            libido_data = [
                {
                    "title": "🌺 Упражнения Кегеля для женщин",
                    "content": """**Упражнения Кегеля для укрепления интимных мышц:**

1. **Найдите правильные мышцы** - остановите поток мочи во время мочеиспускания
2. **Напрягите мышцы** на 5 секунд, затем расслабьте на 5 секунд
3. **Повторяйте 10-15 раз** 3 раза в день
4. **Постепенно увеличивайте** время напряжения до 10 секунд

💡 *Эффект:* Улучшение ощущений, усиление оргазма, профилактика недержания""",
                    "category": "💪 Упражнения",
                    "order": 1
                },
                {
                    "title": "🌿 Натуральные способы повышения либидо",
                    "content": """**Природные методы усиления сексуального желания:**

🍎 **Питание:**
- Авокадо, орехи, темный шоколад
- Устрицы, гранаты, сельдерей
- Имбирь, корица, ваниль

🌱 **Травы:**
- Женьшень (повышает энергию)
- Мака перуанская (гормональный баланс)
- Трибулус (усиливает желание)

🏃‍♀️ **Физическая активность:**
- Йога и пилатес
- Кардио тренировки
- Танцы""",
                    "category": "🌱 Природные методы",
                    "order": 2
                },
                {
                    "title": "💖 Медитации для сексуальной энергии",
                    "content": """**Медитативные практики для пробуждения чувственности:**

1. **Дыхание животом** - 5 минут утром и вечером
2. **Визуализация энергии** - представьте теплую энергию в области таза
3. **Мантра любви** - повторяйте "Я открыта для любви и наслаждения"
4. **Телесное сканирование** - осознавайте ощущения в каждом участке тела

🎵 *Рекомендация:* Включите расслабляющую музыку, создайте приятную атмосферу""",
                    "category": "🧘‍♀️ Медитации",
                    "order": 3
                },
                {
                    "title": "🌙 Гормональный баланс и цикл",
                    "content": """**Работа с женским циклом для стабильного либидо:**

📅 **Фолликулярная фаза (дни 1-14):**
- Энергия повышается
- Идеальное время для новых экспериментов
- Либидо постепенно растет

📅 **Овуляция (дни 14-16):**
- Пик сексуального желания
- Максимальная чувствительность
- Лучшее время для интимной близости

📅 **Лютеиновая фаза (дни 17-28):**
- Энергия снижается
- Нужна нежность и забота
- Спокойные формы близости

💊 *Важно:* Следите за питанием и избегайте стресса""",
                    "category": "📊 Цикл и гормоны",
                    "order": 4
                },
                {
                    "title": "🔥 Пробуждение чувственности",
                    "content": """**Ежедневные практики для усиления чувственности:**

1. **Утренний ритуал:** 
   - 5 минут стояния босиком на земле
   - Массаж тела с аромамаслами
   - Благодарность своему телу

2. **Вечерняя практика:**
   - Теплая ванна с солью и маслами
   - Самомассаж груди и живота
   - Чтение романтической литературы

3. **Еженедельно:**
   - Танцы под любимую музыку
   - Свидание с самой собой
   - Новые ощущения (шелк, перья, разная температура)

🎨 *Совет:* Экспериментируйте с текстурами и ароматами""",
                    "category": "✨ Практики",
                    "order": 5
                }
            ]
            self.libido_content.insert_many(libido_data)
            print("✅ Добавлен контент для раздела либидо")
    
    # === МЕТОДЫ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ ===
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Получает пользователя по ID"""
        return self.users.find_one({'user_id': user_id})
    
    def create_user(self, user_id: int, username: str):
        """Создает нового пользователя"""
        user_data = {
            'user_id': user_id,
            'username': username,
            'gender': None,
            'survey_completed': False,
            'survey_answers': {},
            'subscription_end': None,
            'created_at': datetime.now(),
            'last_recommendation_index': 0,
            'shown_recommendations': [],
            'last_libido_content_index': 0,
            'priority_sections': [],
            'section_scores': {},
            'completed_sections': []
        }
        return self.users.insert_one(user_data)
    
    def update_gender(self, user_id: int, gender: str):
        """Сохраняет пол пользователя"""
        print(f"🔍 Сохранение пола: {gender} для пользователя {user_id}")
        return self.users.update_one(
            {'user_id': user_id},
            {'$set': {'gender': gender}}
        )
    
    def get_gender(self, user_id: int) -> Optional[str]:
        """Получает пол пользователя"""
        user = self.get_user(user_id)
        return user.get('gender') if user else None
    
    def is_female(self, user_id: int) -> bool:
        """Проверяет, является ли пользователь женщиной"""
        return self.get_gender(user_id) == "female"
    
    # === МЕТОДЫ ДЛЯ ПОДПИСКИ ===
    
    def update_subscription(self, user_id: int, days: int = 1):
        """Обновляет подписку пользователя"""
        subscription_end = datetime.now() + timedelta(minutes=1)
        return self.users.update_one(
            {'user_id': user_id},
            {'$set': {'subscription_end': subscription_end}}
        )
    
    def is_subscription_active(self, user_id: int) -> bool:
        """Проверяет активна ли подписка"""
        user = self.get_user(user_id)
        if not user or not user.get('subscription_end'):
            return False
        return user['subscription_end'] > datetime.now()
    
    def get_subscription_time_left(self, user_id: int) -> str:
        """Возвращает оставшееся время подписки в читаемом формате"""
        user = self.get_user(user_id)
        if not user or not user.get('subscription_end'):
            return "нет активной подписки"
        
        time_left = user['subscription_end'] - datetime.now()
        if time_left.total_seconds() <= 0:
            return "подписка истекла"
        
        days = time_left.days
        hours = time_left.seconds // 3600
        minutes = (time_left.seconds % 3600) // 60
        
        if days > 0:
            return f"{days} д {hours} ч {minutes} м"
        elif hours > 0:
            return f"{hours} ч {minutes} м"
        else:
            return f"{minutes} м"
    
    # === МЕТОДЫ ДЛЯ ОПРОСНИКА И РАЗДЕЛОВ ===
    
    def get_section_questions(self, section_id: str) -> List[Dict]:
        """Получает вопросы для конкретного раздела"""
        try:
            questions = list(self.questions.find(
                {'section': section_id}, 
                sort=[('order', 1)]
            ))
            print(f"🔍 Загружено {len(questions)} вопросов для раздела {section_id}")
            return questions
        except Exception as e:
            print(f"❌ Ошибка получения вопросов раздела {section_id}: {e}")
            return []
        
    def save_section_result(self, user_id: int, section_id: str, score: int):  # ⬅️ Убрали answers: dict
        """Сохраняет результат раздела (только число)"""
        print("внутри save section results db")
        print("score")
        print(score)
        try:
            section_config = config.SECTIONS_CONFIG.get(section_id, {})
            result = self.user_sections.update_one(
                {'user_id': user_id, 'section': section_id},
                {'$set': {
                    'score': score,  # ⬅️ Сохраняем только число
                    'completed_at': datetime.now(),
                    'section_name': section_config.get('name', section_id),
                }},
                upsert=True
            )
            print(f"✅ Результат раздела {section_id} сохранен для пользователя {user_id}: {score} баллов")
            return result
        except Exception as e:
            print(f"❌ Ошибка сохранения результата раздела: {e}")
            return None
    
    def complete_survey(self, user_id: int, section_scores: dict, priority_sections: list):
        """Завершает опросник и сохраняет приоритеты"""
        try:
            total_score = sum(section_scores.values())
            completed_sections = list(section_scores.keys())
            
            result = self.users.update_one(
                {'user_id': user_id},
                {'$set': {
                    'survey_completed': True,
                    'survey_completed_at': datetime.now(),
                    'section_scores': section_scores,
                    'priority_sections': priority_sections,
                    'total_score': total_score,
                    'completed_sections': completed_sections,
                    'survey_version': '8_sections_v1'
                }}
            )
            print(f"✅ Опросник завершен для пользователя {user_id}, приоритеты: {priority_sections}")
            return result
        except Exception as e:
            print(f"❌ Ошибка завершения опросника: {e}")
            return None
    
    def has_completed_survey(self, user_id: int) -> bool:
        """Проверяет, прошел ли пользователь опросник"""
        user = self.get_user(user_id)
        return user.get('survey_completed', False) if user else False
    
    def get_user_priority_sections(self, user_id: int) -> List[str]:
        """Получает приоритетные разделы пользователя"""
        try:
            user = self.users.find_one({'user_id': user_id})
            if user and 'priority_sections' in user:
                return user['priority_sections']
            
            # Если приоритеты не установлены, возвращаем разделы по умолчанию
            return list(config.SECTIONS_CONFIG.keys())[:3]
        except Exception as e:
            print(f"❌ Ошибка получения приоритетных разделов: {e}")
            return list(config.SECTIONS_CONFIG.keys())[:3]
    
    def get_section_results(self, user_id: int) -> Dict[str, Dict]:
        """Получает результаты по всем разделам пользователя"""
        try:
            sections = list(self.user_sections.find({'user_id': user_id}))
            return {section['section']: section for section in sections}
        except Exception as e:
            print(f"❌ Ошибка получения результатов разделов: {e}")
            return {}
    
    def has_completed_section(self, user_id: int, section_id: str) -> bool:
        """Проверяет, завершил ли пользователь конкретный раздел"""
        try:
            section = self.user_sections.find_one({
                'user_id': user_id, 
                'section': section_id
            })
            return section is not None
        except Exception as e:
            print(f"❌ Ошибка проверки завершения раздела: {e}")
            return False
    
    def get_completed_sections_count(self, user_id: int) -> int:
        """Получает количество завершенных разделов"""
        try:
            count = self.user_sections.count_documents({'user_id': user_id})
            return count
        except Exception as e:
            print(f"❌ Ошибка получения количества разделов: {e}")
            return 0
    
    def reset_survey_progress(self, user_id: int):
        """Сбрасывает прогресс опросника"""
        try:
            # Удаляем результаты разделов
            self.user_sections.delete_many({'user_id': user_id})
            
            # Сбрасываем флаг завершения опросника
            self.users.update_one(
                {'user_id': user_id},
                {'$set': {
                    'survey_completed': False,
                    'survey_completed_at': None,
                    'section_scores': {},
                    'priority_sections': [],
                    'total_score': 0,
                    'completed_sections': [],
                    'shown_recommendations': []
                }}
            )
            print(f"✅ Прогресс опросника сброшен для пользователя {user_id}")
        except Exception as e:
            print(f"❌ Ошибка сброса прогресса опросника: {e}")
    
    # === МЕТОДЫ ДЛЯ РЕКОМЕНДАЦИЙ ===
    
    def get_personalized_recommendations(self, user_id: int) -> List[Dict]:
        """Получить персонализированные рекомендации на основе опросника"""
        user = self.get_user(user_id)
        if not user or not user.get('survey_answers'):
            return []
        
        answers = user['survey_answers']
        gender = user.get('gender')
        tags = self._analyze_answers(answers, gender)
        
        if not tags:
            return list(self.recommendations.find().sort("priority", -1))
        
        query = {"tags": {"$in": tags}}
        return list(self.recommendations.find(query).sort("priority", -1))
    
    def get_next_recommendation(self, user_id: int) -> Optional[Dict]:
        """Получить следующую НЕПОВТОРЯЮЩУЮСЯ рекомендацию"""
        user = self.get_user(user_id)
        if not user:
            return None
        
        recommendations = self.get_personalized_recommendations(user_id)
        if not recommendations:
            return None
        
        shown_recommendations = user.get('shown_recommendations', [])
        
        for recommendation in recommendations:
            if recommendation['_id'] not in shown_recommendations:
                new_shown = shown_recommendations + [recommendation['_id']]
                self.users.update_one(
                    {'user_id': user_id},
                    {'$set': {'shown_recommendations': new_shown}}
                )
                return recommendation
        
        return None
    
    def get_next_recommendation_by_section(self, user_id: int, section_id: str) -> Optional[Dict]:
        """Получает следующую рекомендацию из указанного раздела"""
        user = self.users.find_one({"user_id": user_id})
        if not user:
            return None
            
        shown_recommendations = user.get('shown_recommendations', [])
        
        # Ищем рекомендацию из нужного раздела, которую еще не показывали
        recommendation = self.recommendations.find_one({
            "section": section_id,
            "_id": {"$nin": shown_recommendations}
        })
        
        if recommendation:
            # Добавляем в показанные
            self.users.update_one(
                {"user_id": user_id},
                {"$push": {"shown_recommendations": recommendation["_id"]}}
            )
            print(f"🔍 Найдена рекомендация: {recommendation['title']} для раздела {section_id}")
        else:
            print(f"🔍 Рекомендации для раздела {section_id} не найдены или все показаны")
        
        return recommendation
    
    def get_recommendation_count(self, user_id: int) -> int:
        """Получить общее количество рекомендаций"""
        recommendations = self.get_personalized_recommendations(user_id)
        return len(recommendations) if recommendations else 0
    
    def get_remaining_recommendations_count(self, user_id: int) -> int:
        """Получить количество оставшихся непоказанных рекомендаций"""
        user = self.get_user(user_id)
        if not user:
            return 0
        
        recommendations = self.get_personalized_recommendations(user_id)
        shown_recommendations = user.get('shown_recommendations', [])
        
        if not recommendations:
            return 0
        
        remaining = [rec for rec in recommendations if rec['_id'] not in shown_recommendations]
        return len(remaining)
    
    def get_remaining_recommendations_count_by_section(self, user_id: int, section_id: str) -> int:
        """Получает количество оставшихся рекомендаций по разделу"""
        user = self.users.find_one({"user_id": user_id})
        if not user:
            return 0
            
        shown_recommendations = user.get('shown_recommendations', [])
        
        count = self.recommendations.count_documents({
            "section": section_id,
            "_id": {"$nin": shown_recommendations}
        })
        
        return count
    
    def get_recommendation_count_by_section(self, user_id: int, section_id: str) -> int:
        """Получает общее количество рекомендаций по разделу"""
        count = self.recommendations.count_documents({
            "section": section_id
        })
        return count
    
    # === МЕТОДЫ ДЛЯ РАЗДЕЛА ЛИБИДО ===
    
    def get_libido_content(self) -> List[Dict]:
        """Получить весь контент для раздела либидо"""
        return list(self.libido_content.find().sort("order", 1))
    
    def get_next_libido_content(self, user_id: int) -> Optional[Dict]:
        """Получить следующий контент для раздела либидо"""
        user = self.get_user(user_id)
        if not user:
            return None
        
        all_content = self.get_libido_content()
        if not all_content:
            return None
        
        current_index = user.get('last_libido_content_index', 0)
        
        if current_index >= len(all_content):
            return None  # Весь контент показан
        
        content = all_content[current_index]
        
        # Обновляем индекс для следующего контента
        self.users.update_one(
            {'user_id': user_id},
            {'$set': {'last_libido_content_index': current_index + 1}}
        )
        
        return content
    
    def get_remaining_libido_content_count(self, user_id: int) -> int:
        """Получить количество оставшегося контента либидо"""
        user = self.get_user(user_id)
        if not user:
            return 0
        
        all_content = self.get_libido_content()
        current_index = user.get('last_libido_content_index', 0)
        
        return max(0, len(all_content) - current_index)
    
    def reset_libido_content(self, user_id: int):
        """Сбрасывает прогресс по контенту либидо"""
        return self.users.update_one(
            {'user_id': user_id},
            {'$set': {'last_libido_content_index': 0}}
        )
    
    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===
    
    def _analyze_answers(self, answers: Dict, gender: Optional[str]) -> List[str]:
        """Анализирует ответы и возвращает теги для рекомендаций"""
        tags = []
        
        for question_id, answer in answers.items():
            if question_id == "relationship_type":
                if answer in ["married"]:
                    tags.extend(["брак", "долгие_отношения", "семья"])
                elif answer in ["long_term"]:
                    tags.extend(["долгие_отношения", "стабильность"])
                elif answer in ["new", "dating"]:
                    tags.extend(["новые_отношения", "знакомство", "развитие"])
            
            elif question_id == "main_issue":
                if answer == "communication":
                    tags.extend(["коммуникация", "общение", "понимание"])
                elif answer == "trust":
                    tags.extend(["доверие", "ревность", "безопасность"])
                elif answer == "intimacy":
                    tags.extend(["интимность", "близость", "страсть"])
                elif answer == "family":
                    tags.extend(["семья", "дети", "родственники"])
                elif answer == "finance":
                    tags.extend(["финансы", "бюджет", "деньги"])
                elif answer == "other":
                    tags.extend(["общие", "развитие", "гармония"])
            
            elif question_id == "stress_level":
                if answer in ["very_high", "high"]:
                    tags.extend(["стресс", "конфликты", "напряжение"])
                else:
                    tags.extend(["гармония", "развитие"])
            
            elif question_id == "time_together":
                if answer in ["very_little", "little"]:
                    tags.extend(["время_вместе", "внимание", "близость"])
            
            elif question_id == "goals":
                if answer == "strengthen":
                    tags.extend(["укрепление", "развитие", "стабильность"])
                elif answer == "resolve_conflicts":
                    tags.extend(["конфликты", "решение", "коммуникация"])
                elif answer == "improve_communication":
                    tags.extend(["коммуникация", "общение", "понимание"])
                elif answer == "family_planning":
                    tags.extend(["семья", "дети", "планирование"])
                elif answer == "rekindle_passion":
                    tags.extend(["страсть", "романтика", "близость"])
        
        # Добавляем гендерные теги
        if gender == "female":
            tags.extend(["женщина", "женское_здоровье"])
        elif gender == "male":
            tags.extend(["мужчина", "мужское_здоровье"])
        
        return list(set(tags))
    def get_section_priority(self, user_id: int) -> str:
        ##"""Получает приоритетный раздел пользователя"""
        try:
            user = self.users.find_one({"user_id": user_id})
            if user and 'priority_sections' in user and user['priority_sections']:
                return user['priority_sections'][0]  # Возвращаем первый приоритетный раздел
            return 'communication'  # Значение по умолчанию
        except Exception as e:
            print(f"❌ Ошибка получения приоритетного раздела: {e}")
            return 'communication'

    def update_section_priority(self, user_id: int, priority_section: str):
        """Обновляет приоритетный раздел для пользователя"""
        try:
            # Получаем текущие приоритеты
            user = self.users.find_one({"user_id": user_id})
            current_priorities = user.get('priority_sections', []) if user else []
            
            # Если раздел уже в приоритетах, перемещаем его на первое место
            if priority_section in current_priorities:
                current_priorities.remove(priority_section)
            current_priorities.insert(0, priority_section)
            
            # Сохраняем только топ-3 приоритета
            updated_priorities = current_priorities[:3]
            
            result = self.users.update_one(
                {"user_id": user_id},
                {"$set": {"priority_sections": updated_priorities}}
            )
            print(f"✅ Приоритеты обновлены для пользователя {user_id}: {updated_priorities}")
            return result
        except Exception as e:
            print(f"❌ Ошибка обновления приоритетов: {e}")
            return None

    def get_section_questions(self, section_id: str) -> list:
        """Получает вопросы для конкретного раздела"""
        try:
            questions = list(self.questions.find(
                {'section': section_id}
            ).sort('order', 1))
            print(f"🔍 Загружено {len(questions)} вопросов для раздела {section_id}")
            return questions
        except Exception as e:
            print(f"❌ Ошибка получения вопросов раздела {section_id}: {e}")
            return []

    # def save_section_result(self, user_id: int, section_id: str, score: int, answers: dict):
    #     """Сохраняет результат раздела"""
    #     try:
    #         section_config = config.SECTIONS_CONFIG.get(section_id, {})
    #         result = self.user_sections.update_one(
    #             {'user_id': user_id, 'section': section_id},
    #             {'$set': {
    #                 'score': score,
    #                 'answers': answers,
    #                 'completed_at': datetime.now(),
    #                 'section_name': section_config.get('name', section_id),
    #                 'max_score': len(answers) * 5  # Предполагая шкалу 1-5
    #             }},
    #             upsert=True
    #         )
    #         print(f"✅ Результат раздела {section_id} сохранен для пользователя {user_id}")
    #         return result
    #     except Exception as e:
    #         print(f"❌ Ошибка сохранения результата раздела: {e}")
    #         return None

    def complete_survey(self, user_id: int, section_scores: dict, priority_sections: list):
        """Завершает опросник и сохраняет приоритеты"""
        try:
            total_score = sum(section_scores.values())
            completed_sections = list(section_scores.keys())
            
            result = self.users.update_one(
                {'user_id': user_id},
                {'$set': {
                    'survey_completed': True,
                    'survey_completed_at': datetime.now(),
                    'section_scores': section_scores,
                    'priority_sections': priority_sections,
                    'total_score': total_score,
                    'completed_sections': completed_sections,
                    'survey_version': '8_sections_v1'
                }}
            )
            print(f"✅ Опросник завершен для пользователя {user_id}, приоритеты: {priority_sections}")
            return result
        except Exception as e:
            print(f"❌ Ошибка завершения опросника: {e}")
            return None

    def get_user_priority_sections(self, user_id: int) -> list:
        """Получает приоритетные разделы пользователя"""
        try:
            user = self.users.find_one({'user_id': user_id})
            if user and 'priority_sections' in user and user['priority_sections']:
                return user['priority_sections']
            
            # Если приоритеты не установлены, возвращаем разделы по умолчанию
            return list(config.SECTIONS_CONFIG.keys())
        except Exception as e:
            print(f"❌ Ошибка получения приоритетных разделов: {e}")
            return list(config.SECTIONS_CONFIG.keys())

    def get_remaining_recommendations_count_by_section(self, user_id: int, section_id: str) -> int:
        """Получает количество оставшихся рекомендаций по разделу"""
        try:
            user = self.users.find_one({"user_id": user_id})
            if not user:
                return 0
                
            shown_recommendations = user.get('shown_recommendations', [])
            
            count = self.recommendations.count_documents({
                "section": section_id,
                "_id": {"$nin": shown_recommendations}
            })
            
            return count
        except Exception as e:
            print(f"❌ Ошибка получения количества рекомендаций по разделу: {e}")
            return 0

    def get_recommendation_count_by_section(self, user_id: int, section_id: str) -> int:
        """Получает общее количество рекомендаций по разделу"""
        try:
            count = self.recommendations.count_documents({
                "section": section_id
            })
            return count
        except Exception as e:
            print(f"❌ Ошибка получения общего количества рекомендаций: {e}")
            return 0

    def mark_survey_completed(self, user_id: int):
        """Помечает опросник как завершенный"""
        try:
            result = self.users.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "survey_completed": True,
                        "survey_completed_at": datetime.now()
                    }
                }
            )
            print(f"✅ Опросник помечен как завершенный для пользователя {user_id}")
            return result
        except Exception as e:
            print(f"❌ Ошибка отметки завершения опросника: {e}")
            return None

    def has_completed_survey(self, user_id: int) -> bool:
        """Проверяет, прошел ли пользователь опросник"""
        try:
            user = self.users.find_one({"user_id": user_id})
            return user.get('survey_completed', False) if user else False
        except Exception as e:
            print(f"❌ Ошибка проверки завершения опросника: {e}")
            return False

    def get_section_results(self, user_id: int) -> Dict[str, Dict]:
        """Получает результаты по всем разделам пользователя"""
        try:
            sections = list(self.user_sections.find({'user_id': user_id}))
            return {section['section']: section for section in sections}
        except Exception as e:
            print(f"❌ Ошибка получения результатов разделов: {e}")
            return {}

    def has_completed_section(self, user_id: int, section_id: str) -> bool:
        """Проверяет, завершил ли пользователь конкретный раздел"""
        try:
            section = self.user_sections.find_one({
                'user_id': user_id, 
                'section': section_id
            })
            return section is not None
        except Exception as e:
            print(f"❌ Ошибка проверки завершения раздела: {e}")
            return False

    def get_completed_sections_count(self, user_id: int) -> int:
        """Получает количество завершенных разделов"""
        try:
            count = self.user_sections.count_documents({'user_id': user_id})
            return count
        except Exception as e:
            print(f"❌ Ошибка получения количества разделов: {e}")
            return 0

    def reset_survey_progress(self, user_id: int):
        """Сбрасывает прогресс опросника"""
        try:
            # Удаляем результаты разделов
            self.user_sections.delete_many({'user_id': user_id})
            
            # Сбрасываем флаг завершения опросника
            self.users.update_one(
                {'user_id': user_id},
                {'$set': {
                    'survey_completed': False,
                    'survey_completed_at': None,
                    'section_scores': {},
                    'priority_sections': [],
                    'total_score': 0,
                    'completed_sections': [],
                    'shown_recommendations': []
                }}
            )
            print(f"✅ Прогресс опросника сброшен для пользователя {user_id}")
        except Exception as e:
            print(f"❌ Ошибка сброса прогресса опросника: {e}")

    def get_movie_recommendations(self,user_id, limit=1):
        # Здесь можно добавить логику подбора фильмов на основе ответов пользователя
        return list(db.movies.aggregate([
            {'$match': {'is_active': True}},
            {'$sample': {'size': limit}}
        ]))

    def get_book_recommendations(self,user_id, limit=1):
        """Получает рекомендации книг с учетом предпочтений пользователя"""
        return list(db.books.aggregate([
            {'$match': {'is_active': True}},
            {'$sample': {'size': limit}}
        ]))

    def get_user_last_movie_sent(self,user_id):
        """Получает дату последней отправки фильма"""
        user = db.users.find_one({'_id': user_id})
        return user.get('last_movie_sent') if user else None

    def get_user_last_book_sent(self,user_id):
        """Получает дату последней отправки книги"""
        user = db.users.find_one({'_id': user_id})
        return user.get('last_book_sent') if user else None

    def update_last_movie_sent(self,user_id):
        """Обновляет дату последней отправки фильма"""
        db.users.update_one(
            {'_id': user_id},
            {'$set': {'last_movie_sent': datetime.now()}}
        )

    def update_last_book_sent(user_id):
        """Обновляет дату последней отправки книги"""
        db.users.update_one(
            {'_id': user_id},
            {'$set': {'last_book_sent': datetime.now()}}
        )
    ############ вставляем тут 
    def get_section_recommendations_count(self) -> int:
        """Получить общее количество рекомендаций в новой структуре"""
        total_count = 0
        sections_cursor = self.activities.find({})
        
        for section_doc in sections_cursor:
            content = section_doc.get('content', [])
            total_count += len(content)
        
        return total_count

    def get_remaining_section_recommendations_count(self, user_id: int) -> int:
        """Получить количество оставшихся непоказанных рекомендаций в новой структуре"""
        user = self.get_user(user_id)
        if not user:
            return 0
        
        shown_recommendations = user.get('shown_recommendations', [])
        total_count = self.get_section_recommendations_count()
        
        return total_count - len(shown_recommendations)

    def get_remaining_section_recommendations_by_category(self, user_id: int, section: str) -> int:
        """Получает количество оставшихся рекомендаций по разделу в новой структуре"""
        user = self.get_user(user_id)
        if not user:
            return 0
            
        shown_recommendations = user.get('shown_recommendations', [])
        
        section_doc = self.activities.find_one({"section": section})
        if not section_doc:
            return 0
        
        content = section_doc.get('content', [])
        total_in_section = len(content)
        
        # Считаем сколько уже показано из этой секции (обрабатываем оба типа ID)
        shown_in_section = 0
        for rec_id in shown_recommendations:
            # Если это строка (новая структура)
            if isinstance(rec_id, str) and rec_id.startswith(f"{section}_"):
                shown_in_section += 1
            # Если это ObjectId (старая структура) - игнорируем для подсчета новой структуры
            # Или можно добавить логику для конвертации, если нужно
        
        return total_in_section - shown_in_section

    def get_section_recommendations_count_by_category(self, section: str) -> int:
        """Получает общее количество рекомендаций по разделу в новой структуре"""
        section_doc = self.activities.find_one({"section": section})
        if not section_doc:
            return 0
        
        content = section_doc.get('content', [])
        return len(content)

    def get_personalized_section_recommendations(self, user_id: int, limit: int = 10) -> list:
        """Получить персонализированные рекомендации из новой структуры"""
        user = self.get_user(user_id)
        if not user:
            return []
        
        shown_recommendations = user.get('shown_recommendations', [])
        
        # Получаем все секции с рекомендациями
        all_recommendations = []
        sections_cursor = self.activities.find({})
        
        for section_doc in sections_cursor:
            section_name = section_doc.get('section', '')
            content = section_doc.get('content', [])
            
            for rec in content:
                # Создаем уникальный ID для рекомендации (секция + индекс)
                rec_id = f"{section_name}_{content.index(rec)}"
                if rec_id not in shown_recommendations:
                    rec['_id'] = rec_id
                    rec['section'] = section_name
                    all_recommendations.append(rec)
        
        # Ограничиваем количество и возвращаем
        recommendations = all_recommendations[:limit]
        
        # Обновляем список показанных рекомендаций
        if recommendations:
            new_shown_ids = [rec['_id'] for rec in recommendations]
            self.users.update_one(
                {"user_id": user_id},
                {"$push": {"shown_recommendations": {"$each": new_shown_ids}}}
            )
        
        return recommendations

    def get_section_recommendations_by_category(self, user_id: int, section: str, limit: int = 5) -> list:
        """Получить рекомендации по конкретному разделу из новой структуры"""
        user = self.get_user(user_id)
        if not user:
            return []
        
        shown_recommendations = user.get('shown_recommendations', [])
        
        section_doc = self.activities.find_one({"section": section})
        if not section_doc:
            return []
        
        content = section_doc.get('content', [])
        recommendations = []
        
        for rec in content:
            rec_id = f"{section}_{content.index(rec)}"
            if rec_id not in shown_recommendations:
                rec['_id'] = rec_id
                rec['section'] = section
                recommendations.append(rec)
                
                if len(recommendations) >= limit:
                    break
        
        # Обновляем список показанных рекомендаций
        if recommendations:
            new_shown_ids = [rec['_id'] for rec in recommendations]
            self.users.update_one(
                {"user_id": user_id},
                {"$push": {"shown_recommendations": {"$each": new_shown_ids}}}
            )
        
        return recommendations

    def format_section_recommendation(self, recommendation: dict) -> str:
        """Форматирует рекомендацию из новой структуры в красивый текст для отправки"""
        if not recommendation:
            return "Рекомендация не найдена"
        
        title = recommendation.get('title', 'Без названия')
        goal = recommendation.get('goal', '')
        steps = recommendation.get('steps', [])
        section = recommendation.get('section', '')
        
        formatted_text = f"🎯 **{title}**\n\n"
        
        if goal:
            formatted_text += f"**Цель:** {goal}\n\n"
        
        if steps:
            formatted_text += "**Шаги:**\n"
            for i, step in enumerate(steps, 1):
                formatted_text += f"{i}. {step}\n"
        
        if section:
            formatted_text += f"\n#{section}"
        
        return formatted_text

    def get_user_section_stats(self, user_id: int) -> dict:
        """Получить статистику по рекомендациям новой структуры для пользователя"""
        user = self.get_user(user_id)
        if not user:
            return {}
        
        shown_recommendations = user.get('shown_recommendations', [])
        total_recommendations = self.get_section_recommendations_count()
        remaining_recommendations = total_recommendations - len(shown_recommendations)
        
        # Статистика по секциям
        section_stats = {}
        sections_cursor = self.activities.find({})
        
        for section_doc in sections_cursor:
            section_name = section_doc.get('section', '')
            content = section_doc.get('content', [])
            total_in_section = len(content)
            
            shown_in_section = len([rec_id for rec_id in shown_recommendations if rec_id.startswith(f"{section_name}_")])
            remaining_in_section = total_in_section - shown_in_section
            
            section_stats[section_name] = {
                'total': total_in_section,
                'shown': shown_in_section,
                'remaining': remaining_in_section
            }
        
        return {
            'total': total_recommendations,
            'shown': len(shown_recommendations),
            'remaining': remaining_recommendations,
            'sections': section_stats
        }
    def get_next_section_recommendation_by_category(self, user_id: int, section: str) -> Optional[Dict]:
        """Получает следующую рекомендацию из указанного раздела в новой структуре"""
        user = self.get_user(user_id)
        if not user:
            return None
            
        shown_recommendations = user.get('shown_recommendations', [])
        
        # Ищем секцию
        section_doc = self.activities.find_one({"section": section})
        if not section_doc:
            print(f"🔍 Раздел {section} не найден")
            return None
        
        content = section_doc.get('content', [])
        if not content:
            print(f"🔍 В разделе {section} нет рекомендаций")
            return None
        
        # Ищем первую непоказанную рекомендацию из этого раздела
        for rec in content:
            rec_id = f"{section}_{content.index(rec)}"
            if rec_id not in shown_recommendations:
                # Добавляем ID и секцию к рекомендации
                rec['_id'] = rec_id
                rec['section'] = section
                
                # Добавляем в показанные
                self.users.update_one(
                    {"user_id": user_id},
                    {"$push": {"shown_recommendations": rec_id}}
                )
                print(f"🔍 Найдена рекомендация: {rec['title']} для раздела {section}")
                return rec
        
        print(f"🔍 Все рекомендации для раздела {section} уже показаны")
        return None

    def get_next_recommendation_from_any_collection_old(self, user_id: int, section: str) -> Optional[Dict]:
        """Ищет следующую рекомендацию во всех коллекциях"""
        for collection_name in self.recommendation_collections:
            collection = getattr(self, collection_name)
            
            # Для activities (новая структура)
            if collection_name == 'activities':
                section_doc = collection.find_one({"section": section})
                if section_doc:
                    content = section_doc.get('content', [])
                    user = self.get_user(user_id)
                    shown_recommendations = user.get('shown_recommendations', []) if user else []
                    
                    for rec in content:
                        rec_id = f"{collection_name}_{section}_{content.index(rec)}"
                        if rec_id not in [r for r in shown_recommendations if isinstance(r, str)]:
                            rec['_id'] = rec_id
                            rec['section'] = section
                            rec['collection'] = collection_name
                            
                            # Добавляем в показанные
                            if user:
                                self.users.update_one(
                                    {"user_id": user_id},
                                    {"$push": {"shown_recommendations": rec_id}}
                                )
                            return rec
            
            # Для literature, cinema, questions_new (предполагаем старую структуру)
            else:
                user = self.get_user(user_id)
                shown_recommendations = user.get('shown_recommendations', []) if user else []
                
                recommendation = collection.find_one({
                    "section": section,
                    "_id": {"$nin": shown_recommendations}
                })
                
                if recommendation:
                    # Создаем уникальный ID с указанием коллекции
                    rec_id = f"{collection_name}_{recommendation['_id']}"
                    recommendation['collection'] = collection_name
                    
                    # Добавляем в показанные
                    if user:
                        self.users.update_one(
                            {"user_id": user_id},
                            {"$push": {"shown_recommendations": rec_id}}
                        )
                    return recommendation
        
        return None
    def get_next_recommendation_from_any_collection(self, user_id: int, section: str) -> Optional[Dict]:
        """Ищет следующую рекомендацию во всех коллекциях"""
        user = self.get_user(user_id)
        if not user:
            return None
            
        shown_recommendations = user.get('shown_recommendations', [])
        
        for collection_name in self.recommendation_collections:
            collection = getattr(self, collection_name)
            
            # Для activities (новая структура с массивом content)
            if collection_name == 'activities':
                section_doc = collection.find_one({"section": section})
                if section_doc:
                    content = section_doc.get('content', [])
                    for rec in content:
                        rec_id = f"{collection_name}_{section}_{content.index(rec)}"
                        if rec_id not in [r for r in shown_recommendations if isinstance(r, str)]:
                            rec['_id'] = rec_id
                            rec['section'] = section
                            rec['collection'] = collection_name
                            
                            # Добавляем в показанные
                            self.users.update_one(
                                {"user_id": user_id},
                                {"$push": {"shown_recommendations": rec_id}}
                            )
                            return rec
            
            # Для literature (структура с массивом content)
            elif collection_name == 'literature':
                section_doc = collection.find_one({"section": section})
                if section_doc:
                    content = section_doc.get('content', [])
                    for rec in content:
                        rec_id = f"{collection_name}_{section}_{content.index(rec)}"
                        if rec_id not in [r for r in shown_recommendations if isinstance(r, str)]:
                            rec['_id'] = rec_id
                            rec['section'] = section
                            rec['collection'] = collection_name
                            
                            self.users.update_one(
                                {"user_id": user_id},
                                {"$push": {"shown_recommendations": rec_id}}
                            )
                            return rec
            
            # Для cinema (структура с массивом films -> movies)
            elif collection_name == 'cinema':
                section_doc = collection.find_one({"section": section})
                if section_doc and section_doc.get('films'):
                    films = section_doc['films']
                    for film_group in films:
                        movies = film_group.get('movies', [])
                        for movie in movies:
                            rec_id = f"{collection_name}_{section}_{films.index(film_group)}_{movies.index(movie)}"
                            if rec_id not in [r for r in shown_recommendations if isinstance(r, str)]:
                                # Создаем рекомендацию из данных фильма
                                recommendation = {
                                    '_id': rec_id,
                                    'section': section,
                                    'collection': collection_name,
                                    'prescribe': film_group.get('prescribe', ''),
                                    'as_result': film_group.get('as_result', ''),
                                    'movies': [movie]  # Отправляем один фильм
                                }
                                
                                self.users.update_one(
                                    {"user_id": user_id},
                                    {"$push": {"shown_recommendations": rec_id}}
                                )
                                return recommendation
            
            # Для questions_new (структура с массивом content)
            elif collection_name == 'questions_new':
                section_doc = collection.find_one({"section": section})
                if section_doc:
                    content = section_doc.get('content', [])
                    for rec in content:
                        rec_id = f"{collection_name}_{section}_{content.index(rec)}"
                        if rec_id not in [r for r in shown_recommendations if isinstance(r, str)]:
                            rec['_id'] = rec_id
                            rec['section'] = section
                            rec['collection'] = collection_name
                            
                            self.users.update_one(
                                {"user_id": user_id},
                                {"$push": {"shown_recommendations": rec_id}}
                            )
                            return rec
        
        return None
    def get_next_activity_recommendation(self, user_id: int, section: str) -> Optional[Dict]:
        """Получает следующую рекомендацию из activities"""
        return self._get_recommendation_from_collection(user_id, section, 'activities')

    def get_next_literature_recommendation(self, user_id: int, section: str) -> Optional[Dict]:
        """Получает следующую книгу из literature"""
        return self._get_recommendation_from_collection(user_id, section, 'literature')

    def get_next_cinema_recommendation(self, user_id: int, section: str) -> Optional[Dict]:
        """Получает следующий фильм из cinema"""
        return self._get_recommendation_from_collection(user_id, section, 'cinema')

    def get_next_question_recommendation(self, user_id: int, section: str) -> Optional[Dict]:
        """Получает следующий вопрос из questions_new"""
        return self._get_recommendation_from_collection(user_id, section, 'questions_new')

    def _get_recommendation_from_collection(self, user_id: int, section: str, collection_name: str) -> Optional[Dict]:
        """Вспомогательный метод для получения рекомендации из конкретной коллекции"""
        user = self.get_user(user_id)
        if not user:
            return None
        # print(collection_name)
        print("collection_name внутри _get_rec_from_col" )
        shown_recommendations = user.get('shown_recommendations', [])
        collection = getattr(self, collection_name)
        # print("section")
        # print(section)
        # print("collection")
        # print(collection)
        # Общая логика для всех коллекций с массивом content
        if collection_name in ['activities', 'literature', 'questions_new']:
            section_doc = collection.find_one({"sector": section})
            # print(section_doc)
            # print("section_doc")
            # if section_doc:
                content = section_doc.get('content', [])
                for rec in content:
                    rec_id = f"{collection_name}_{section}_{content.index(rec)}"
                    if rec_id not in [r for r in shown_recommendations if isinstance(r, str)]:
                        rec['_id'] = rec_id
                        rec['section'] = section
                        rec['collection'] = collection_name
                        
                        self.users.update_one(
                            {"user_id": user_id},
                            {"$push": {"shown_recommendations": rec_id}}
                        )
                        return rec
        
        # Особенная логика для cinema
        elif collection_name == 'cinema':
            section_doc = collection.find_one({"sector": section})
            if section_doc and section_doc.get('films'):
                films = section_doc['films']
                for film_group in films:
                    movies = film_group.get('movies', [])
                    for movie in movies:
                        rec_id = f"{collection_name}_{section}_{films.index(film_group)}_{movies.index(movie)}"
                        if rec_id not in [r for r in shown_recommendations if isinstance(r, str)]:
                            recommendation = {
                                '_id': rec_id,
                                'section': section,
                                'collection': collection_name,
                                'prescribe': film_group.get('prescribe', ''),
                                'as_result': film_group.get('as_result', ''),
                                'movies': [movie]
                            }
                            
                            self.users.update_one(
                                {"user_id": user_id},
                                {"$push": {"shown_recommendations": rec_id}}
                            )
                            return recommendation
        
        return None
        
db = Database()
        



# Глобальный экземпляр базы данных
# 
