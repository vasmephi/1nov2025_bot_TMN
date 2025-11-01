# database.py
from pymongo import MongoClient
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import config

class DatabaseCouples: 

    def __init__(self, connection_string: str = None, db_name: str = None):
        """Инициализация базы данных"""
        # Используем значения из config по умолчанию
        self.connection_string = connection_string or config.MONGO_URI
        self.db_name = db_name or config.DATABASE_NAME
        
        try:
            self.client = MongoClient(self.connection_string)
            self.db = self.client[self.db_name]
            
            # Основные коллекции
            self.users = self.db.users
            self.questions = self.db.questions
            self.recommendations = self.db.recommendations
            
            # Новые коллекции для парной системы
            self.couples = self.db.couples
            self.invites = self.db.invites
            self.couple_surveys = self.db.couple_surveys
            self.user_results = self.db.user_results
        
        # Инициализируем коллекции при создании
            self._init_collections()
        except Exception as e:
            print(f"❌ Ошибка подключения к MongoDB: {e}")
            raise
    
    def _init_collections(self):
        """Инициализирует коллекции (создает если их нет)"""
        try:
            # Создаем коллекцию user_results если ее нет
            if 'user_results' not in self.db.list_collection_names():
                self.db.create_collection('user_results')
                print("✅ Коллекция user_results создана")
            
            # Создаем индексы для быстрого поиска
            self.user_results.create_index("user_id", unique=True)
            self.user_results.create_index("completed_at")
            
        except Exception as e:
            print(f"⚠️ Ошибка инициализации коллекций: {e}")

            print(f"✅ Подключение к БД: {self.db_name}")
            
        except Exception as e:
            print(f"❌ Ошибка подключения к MongoDB: {e}")
            raise

    # МЕТОДЫ ДЛЯ РАБОТЫ С ПАРАМИ
    def create_couple(self, user1_id: int, user2_id: int) -> bool:
        """Создает пару между пользователями"""
        try:
            couple_id = f"couple_{min(user1_id, user2_id)}_{max(user1_id, user2_id)}"
            
            # Проверяем, не существует ли уже такая пара
            existing_couple = self.couples.find_one({"couple_id": couple_id})
            if existing_couple:
                print(f"⚠️ Пара {couple_id} уже существует")
                return False
            
            # Получаем информацию о пользователях
            user1_info = self.users.find_one({"user_id": user1_id}) or {}
            user2_info = self.users.find_one({"user_id": user2_id}) or {}
            
            couple_data = {
                'couple_id': couple_id,
                'user1_id': min(user1_id, user2_id),
                'user2_id': max(user1_id, user2_id),
                'user1_info': {
                    'first_name': user1_info.get('first_name', 'User1'),
                    'username': user1_info.get('username', '')
                },
                'user2_info': {
                    'first_name': user2_info.get('first_name', 'User2'),
                    'username': user2_info.get('username', '')
                },
                'created_at': datetime.now(),
                'status': 'active',
                'surveys_completed': 0,
                'last_survey_date': None,
                'priority_sections': [],
                'relationship_stage': 'new'
            }
            
            result = self.couples.insert_one(couple_data)
            
            # Обновляем пользователей - добавляем ссылку на пару
            self.users.update_one(
                {'user_id': user1_id},
                {'$set': {
                    'partner_id': user2_id,
                    'couple_id': couple_id,
                    'in_relationship_since': datetime.now()
                }}
            )
            self.users.update_one(
                {'user_id': user2_id},
                {'$set': {
                    'partner_id': user1_id,
                    'couple_id': couple_id,
                    'in_relationship_since': datetime.now()
                }}
            )
            
            print(f"✅ Пара создана: {couple_id}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка создания пары: {e}")
            return False
    
    def get_section_questions(self, section_id: str) -> list:
        """Получает вопросы для конкретного раздела из БД с вариантами ответов"""
        try:
            questions = list(self.questions.find(
                {'section': section_id}
            ).sort('order', 1))
            
            print(f"🔍 Загружено {len(questions)} вопросов для раздела {section_id}")
            
            # Проверяем структуру вопросов
            for question in questions:
                print(f"🔍 Вопрос: {question['question']}")
                print(f"🔍 Варианты: {len(question.get('options', []))}")
            
            return questions
        except Exception as e:
            print(f"❌ Ошибка получения вопросов раздела {section_id}: {e}")
            return []
    def get_couple(self, user_id: int) -> Optional[Dict]:
        """Получает информацию о паре пользователя"""
        try:
            user = self.users.find_one({"user_id": user_id})
            if not user or 'couple_id' not in user:
                return None
                
            couple = self.couples.find_one({"couple_id": user['couple_id']})
            return couple
        except Exception as e:
            print(f"❌ Ошибка получения пары: {e}")
            return None

    def get_couple_by_id(self, couple_id: str) -> Optional[Dict]:
        """Получает пару по ID"""
        try:
            return self.couples.find_one({"couple_id": couple_id})
        except Exception as e:
            print(f"❌ Ошибка получения пары по ID: {e}")
            return None

    def remove_couple(self, user_id: int) -> bool:
        """Удаляет пару (для обоих пользователей)"""
        try:
            user = self.users.find_one({"user_id": user_id})
            if not user or 'couple_id' not in user:
                return False
                
            couple_id = user['couple_id']
            couple = self.couples.find_one({"couple_id": couple_id})
            if not couple:
                return False
            
            # Получаем ID обоих пользователей
            user1_id = couple['user1_id']
            user2_id = couple['user2_id']
            
            # Удаляем пару из коллекции
            self.couples.delete_one({"couple_id": couple_id})
            
            # Обновляем записи пользователей
            self.users.update_one(
                {"user_id": user1_id},
                {"$unset": {
                    'partner_id': "",
                    'couple_id': "", 
                    'in_relationship_since': ""
                }}
            )
            self.users.update_one(
                {"user_id": user2_id},
                {"$unset": {
                    'partner_id': "",
                    'couple_id': "",
                    'in_relationship_since': ""
                }}
            )
            
            print(f"✅ Пара {couple_id} удалена")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка удаления пары: {e}")
            return False

    def update_couple_stats(self, couple_id: str, survey_data: Dict = None):
        """Обновляет статистику пары после опросника"""
        try:
            update_data = {
                'last_activity': datetime.now()
            }
            
            if survey_data:
                update_data['$inc'] = {'surveys_completed': 1}
                update_data['$set'] = {
                    'last_survey_date': datetime.now(),
                    'priority_sections': survey_data.get('priority_sections', [])
                }
            
            result = self.couples.update_one(
                {"couple_id": couple_id},
                update_data
            )
            return result
        except Exception as e:
            print(f"❌ Ошибка обновления статистики пары: {e}")
            return None

    # МЕТОДЫ ДЛЯ РАБОТЫ С ПРИГЛАШЕНИЯМИ
    def create_invite(self, user_id: int, token: str, expires_hours: int = 24) -> bool:
        """Создает приглашение в БД"""
        try:
            expires_at = datetime.now() + timedelta(hours=expires_hours)
            
            invite_data = {
                'user_id': user_id,
                'token': token,
                'created_at': datetime.now(),
                'expires_at': expires_at,
                'used': False,
                'used_by': None,
                'used_at': None
            }
            
            self.invites.insert_one(invite_data)
            return True
        except Exception as e:
            print(f"❌ Ошибка создания приглашения: {e}")
            return False

    def get_invite_by_token(self, token: str):
        """Получает приглашение по токену"""
        try:
            invite = self.invites.find_one({
                'token': token,
                'used': False,
                'expires_at': {'$gt': datetime.now()}
            })
            return invite
        except Exception as e:
            print(f"❌ Ошибка получения приглашения: {e}")
            return None

    def mark_invite_used(self, token: str, used_by: int) -> bool:
        """Помечает приглашение как использованное"""
        try:
            result = self.invites.update_one(
                {'token': token},
                {'$set': {
                    'used': True, 
                    'used_by': used_by,
                    'used_at': datetime.now()
                }}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"❌ Ошибка отметки приглашения: {e}")
            return False

    # МЕТОДЫ ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ
    def get_user_info(self, user_id: int) -> Optional[Dict]:
        """Получает информацию о пользователе"""
        try:
            return self.users.find_one({"user_id": user_id})
        except Exception as e:
            print(f"❌ Ошибка получения информации о пользователе: {e}")
            return None

    def get_partner_id(self, user_id: int) -> Optional[int]:
        """Получает ID партнера пользователя"""
        try:
            user = self.users.find_one({"user_id": user_id})
            print(user)
            print("user")
            return user.get('partner_id') if user else None
        except Exception as e:
            print(f"❌ Ошибка получения партнера: {e}")
            return None

    def has_partner(self, user_id: int) -> bool:
        """Проверяет, есть ли у пользователя партнер"""
        try:
            user = self.users.find_one({"user_id": user_id})
            return user and 'partner_id' in user and user['partner_id'] is not None
        except Exception as e:
            print(f"❌ Ошибка проверки партнера: {e}")
            return False

    # МЕТОДЫ ДЛЯ РАБОТЫ С ПАРНЫМИ ОПРОСНИКАМИ
    def save_couple_survey_results(self, couple_id: str, survey_data: Dict) -> bool:
        """Сохраняет результаты парного опросника"""
        try:
            survey_record = {
                'couple_id': couple_id,
                'completed_at': datetime.now(),
                'user1_answers': survey_data.get('user1_answers', {}),
                'user2_answers': survey_data.get('user2_answers', {}),
                'weak_sections': survey_data.get('weak_sections', []),
                'recommendations': survey_data.get('recommendations', {}),
                'scores': {
                    'user1_total': survey_data.get('user1_total_score', 0),
                    'user2_total': survey_data.get('user2_total_score', 0),
                    'couple_average': survey_data.get('couple_average_score', 0)
                },
                'survey_version': 'couple_v1'
            }
            
            result = self.couple_surveys.insert_one(survey_record)
            
            # Обновляем статистику пары
            self.update_couple_stats(couple_id, survey_data)
            
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения парного опросника: {e}")
            return False

    def get_couple_survey_history(self, couple_id: str, limit: int = 5) -> List[Dict]:
        """Получает историю опросников пары"""
        try:
            surveys = list(self.couple_surveys.find(
                {"couple_id": couple_id}
            ).sort("completed_at", -1).limit(limit))
            
            return surveys
        except Exception as e:
            print(f"❌ Ошибка получения истории опросников: {e}")
            return []

    def get_couple_stats(self, user1_id: int, user2_id: int):
        """Получает статистику пары"""
        try:
            couple_id = f"couple_{min(user1_id, user2_id)}_{max(user1_id, user2_id)}"
            
            # Количество завершенных опросников
            surveys_count = self.couple_surveys.count_documents({'couple_id': couple_id})
            
            # Дата создания пары
            couple = self.couples.find_one({'couple_id': couple_id})
            together_since = couple['created_at'].strftime("%d.%m.%Y") if couple else "недавно"
            
            return {
                'surveys_completed': surveys_count,
                'together_since': together_since
            }
        except Exception as e:
            print(f"❌ Ошибка получения статистики пары: {e}")
            return {}
        
    
        
    def save_user_results(self, user_id: int):
        """Сохраняет итоговые результаты пользователя по всем секциям"""
        session = self.user_sessions.get(user_id)
        if not session:
            return
        
        user_results = {}
        
        # 🔥 ПРОХОДИМ ПО ВСЕМ СЕКЦИЯМ И СУММИРУЕМ ОТВЕТЫ
        for section_id, answers_dict in session.get('section_answers', {}).items():
            if answers_dict:
                # Суммируем все ответы в секции
                section_total = sum(
                    float(answer) for answer in answers_dict.values() 
                    if self._is_numeric(answer)
                )
                user_results[section_id] = section_total
                print(f"✅ Секция {section_id}: {len(answers_dict)} ответов, сумма = {section_total}")
            else:
                user_results[section_id] = 0
                print(f"⚠️ Секция {section_id}: нет ответов")
        
        # Сохраняем итоговые результаты
        self.user_results[user_id] = user_results
        print(f"💾 Сохранены результаты пользователя {user_id}: {user_results}")
    
    def save_individual_results(self, user_id: int, answers: dict) -> bool:
        """Сохраняет индивидуальные результаты пользователя И ОБНОВЛЯЕТ survey_completed"""
        try:
            # Сохраняем в user_results
            result = self.user_results.update_one(
                {'user_id': user_id},
                {'$set': {
                    'answers': answers,
                    'completed_at': datetime.now(),
                    'user_id': user_id
                }},
                upsert=True
            )
            
            # 🔥 ОБНОВЛЯЕМ survey_completed В КОЛЛЕКЦИИ USERS
            self.users.update_one(
                {'user_id': user_id},
                {'$set': {
                    'survey_completed': True,
                    'survey_completed_at': datetime.now(),
                    'last_survey_type': 'couple'  # Можно добавить тип опросника
                }}
            )
            
            print(f"✅ Результаты сохранены для пользователя {user_id}, survey_completed=True")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка сохранения результатов: {e}")
            return False

    def has_completed_survey(self, user_id: int) -> bool:
        """Проверяет, прошел ли пользователь опрос"""
        try:
            result = self.user_results.find_one({'user_id': user_id})
            return result is not None
        except Exception as e:
            print(f"❌ Ошибка проверки опроса: {e}")
            return False

    def get_user_results(self, user_id: int) -> dict:
        """Получает результаты пользователя"""
        try:
            result = self.user_results.find_one({'user_id': user_id})
            return result.get('answers', {}) if result else {}
        except Exception as e:
            print(f"❌ Ошибка получения результатов: {e}")
            return {}

    def get_both_users_results(self, user1_id: int, user2_id: int) -> tuple:
        """Получает результаты обоих пользователей"""
        user1_results = self.get_user_results(user1_id)
        user2_results = self.get_user_results(user2_id)
        return user1_results, user2_results

    def clear_user_results(self, user_id: int) -> bool:
        """Очищает результаты пользователя (для тестирования)"""
        try:
            result = self.user_results.delete_one({'user_id': user_id})
            return result.deleted_count > 0
        except Exception as e:
            print(f"❌ Ошибка очистки результатов: {e}")
            return False
    def save_couple_for_recommendations(self, user1_id: int, user2_id: int):
        """Сохраняет пару для парных рекомендаций"""
        try:
            # Просто сохраняем ID пары у каждого пользователя
            self.users.update_one(
                {'user_id': user1_id},
                {'$set': {'partner_id': user2_id, 'has_couple_survey': True}}
            )
            self.users.update_one(
                {'user_id': user2_id}, 
                {'$set': {'partner_id': user1_id, 'has_couple_survey': True}}
            )
            print(f"✅ Пара {user1_id}+{user2_id} сохранена для рекомендаций")
        except Exception as e:
            print(f"❌ Ошибка сохранения пары: {e}")
    def has_both_partners_completed_survey(self, user_id: int) -> bool:
        """Проверяет, завершили ли оба партнера опрос (по полю surveys_completed)"""
        try:
            couple = self.get_couple(user_id)
            if not couple:
                return False
            
            # 🔥 ПРОВЕРЯЕМ ПО surveys_completed В КОЛЛЕКЦИИ COUPLES
            return couple.get('surveys_completed', 0) > 0
        except Exception as e:
            print(f"❌ Ошибка проверки завершения пары: {e}")
            return False

    def mark_couple_survey_completed(self, user1_id: int, user2_id: int):
        """Помечает что пара завершила опрос (увеличивает surveys_completed)"""
        try:
            couple_id = f"couple_{min(user1_id, user2_id)}_{max(user1_id, user2_id)}"
            
            result = self.couples.update_one(
                {'couple_id': couple_id},
                {
                    '$inc': {'surveys_completed': 1},
                    '$set': {
                        'last_survey_date': datetime.now(),
                        'priority_sections': self._calculate_priority_sections(user1_id, user2_id)
                    }
                }
            )
            
            print(f"✅ Пара {couple_id} завершила опрос. Surveys: +1")
            return result.modified_count > 0
        except Exception as e:
            print(f"❌ Ошибка отметки завершения пары: {e}")
            return False
    def get_couple_priority_sections(self, user_id: int) -> list:
        """Получает приоритетные разделы пользователя ТОЛЬКО из коллекции couples"""
        try:
            # 🔥 ИЩЕМ ПАРУ ПОЛЬЗОВАТЕЛЯ
            couple_data = self.couples.find_one({
                '$or': [
                    {'user1_id': user_id},
                    {'user2_id': user_id}
                ]
            })
            
            if couple_data:
                if 'priority_sections' in couple_data and couple_data['priority_sections']:
                    print(f"✅ Приоритеты из couples: {couple_data['priority_sections']}")
                    return couple_data['priority_sections']
                else:
                    print(f"⚠️ В паре нет приоритетов, но пара найдена: {couple_data['_id']}")
            else:
                print(f"⚠️ Пара не найдена для пользователя {user_id}")
            
            # Если в couples нет приоритетов или пара не найдена
            return list(config.SECTIONS_CONFIG.keys())
        
        except Exception as e:
            print(f"❌ Ошибка получения приоритетных разделов: {e}")
            return list(config.SECTIONS_CONFIG.keys())
    def _calculate_priority_sections(self, user1_id: int, user2_id: int) -> list:
        """Рассчитывает приоритетные разделы для пары"""
        try:
            print(f"🔍 === НАЧАЛО РАСЧЕТА ПРИОРИТЕТОВ ===")
            print(f"🔍 user1_id: {user1_id}, user2_id: {user2_id}")
            
            # Получаем результаты обоих пользователей
            user1_results = self.get_user_results(user1_id)
            user2_results = self.get_user_results(user2_id)
            
            print(f"🔍 user1_results: {user1_results}")
            print(f"🔍 user2_results: {user2_results}")
            print(f"🔍 Тип user1_results: {type(user1_results)}")
            print(f"🔍 Тип user2_results: {type(user2_results)}")
            
            # Простая логика: находим разделы с наименьшими средними баллами
            section_scores = {}
            
            print(f"🔍 Разделы из конфига: {list(config.SECTIONS_CONFIG.keys())}")
            
            for section_id in config.SECTIONS_CONFIG.keys():
                print(f"🔍 Обрабатываем раздел: {section_id}")
                
                user1_section = user1_results.get(section_id, [])
                user2_section = user2_results.get(section_id, [])
                
                print(f"   user1_section: {user1_section} (тип: {type(user1_section)})")
                print(f"   user2_section: {user2_section} (тип: {type(user2_section)})")
                
                # 🔥 ПРОВЕРЯЕМ, ЕСТЬ ЛИ ДАННЫЕ У ОБОИХ ПОЛЬЗОВАТЕЛЕЙ
                if user1_section and user2_section:
                    print(f"   ✅ Оба пользователя заполнили раздел")
                    user1_sum = sum(user1_section[section_id])    
                    user2_sum = sum(user2_section[section_id])   
                    
                    # 🔥 ПРЕОБРАЗУЕМ В ЧИСЛА ЕСЛИ НУЖНО
                    # if isinstance(user1_section, (int, float)):
                    #     user1_sum = float(user1_section)
                    # elif isinstance(user1_section, (list, tuple)):
                    #     user1_sum = sum(float(x) for x in user1_section['section_id'])
                    # else:
                    #     user1_sum = float(user1_section) if str(user1_section).replace('.', '').isdigit() else 0
                    
                    # if isinstance(user2_section, (int, float)):
                    #     user2_sum = float(user2_section)
                    # elif isinstance(user2_section, (list, tuple)):
                    #     user2_sum = sum(float(x) for x in user2_section['section_id'])
                    # else:
                    #     user2_sum = float(user2_section) if str(user2_section).replace('.', '').isdigit() else 0
                    
                    avg_score = (user1_sum + user2_sum) / 2
                    section_scores[section_id] = avg_score
                    
                    print(f"   📊 user1_sum: {user1_sum}, user2_sum: {user2_sum}, avg: {avg_score}")
                else:
                    print(f"   ⚠️ Пропускаем раздел - нет данных у одного из пользователей")
            
            print(f"🔍 section_scores: {section_scores}")
            
            if not section_scores:
                print(f"⚠️ Нет данных для расчета приоритетов")
                return []
            
            # Сортируем по возрастанию (самые низкие баллы - самые приоритетные)
            sorted_sections = sorted(section_scores.items(), key=lambda x: x[1])
            priority_sections = [section_id for section_id, score in sorted_sections]
            
            print(f"🎯 Отсортированные разделы: {sorted_sections}")
            print(f"🎯 Топ-3 приоритетных раздела: {priority_sections}")
            print(f"🔍 === КОНЕЦ РАСЧЕТА ПРИОРИТЕТОВ ===\n")
            
            return priority_sections
                
        except Exception as e:
            print(f"❌ Ошибка расчета приоритетов: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    # database_couples.py - упрощенная версия
    def get_couple_recommendation(self, user1_id: int, user2_id: int):
        """Упрощенная версия - возвращает случайную рекомендацию"""
        try:
            # Просто возвращаем первую попавшуюся рекомендацию
            recommendation = self.recommendations.find_one({})
            
            if recommendation:
                print(f"✅ Упрощенная парная рекомендация: {recommendation['title']}")
            else:
                print("❌ Нет рекомендаций в базе")
                
            return recommendation
            
        except Exception as e:
            print(f"❌ Ошибка упрощенного получения рекомендации: {e}")
            return None