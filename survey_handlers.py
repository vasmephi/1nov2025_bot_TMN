from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import db
import config
import asyncio
from typing import Dict, Optional, List
from couple_manager import couple_manager



class AdvancedSurveyManager:
    def __init__(self):
        self.user_sessions = {}
        self.sections_order = self._get_sections_order()
    
    def _get_sections_order(self):
        """Возвращает порядок разделов по приоритету"""
        return sorted(config.SECTIONS_CONFIG.keys(), 
                     key=lambda x: config.SECTIONS_CONFIG[x]['priority'])
    
    async def start_survey(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало комплексного опросника"""
        if update.callback_query:
            await update.callback_query.answer()
            user_id = update.callback_query.from_user.id
        else:
            user_id = update.effective_user.id
        
        # Проверяем, не проходил ли уже опросник
        if db.has_completed_survey(user_id):
            await self.show_survey_completed(update, context)
            return
        
        # Создаем сессию опросника
        self.user_sessions[user_id] = {
            'current_section_index': 0,
            'current_question': 0,
            'section_answers': {},
            'completed_sections': [],
            'sections_order': self.sections_order.copy(),
            'started_at': asyncio.get_event_loop().time()
        }
        
        # Показываем первый раздел
        await self.show_section_intro(update, context, user_id)
    
    async def show_section_intro(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Показывает введение в раздел"""
        session = self.user_sessions.get(user_id)
        if not session:
            await self.restart_survey(update, context)
            return
        
        section_index = session['current_section_index']
        if section_index >= len(session['sections_order']):
            await self.complete_all_sections(update, context, user_id)
            return
        
        section_id = session['sections_order'][section_index]
        section_config = config.SECTIONS_CONFIG[section_id]
        
        # Загружаем вопросы для раздела
        questions = db.get_section_questions(section_id)
        if not questions:
            await self._handle_section_error(update, section_config['name'])
            return
        
        # Обновляем сессию
        session['current_section'] = section_id
        session['current_questions'] = questions
        session['current_question'] = 0
        session['answers'] = {}
        
        # Показываем введение в раздел
        completed_count = len(session['completed_sections'])
        total_sections = len(self.sections_order)
        
        text = f"📊 *Раздел {section_index + 1}/{total_sections}*\n\n"
        text += f"**{section_config['name']}**\n"
        text += f"{section_config['description']}\n\n"
        text += f"📝 Вопросов в разделе: {len(questions)}\n"
        text += f"⏱️ Примерное время: {len(questions) * 2} минут\n\n"
        text += f"🎯 Прогресс: {completed_count}/{total_sections} разделов завершено"
        
        keyboard = [
            [InlineKeyboardButton("📋 Начать раздел", callback_data=f"start_section_{section_id}")],
  ##          [InlineKeyboardButton("⏸️ Пропустить раздел", callback_data=f"skip_section_{section_id}")],
            [InlineKeyboardButton("⬅️ В главное меню", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def start_section(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начинает конкретный раздел"""
        if not update.callback_query:
            return
            
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        section_id = query.data.replace("start_section_", "")
        
        session = self.user_sessions.get(user_id)
        if not session:
            await self.restart_survey(update, context)
            return
        
        # Обновляем сессию
        session['current_section'] = section_id
        session['current_question'] = 0
        session['answers'] = {}
        
        # Загружаем вопросы для этого раздела
        questions = db.get_section_questions(section_id)
        if not questions:
            await self._handle_section_error(update, config.SECTIONS_CONFIG.get(section_id, {}).get('name', section_id))
            return
        
        session['current_questions'] = questions
        
        print(f"🔍 Начинаем раздел {section_id} для пользователя {user_id}")
        print(f"🔍 Загружено вопросов: {len(questions)}")
        
        # Показываем первый вопрос раздела
        await self.show_question(update, context, user_id)
    
    async def show_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Показывает текущий вопрос"""
        session = self.user_sessions.get(user_id)
        if not session:
            await self.restart_survey(update, context)
            return
        
        current_index = session['current_question']
        questions = session['current_questions']
        section_id = session['current_section']
        section_config = config.SECTIONS_CONFIG[section_id]
        
        if current_index >= len(questions):
            await self.complete_section(update, context, user_id)
            return
        
        question = questions[current_index]
        
        # Создаем клавиатуру с вариантами ответов
        keyboard = []
        for option in question['options']:
            keyboard.append([InlineKeyboardButton(
                option['text'], 
                callback_data=f"answer_{section_id}_{question['question_id']}_{option['value']}"
            )])
        
        # Добавляем кнопку возврата
     #   keyboard.append([InlineKeyboardButton("⬅️ Назад к разделам", callback_data="back_to_sections")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        progress = f"{current_index + 1}/{len(questions)}"
        text = f"📝 *{section_config['name']}* | Вопрос {progress}\n\n"
        text += f"{question['question']}"
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    
    async def handle_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает ответ на вопрос"""
        if not update.callback_query:
            return
            
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        callback_data = query.data.replace("answer_", "")
        
        parts = callback_data.split("_")
        if len(parts) < 3:
            await query.edit_message_text("❌ Ошибка обработки ответа")
            return
        
        section_id = parts[0]
        answer_value = float(parts[2:][1])  # значение ответа
        
        print(f"🔍 Ответ: секция={section_id}, значение={answer_value}")
        
        session = self.user_sessions.get(user_id)
        if session and session['current_section'] == section_id:
            current_index = session['current_question']
            
            # 🔥 ИНИЦИАЛИЗИРУЕМ СПИСОК ДЛЯ СЕКЦИИ ЕСЛИ НЕТ
            if section_id not in session['answers']:
                session['answers'][section_id] = []
            
            # 🔥 ДОБАВЛЯЕМ ОТВЕТ В СПИСОК ПО ИНДЕКСУ
            # Если список короче текущего индекса - заполняем нулями
            while len(session['answers'][section_id]) <= current_index:
                session['answers'][section_id].append(0.0)
            
            session['answers'][section_id][current_index] = answer_value
            session['current_question'] += 1
            
            print(f"💾 Ответы для {section_id}: {session['answers'][section_id]}")
            
            await self.show_question(update, context, user_id)
    async def complete_section(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Завершает раздел и показывает результаты"""
        session = self.user_sessions.get(user_id)
        if not session:
            await self.restart_survey(update, context)
            return
        
        section_id = session['current_section']
        section_config = config.SECTIONS_CONFIG[section_id]
        
        # Сохраняем ответы раздела
        session['section_answers'][section_id] = session['answers'].copy()
        session['completed_sections'].append(section_id)
        print(session)
        print("session внутри complete section")
        # Рассчитываем баллы для раздела
        if section_id in session['answers']:
         section_score = sum(session['answers'][section_id])
        else:
            section_score = 0.0
        print("section_score")
        print(section_score)
        # 🔥 СОХРАНЯЕМ ТОЛЬКО ЧИСЛО (без answers)
        db.save_section_result(user_id, section_id, section_score)  # ⬅️ Убрали session['answers']
        
        # Показываем результаты раздела
        completed_count = len(session['completed_sections'])
        total_sections = len(self.sections_order)
        
        text = f"✅ *{section_config['name']} - завершено!*\n\n"
        text +="благодарим за прохождение этого раздела! Для получения рекомендаций пройдите следующий раздел"
        
        # Переходим к следующему разделу
        session['current_section_index'] += 1
        
        if session['current_section_index'] < len(session['sections_order']):
            next_section_id = session['sections_order'][session['current_section_index']]
            next_section_config = config.SECTIONS_CONFIG[next_section_id]
            
            text += f"\n\n➡️ Следующий раздел: *{next_section_config['name']}*"
            
            keyboard = [
                [InlineKeyboardButton(f"📋 Перейти к {next_section_config['name']}", 
                                    callback_data=f"start_section_{next_section_id}")],
                [InlineKeyboardButton("⬅️ В главное меню", callback_data="back_to_main")]
            ]
        else:
            # Все разделы завершены
            keyboard = [
                [InlineKeyboardButton("🎯 Завершить диагностику", callback_data="complete_all_sections")],
                [InlineKeyboardButton("⬅️ В главное меню", callback_data="back_to_main")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def skip_section(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Пропускает раздел"""
        if not update.callback_query:
            return
            
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        section_id = query.data.replace("skip_section_", "")
        
        session = self.user_sessions.get(user_id)
        if not session:
            await self.restart_survey(update, context)
            return
        
        # Помечаем раздел как пропущенный
        session['completed_sections'].append(section_id)
        session['current_section_index'] += 1
        
        # Переходим к следующему разделу или завершаем
        if session['current_section_index'] < len(session['sections_order']):
            await self.show_section_intro(update, context, user_id)
        else:
            await self.complete_all_sections(update, context, user_id)
    
    # survey_handlers.py
    async def complete_all_sections(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int = None):
        """Завершает все разделы и показывает общие результаты"""
        if not user_id:
            if update.callback_query:
                user_id = update.callback_query.from_user.id
            else:
                user_id = update.effective_user.id
        
        session = self.user_sessions.get(user_id)
        if not session:
            await self.restart_survey(update, context)
            return
        
        # Анализируем результаты всех разделов
        section_scores = {}
        for section_id in session['completed_sections']:
            if section_id in session['section_answers']:
                section_scores[section_id] = self.calculate_section_score(
                    session['section_answers'][section_id], section_id
                )
        
        # Определяем приоритетные разделы для рекомендаций
        priority_sections = self.analyze_priority_sections(section_scores)
        print("🔍 внутри complete_all_sections")
        
        # 🔥 СОХРАНЕНИЕ: Используем парную систему если пользователь в паре
        from database_couples import DatabaseCouples
        db_couples = DatabaseCouples()
        
        # Проверяем есть ли пара
        partner_id = db_couples.get_partner_id(user_id)
        
        if partner_id:
            # 🔥 СОХРАНЯЕМ В ПАРНУЮ СИСТЕМУ
            print(f"🔍 Пользователь в паре, сохраняем через парную систему")
            print("session['section_answers']")
            print(session['section_answers'])
            ##
            # Сохраняем индивидуальные результаты
            success = db_couples.save_individual_results(user_id, session['section_answers'])
           # success =db.save_user_results(user_id)
            print(f"🔍 Результаты сохранены: {success}")
            
            # Проверяем статус партнера и пары
            partner_completed = db_couples.has_completed_survey(partner_id)
            couple_completed = db_couples.has_both_partners_completed_survey(user_id)
            
            print(f"🔍 Статус: user_completed=True, partner_completed={partner_completed}, couple_completed={couple_completed}")
            
            if partner_completed and not couple_completed:
                # 🔥 ОБА ЗАВЕРШИЛИ - ОТМЕЧАЕМ ПАРУ
                db_couples.mark_couple_survey_completed(user_id, partner_id)
                print("🔍 Пара отмечена как завершившая опрос")
                
                # Показываем парные результаты
                await self.show_couple_results(update, context, user_id, partner_id, section_scores)
            else:
                # Ждем партнера или показываем индивидуальные результаты
                await self._show_simple_waiting_message(update, context, user_id, partner_id)
        else:
            # 🔥 ИНДИВИДУАЛЬНЫЙ ПОЛЬЗОВАТЕЛЬ - сохраняем в старую систему
            print("🔍 Индивидуальный пользователь, сохраняем в старую систему")
       #     db.complete_survey(user_id, section_scores, priority_sections)
            await self.show_final_results(update, context, user_id, section_scores, priority_sections)
        
        # Удаляем сессию
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
        
    # def calculate_section_score(self, answers_dict: dict, section_id: str) -> float:
    #     """Рассчитывает сумму баллов для всех ответов в разделе"""
    #     total_score = 0.0
    #     answer_count = 0
        
    #     if not answers_dict:
    #         print(f"⚠️ В секции {section_id} нет ответов")
    #         return total_score
        
    #     print(f"🔍 Расчет баллов для секции {section_id}: {len(answers_dict)} ответов")
        
    #     for question_id, answer_value in answers_dict.items():
    #         try:
    #             # Преобразуем ответ в число
    #             if isinstance(answer_value, (int, float)):
    #                 numeric_value = float(answer_value)
    #             elif isinstance(answer_value, str):
    #                 numeric_value = float(answer_value)
    #             else:
    #                 print(f"⚠️ Неподдерживаемый тип ответа: {type(answer_value)} для вопроса {question_id}")
    #                 continue
                
    #             total_score += numeric_value
    #             answer_count += 1
    #             print(f"   📝 Вопрос {question_id}: {answer_value} → {numeric_value} (сумма: {total_score})")
                
    #         except (ValueError, TypeError) as e:
    #             print(f"⚠️ Ошибка обработки ответа '{answer_value}' для вопроса {question_id}: {e}")
    #             continue
        
    #     print(f"✅ Секция {section_id}: обработано {answer_count}/{len(answers_dict)} ответов, итог = {total_score}")
    #     return total_score
    def calculate_section_score(self, answers_dict: dict, section_id: str) -> float:
        """Рассчитывает сумму баллов для раздела из списка ответов"""
        if section_id not in answers_dict:
            return 0.0
        
        answers_list = answers_dict[section_id]
        total_score = sum(answers_list)
        
        print(f"🔍 Секция {section_id}: ответы {answers_list}, сумма = {total_score}")
        
        return total_score
    def analyze_priority_sections(self, section_scores: dict) -> list:
        """Анализирует приоритетные разделы для рекомендаций"""
        if not section_scores:
            return list(config.SECTIONS_CONFIG.keys())[:3]
        
        # Сортируем разделы по наименьшему баллу (наиболее проблемные)
        sorted_sections = sorted(section_scores.items(), key=lambda x: x[1])
        
        # Возвращаем 3 самых проблемных раздела
        return [section_id for section_id, score in sorted_sections[:3]]
    
    async def show_survey_completed(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает что опросник уже пройден"""
        user_id = update.effective_user.id
        
        text = "✅ *Вы уже прошли опросник*\n\n"
        
        if db.is_subscription_active(user_id):
            text += "💎 У вас есть активная подписка, вы можете просмотреть свои рекомендации."
            keyboard = [
                [InlineKeyboardButton("📊 Мои рекомендации", callback_data="show_recommendations")],
                [InlineKeyboardButton("👤 Профиль", callback_data="my_profile")]
            ]
        else:
            text += "💡 Для доступа к персонализированным рекомендациям необходима подписка."
            keyboard = [
                [InlineKeyboardButton("💳 Купить подписку", callback_data="buy_subscription")],
                [InlineKeyboardButton("👤 Профиль", callback_data="my_profile")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def restart_survey(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Перезапускает опросник"""
        user_id = update.effective_user.id
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
        
        await self.start_survey(update, context)
    
    async def back_to_sections(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Возвращает к списку разделов"""
        if not update.callback_query:
            return
            
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        await self.show_section_intro(update, context, user_id)
    
    async def _handle_section_error(self, update: Update, section_name: str):
        """Обрабатывает ошибку загрузки раздела"""
        text = f"❌ *Ошибка загрузки раздела*\n\n"
        text += f"Раздел '{section_name}' временно недоступен.\n"
        text += "Пожалуйста, попробуйте позже или перейдите к следующему разделу."
        
        keyboard = [[InlineKeyboardButton("⬅️ В главное меню", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')


        # В класс Database добавляем следующие методы:

    def get_section_priority(self, user_id: int) -> str:
        """Получает приоритетный раздел пользователя"""
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
            return list(config.SECTIONS_CONFIG.keys())[:3]
        except Exception as e:
            print(f"❌ Ошибка получения приоритетных разделов: {e}")
            return list(config.SECTIONS_CONFIG.keys())[:3]

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
    async def _show_simple_waiting_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, partner_id: int):
        """Простое сообщение об ожидании партнера"""
        from database_couples import DatabaseCouples
        db_couples = DatabaseCouples()
        
        partner_info = db_couples.get_user_info(partner_id)
        partner_name = partner_info.get('first_name', 'Партнер') if partner_info else 'Партнер'
        
        text = f"✅ *Вы завершили опрос!*\n\n"
        text += f"⏳ Ожидаем, когда {partner_name} также завершит диагностику.\n"
        text += "Вы получите уведомление, когда оба будут готовы."
        
        keyboard = [
            [InlineKeyboardButton("👫 Статус пары", callback_data="couple_profile")],
            [InlineKeyboardButton("⬅️ Главное меню", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_couple_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                user1_id: int, user2_id: int, user1_section_scores: dict):
        """Показывает результаты для пары (сумма баллов обоих пользователей)"""
        from database_couples import DatabaseCouples
        db_couples = DatabaseCouples()
        
        partner_info = db_couples.get_user_info(user2_id)
        partner_name = partner_info.get('first_name', 'Партнер') if partner_info else 'Партнер'
        
        # 🔥 ПОЛУЧАЕМ РЕЗУЛЬТАТЫ ВТОРОГО ПОЛЬЗОВАТЕЛЯ
        user2_results = db_couples.get_user_results(user2_id)
        user1_results = db_couples.get_user_results(user1_id)
        print(f"🔍 Результаты пользователя 2 ({user2_id}): {user2_results}")
        print(f"🔍 Результаты пользователя 1 ({user1_id}): {user1_results}")
        # 🔥 РАССЧИТЫВАЕМ ОБЩИЕ РЕЗУЛЬТАТЫ ПАРЫ
        couple_section_scores = self.calculate_couple_scores(user1_results, user2_results)
        print(f"🔍 Общие результаты пары: {couple_section_scores}")
        
        text = f"👫 *Парные результаты опросника*\n\n"
        text += f"💑 *Вы + {partner_name}*\n\n"
        text += "🎉 Оба партнера завершили опрос!\n\n"
        text += "📊 *Общие результаты пары:*\n"
        
        # Показываем результаты по разделам (сумма обоих пользователей)
        for section_id, couple_score in list(couple_section_scores.items())[:7]:
            section_config = config.SECTIONS_CONFIG.get(section_id, {})
            section_name = section_config.get('name', section_id)
            
            # 🔥 МАКСИМАЛЬНЫЙ БАЛЛ ДЛЯ ПАРЫ = 2 пользователя × 15 баллов каждый
            max_score_couple = 30  # 15 × 2
            percentage = (couple_score / max_score_couple) * 100 if max_score_couple > 0 else 0
            
            # Эмодзи в зависимости от процента
            if percentage >= 80:
                emoji = "🟢"
            elif percentage >= 60:
                emoji = "🟡" 
            elif percentage >= 40:
                emoji = "🟠"
            else:
                emoji = "🔴"
                
            text += f"{emoji} {section_name}: {couple_score}/{max_score_couple} ({percentage:.0f}%)\n"
        
        text += "\n💡 Теперь доступны парные рекомендации!"
        
        keyboard = [
            [InlineKeyboardButton("💫 Получить рекомендации", callback_data="show_recommendations")],
           # [InlineKeyboardButton("👫 Профиль пары", callback_data="couple_profile")],
            [InlineKeyboardButton("⬅️ Главное меню", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем обоим пользователям
        for user_id in [user1_id, user2_id]:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                print(f"✅ Парные результаты отправлены пользователю {user_id}")
            except Exception as e:
                print(f"❌ Не удалось отправить результаты {user_id}: {e}")

    # def calculate_couple_scores(self, user1_section_scores: dict, user2_results: dict) -> dict:
    #     """Рассчитывает общие баллы пары по разделам"""
    #     couple_scores = {}
        
    #     # 🔥 СКЛАДЫВАЕМ БАЛЛЫ ОБОИХ ПОЛЬЗОВАТЕЛЕЙ ПО КАЖДОЙ СЕКЦИИ
    #     all_sections = set(user1_section_scores.keys()) | set(user2_results.keys())
        
    #     for section_id in all_sections:
    #         user1_score = user1_section_scores.get(section_id, 0)
            
    #         # 🔥 РАССЧИТЫВАЕМ БАЛЛЫ ВТОРОГО ПОЛЬЗОВАТЕЛЯ ИЗ ЕГО ОТВЕТОВ
    #         user2_section_answers = user2_results.get(section_id, [])
    #         user2_score = sum(user2_section_answers) if user2_section_answers else 0
            
    #         # Суммируем баллы обоих пользователей
    #         couple_score = user1_score + user2_score
    #         couple_scores[section_id] = couple_score
            
    #         print(f"🔍 Раздел {section_id}: user1={user1_score}, user2={user2_score}, пара={couple_score}")
    
    #     return couple_scores
    # def calculate_couple_scores(self, user1_section_scores: dict, user2_results: dict) -> dict:
    #     """Рассчитывает общие баллы пары по разделам"""
    #     couple_scores = {}
        
    #     # 🔥 СКЛАДЫВАЕМ БАЛЛЫ ОБОИХ ПОЛЬЗОВАТЕЛЕЙ ПО КАЖДОЙ СЕКЦИИ
    #     all_sections = set(user1_section_scores.keys()) | set(user2_results.keys())
        
    #     for section_id in all_sections:
    #         user1_score = user1_section_scores.get(section_id, 0)
            
    #         # 🔥 РАССЧИТЫВАЕМ БАЛЛЫ ВТОРОГО ПОЛЬЗОВАТЕЛЯ ИЗ ЕГО ОТВЕТОВ
    #         user2_section_answers = user2_results.get(section_id, [])
    #         print()
    #         # 🔥 ИСПРАВЛЕНИЕ: Конвертируем все ответы в числа перед суммированием
    #         user2_score = 0
    #         if user2_section_answers:
    #             try:
    #                 # Конвертируем каждый ответ в число и суммируем
    #                 user2_score = sum(int(answer) for answer in user2_section_answers)
    #             except (ValueError, TypeError) as e:
    #                 print(f"⚠️ Ошибка конвертации ответов для раздела {section_id}: {e}")
    #                 print(f"Ответы: {user2_section_answers}")
    #                 user2_score = 0
            
    #         # Суммируем баллы обоих пользователей
    #         couple_score = user1_score + user2_score
    #         couple_scores[section_id] = couple_score
            
    #         print(f"🔍 Раздел {section_id}: user1={user1_score}, user2={user2_score}, пара={couple_score}")

    #     return couple_scores
    def calculate_couple_scores(self, user1_results: dict, user2_results: dict) -> dict:
        """Рассчитывает общие баллы пары по разделам"""
        couple_scores = {}
        
        all_sections = set(user1_results.keys()) | set(user2_results.keys())
        
        for section_id in all_sections:
            # 🔥 ПРЕОБРАЗУЕМ RESULTS В ЧИСЛОВЫЕ БАЛЛЫ
            user1_score_data = user1_results.get(section_id, {})
            user2_score_data = user2_results.get(section_id, {})
            print(user1_results.get(section_id, {}))
            # 🔥 ВЫЗЫВАЕМ ФУНКЦИЮ ДЛЯ РАСЧЕТА БАЛЛОВ
            user1_score = self._calculate_user_section_score(user1_score_data, "User1", section_id)
            user2_score = self._calculate_user_section_score(user2_score_data, "User2", section_id)
            
            print(f"🔍 Раздел {section_id}: user1_data={user1_score_data}, user2_data={user2_score_data}")
            print(f"🔍 Раздел {section_id}: user1_score={user1_score}, user2_score={user2_score}")
            
            couple_score = user1_score + user2_score
            couple_scores[section_id] = couple_score
            print(f"✅ Раздел {section_id}: общий балл пары = {couple_score}")
            print(f"📊 Раздел {section_id}: user1={user1_score}, user2={user2_score}, пара={couple_score}")
        print(couple_scores)
        return couple_scores

    def _calculate_user_section_score(self, section_data, user_label: str, section_id: str) -> int:
        """Рассчитывает баллы пользователя для конкретного раздела"""
        total_score = 0
        
        # Если данные пустые
        if not section_data:
            print(f"🔍 {user_label}: нет данных для раздела {section_id}")
            return total_score
        
        # Если уже число - возвращаем как есть
        if isinstance(section_data, (int, float)):
            print(f"🔍 {user_label}: готовый балл {section_data} для раздела {section_id}")
            return int(section_data)
        
        # 🔥 ЕСЛИ ЭТО СПИСОК - СУММИРУЕМ ВСЕ ЭЛЕМЕНТЫ
        if isinstance(section_data, list):
            try:
                total_score = sum(float(x) for x in section_data)
                print(f"🔍 {user_label}: список {section_data} → сумма {total_score} для раздела {section_id}")
                return int(total_score)
            except (ValueError, TypeError) as e:
                print(f"⚠️ {user_label}: ошибка обработки списка {section_data}: {e}")
                return 0
        
        # Если это словарь - обрабатываем значения
        if isinstance(section_data, dict):
            try:
                for key, value in section_data.items():
                    if isinstance(value, (int, float)):
                        total_score += value
                    elif isinstance(value, str) and self._is_numeric(value):
                        total_score += float(value)
                    # 🔥 ДОБАВЛЯЕМ ОБРАБОТКУ СПИСКОВ В СЛОВАРЕ
                    elif isinstance(value, list):
                        total_score += sum(float(x) for x in value)
                    else:
                        print(f"⚠️ {user_label}: неподдерживаемый формат данных: {value}")
                
                print(f"🔍 {user_label}: словарь {section_data} → сумма {total_score} для раздела {section_id}")
                return int(total_score)
                        
            except (ValueError, TypeError) as e:
                print(f"⚠️ Ошибка обработки данных {user_label} для раздела {section_id}: {e}")
                return 0
        
        print(f"⚠️ {user_label}: неподдерживаемый тип данных {type(section_data)} для раздела {section_id}")
        return 0
    # Глобальный экземпляр менеджера опросников

   


survey_manager = AdvancedSurveyManager()


async def create_invite_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создает ссылку-приглашение"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # Проверяем, нет ли уже партнера
    if db.has_partner(user_id):
        await query.edit_message_text("❌ У вас уже есть партнер.")
        return
    
    # Генерируем ссылку
    invite_link = couple_manager.generate_invite_link(user_id)
    
    text = "👫 *Приглашение партнера*\n\n"
    text += "Отправьте эту ссылку вашему партнеру:\n\n"
    text += f"`{invite_link}`\n\n"
    text += "📋 *Инструкция:*\n"
    text += "1. Отправьте ссылку партнеру\n"
    text += "2. Партнер должен перейти по ссылке\n"
    text += "3. Он подтвердит приглашение в боте\n"
    text += "4. Вы получите уведомление о создании пары\n\n"
    text += "⏳ Ссылка действительна 24 часа"
    
    keyboard = [
        [InlineKeyboardButton("⬅️ Назад", callback_data="couple_menu")],
        [InlineKeyboardButton("📤 Поделиться ссылкой", 
                           url=f"https://t.me/share/url?url={invite_link}&text=Присоединяйся%20ко%20мне%20в%20боте%20для%20работы%20над%20отношениями!")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

# Обработчики callback-запросов
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает callback-запросы"""
    query = update.callback_query
    data = query.data
    
    if data.startswith('accept_invite_'):
        token = data.replace('accept_invite_', '')
        await couple_manager.accept_invite(update, context, token)
    elif data == 'couple_menu':
        await show_couple_menu(update, context)
    elif data == 'create_invite_link':
        await create_invite_link(update, context)
    elif data == 'start_couple_survey':
        await couple_survey_manager.start_couple_survey(update, context)

# survey_handlers.py


async def show_individual_results_with_partner_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                                    user_id: int, partner_id: int, section_scores: dict):
    """Показывает индивидуальные результаты со статусом партнера"""
    from database_couples import DatabaseCouples
    db_couples = DatabaseCouples()
    
    partner_info = db_couples.get_user_info(partner_id)
    partner_name = partner_info.get('first_name', 'Партнер') if partner_info else 'Партнер'
    
    text = f"✅ *Вы завершили опрос!*\n\n"
    text += f"👫 Ожидаем завершения {partner_name}\n\n"
    text += "📊 *Ваши результаты:*\n"
    
    # Показываем топ-3 раздела
    top_sections = sorted(section_scores.items(), key=lambda x: x[1], reverse=True)[:3]
    
    for section_id, score in top_sections:
        section_config = config.SECTIONS_CONFIG.get(section_id, {})
        section_name = section_config.get('name', section_id)
        max_score = 10
        percentage = (score / max_score) * 100 if max_score > 0 else 0
        
        text += f"• {section_name}: {score}/{max_score} ({percentage:.0f}%)\n"
    
    text += f"\n⏳ Как только {partner_name} завершит опрос, вы получите парные рекомендации!"
    
    keyboard = [
        [InlineKeyboardButton("👫 Статус пары", callback_data="couple_profile")],
        [InlineKeyboardButton("⬅️ Главное меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
async def test_priority_calculation(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Тестовый хэндлер для проверки расчета приоритетов"""
        user_id = update.effective_user.id
        
        # Получаем ID партнера
        from database_couples import DatabaseCouples
        db_couples = DatabaseCouples()
        partner_id = db_couples.get_partner_id(user_id)
        
        if not partner_id:
            await update.message.reply_text("❌ У вас нет партнера для тестирования")
            return
        
        await update.message.reply_text("🔍 Запускаю тест расчета приоритетов...")
        
        # Вызываем функцию расчета приоритетов
        db_couples.mark_couple_survey_completed(user_id, partner_id)
        priority_sections = db_couples._calculate_priority_sections(user_id, partner_id)
        
        # Формируем результат
        if priority_sections:
            result_text = "✅ **Результаты расчета приоритетов:**\n\n"
            for i, section_id in enumerate(priority_sections, 1):
                section_name = config.SECTIONS_CONFIG.get(section_id, {}).get('name', section_id)
                result_text += f"{i}. {section_name} (`{section_id}`)\n"
            
            result_text += f"\n📊 Всего приоритетов: {len(priority_sections)}"
        else:
            result_text = "❌ Не удалось рассчитать приоритеты"
        
        await update.message.reply_text(result_text)

async def quick_test_priority(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Быстрый тест расчета приоритетов"""
        user_id = update.effective_user.id
        
        from database_couples import DatabaseCouples
        db_couples = DatabaseCouples()
        
        # Тестируем на себе (если нет партнера)
        partner_id = db_couples.get_partner_id(user_id) or user_id
        
        print("🔍 === ЗАПУСК БЫСТРОГО ТЕСТА ===")
        priority_sections = db_couples._calculate_priority_sections(user_id, partner_id)
        print("🔍 === ЗАВЕРШЕНИЕ БЫСТРОГО ТЕСТА ===")
        
        await update.message.reply_text(f"🔍 Приоритеты: {priority_sections}")


