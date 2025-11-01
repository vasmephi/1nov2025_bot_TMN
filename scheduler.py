from telegram.ext import ContextTypes
from datetime import datetime, time, timedelta
import asyncio
from database import db
import config
from typing import Dict, List

class RecommendationScheduler:
    def __init__(self):
        self.user_schedules: Dict[int, Dict] = {}  # user_id -> schedule_data
        self.default_times = [time(9, 0), time(14, 0), time(19, 0)]  # 9:00, 14:00, 19:00
    
    async def send_scheduled_recommendation(self, context: ContextTypes.DEFAULT_TYPE):
        """Отправляет рекомендацию по расписанию"""
        job = context.job
        user_id = job.data['user_id']
        chat_id = job.data['chat_id']
        print("job.data['chat_id']")
        print(job.data['chat_id'])
        # Проверяем активна ли подписка
        if not db.is_subscription_active(user_id):
            await self.stop_user_schedule(user_id, context.application)
            return
        
        # Получаем следующую рекомендацию
        recommendation = await self.get_next_recommendation(user_id)
        
        if recommendation:
            await context.bot.send_message(
                chat_id=chat_id,
                text=self.format_recommendation(recommendation),
                parse_mode='Markdown'
            )
        else:
            # Рекомендации закончились
            await context.bot.send_message(
                chat_id=chat_id,
                text="🎉 *Вы прочитали все рекомендации!*\n\n"
                     "Пройти опросник заново для получения новых рекомендаций: /survey",
                parse_mode='Markdown'
            )
            await self.stop_user_schedule(user_id, context.application)
    
    async def setup_user_schedule(self, user_id: int, chat_id: int, application, 
                                custom_times: List[time] = None):
        """Настраивает расписание для пользователя"""
        
        # Останавливаем старое расписание
        await self.stop_user_schedule(user_id, application)
        
        # Используем кастомное или стандартное расписание
        times = custom_times or self.default_times
        
        jobs = []
        print("times")
        print(times)
        
        for schedule_time in times:
            # 🔧 КОРРЕКЦИЯ: добавляем 3 часа для московского времени
            msk_time = schedule_time
            utc_time = time(
                (schedule_time.hour - 3) % 24,  # Вычитаем 3 часа для UTC
                schedule_time.minute
            )
            
            print(f"🕒 МСК: {msk_time.strftime('%H:%M')} -> UTC: {utc_time.strftime('%H:%M')}")
            
            job = application.job_queue.run_daily(
                self.send_scheduled_recommendation,
                time=utc_time,  # ✅ Используем UTC время!
                days=tuple(range(7)),  # Все дни недели
                data={
                    'user_id': user_id, 
                    'chat_id': chat_id, 
                    'time': schedule_time,  # Сохраняем оригинальное время для отображения
                    'msk_time': msk_time.strftime('%H:%M'),  # Московское время для пользователя
                    'utc_time': utc_time.strftime('%H:%M')   # UTC время для отладки
                }
            )
            jobs.append(job)
        

        # Сохраняем информацию о расписании
        self.user_schedules[user_id] = {
            'jobs': jobs,
            'times': times,
            'chat_id': chat_id
        }
        
        return len(jobs)
    
    async def stop_user_schedule(self, user_id: int, application):
        """Останавливает расписание пользователя"""
        if user_id in self.user_schedules:
            for job in self.user_schedules[user_id]['jobs']:
                job.schedule_removal()
            del self.user_schedules[user_id]
    
    async def get_next_recommendation(self, user_id: int):
        """Получает следующую рекомендацию с учетом приоритета разделов"""
        priority_sections = db.get_user_priority_sections(user_id)
        
        # Ищем рекомендации в порядке приоритета
        for section_id in priority_sections:
            recommendation = db.get_next_recommendation_by_section(user_id, section_id)
            if recommendation:
                return recommendation
        
        # Если в приоритетных разделах нет рекомендаций, ищем в других
        all_sections = list(config.SECTIONS_CONFIG.keys())
        remaining_sections = [s for s in all_sections if s not in priority_sections]
        
        for section_id in remaining_sections:
            recommendation = db.get_next_recommendation_by_section(user_id, section_id)
            if recommendation:
                return recommendation
        
        return None
    
    def format_recommendation(self, recommendation: Dict) -> str:
        """Форматирует рекомендацию для отправки"""
        section_config = config.SECTIONS_CONFIG.get(recommendation.get('section', 'communication'), {})
        
        text = f"{section_config.get('icon', '💫')} *Рекомендация на сегодня*\n\n"
        text += f"**{recommendation['title']}**\n"
        text += f"🏷️ {recommendation['category']}\n\n"
        text += f"📝 *Описание:* {recommendation['description']}\n\n"
        text += f"**Содержание:**\n{recommendation['content']}\n\n"
        text += f"⏰ *Следующая рекомендация:* завтра в это же время"
        
        return text
    
    def get_user_schedule(self, user_id: int) -> List[time]:
        """Возвращает расписание пользователя"""
        if user_id in self.user_schedules:
            return self.user_schedules[user_id]['times']
        return []
    
    def is_user_scheduled(self, user_id: int) -> bool:
        """Проверяет, есть ли у пользователя активное расписание"""
        return user_id in self.user_schedules

from datetime import datetime, time, timedelta
import asyncio

class ExtendedScheduler:
    def __init__(self):
        self.user_jobs = {}
        self.movie_jobs = {}
        self.book_jobs = {}
    
    async def setup_movie_schedule(self, application):
        """Настраивает расписание для фильмов (каждую пятницу в 20:00)"""
        # Удаляем старые задания
        for job in self.movie_jobs.values():
            job.schedule_removal()
        self.movie_jobs.clear()
        
        # Создаем задание для всех пользователей с активной подпиской
        job = application.job_queue.run_daily(
            self.send_movie_recommendations,
            time(hour=20, minute=0),
            days=(4,)  # 4 = пятница (понедельник=0)
        )
        self.movie_jobs['global'] = job
    
    async def setup_book_schedule(self, application):
        """Настраивает расписание для книг (каждые 21 день)"""
        for job in self.book_jobs.values():
            job.schedule_removal()
        self.book_jobs.clear()
        
        # Запускаем проверку каждые 24 часа
        job = application.job_queue.run_daily(
            self.send_book_recommendations,
            time(hour=9, minute=0)  # Проверяем каждый день в 9:00
        )
        self.book_jobs['global'] = job
    
    async def send_movie_recommendations(self, context: ContextTypes.DEFAULT_TYPE):
        """Отправляет рекомендации фильмов всем подписанным пользователям"""
        from database import db
        
        # Получаем всех пользователей с активной подпиской
        active_users = db.get_active_subscribers()
        
        for user in active_users:
            user_id = user['_id']
            chat_id = user.get('chat_id')
            
            if not chat_id:
                continue
                
            try:
                # Получаем рекомендацию фильма
                movies = db.get_movie_recommendations(user_id, 1)
                if not movies:
                    continue
                
                movie = movies[0]
                
                # Форматируем сообщение
                text = "🎬 *Рекомендация фильма на выходные!*\n\n"
                text += f"*{movie['title']}* ({movie.get('year', 'N/A')})\n\n"
                text += f"📝 *Описание:* {movie['description']}\n\n"
                
                if movie.get('genre'):
                    text += f"🎭 *Жанр:* {movie['genre']}\n"
                if movie.get('duration'):
                    text += f"⏱ *Продолжительность:* {movie['duration']}\n"
                if movie.get('why_recommend'):
                    text += f"💡 *Почему смотреть:* {movie['why_recommend']}\n"
                
                # Отправляем сообщение
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode='Markdown'
                )
                
                # Обновляем дату отправки
                db.update_last_movie_sent(user_id)
                
                # Небольшая задержка между отправками
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"Ошибка отправки фильма пользователю {user_id}: {e}")
    
    async def send_book_recommendations(self, context: ContextTypes.DEFAULT_TYPE):
        """Отправляет рекомендации книг (каждые 21 день)"""
        from database import db
        from datetime import datetime, timedelta
        
        active_users = db.get_active_subscribers()
        
        for user in active_users:
            user_id = user['_id']
            chat_id = user.get('chat_id')
            
            if not chat_id:
                continue
            
            # Проверяем, прошло ли 21 день с последней отправки
            last_book_sent = db.get_user_last_book_sent(user_id)
            should_send = False
            
            if not last_book_sent:
                # Если никогда не отправляли - отправляем
                should_send = True
            else:
                # Проверяем, прошло ли 21 день
                days_passed = (datetime.now() - last_book_sent).days
                if days_passed >= 21:
                    should_send = True
            
            if should_send:
                try:
                    # Получаем рекомендацию книги
                    books = db.get_book_recommendations(user_id, 1)
                    if not books:
                        continue
                    
                    book = books[0]
                    
                    # Форматируем сообщение
                    text = "📚 *Новая рекомендация книги!*\n\n"
                    text += f"*{book['title']}* - {book.get('author', 'Неизвестный автор')}\n\n"
                    text += f"📝 *Описание:* {book['description']}\n\n"
                    
                    if book.get('pages'):
                        text += f"📖 *Страниц:* {book['pages']}\n"
                    if book.get('genre'):
                        text += f"🏷️ *Жанр:* {book['genre']}\n"
                    if book.get('why_recommend'):
                        text += f"💡 *Почему читать:* {book['why_recommend']}\n"
                    
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=text,
                        parse_mode='Markdown'
                    )
                    
                    # Обновляем дату отправки
                    db.update_last_book_sent(user_id)
                    
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    print(f"Ошибка отправки книги пользователю {user_id}: {e}")

# Создаем экземпляр расширенного планировщика
extended_scheduler = ExtendedScheduler()

# Глобальный экземпляр планировщика
scheduler = RecommendationScheduler()