from pymongo import MongoClient
from typing import List, Dict, Any
from bson.objectid import ObjectId
from datetime import datetime
import logging
import config


logger = logging.getLogger(__name__)




class Database_lib:
    def __init__(self):
        self.client = MongoClient(config.MONGO_URI)
        self.db = self.client.family_bot
#        self.mental_exercises = self.db['mental_exercises']
#    # Методы для работы с упражнениями
#     def get_exercises_for_sector(self, sphere: str, limit: int = 3):
#         """Получить упражнения для указанной сферы"""
#         try:
#             result = list(self.db.excersises1.aggregate([
#                 {"$match": {"sector": sphere}},
#                 {"$unwind": "$content"},
#                 {"$sample": {"size": 1}}
#             ]))
#             return result[0]['content'] if result else None
#         except Exception as e:
#             logger.error(f"Ошибка получения упражнения: {e}")
#             return None
        
#     def get_cinema_for_sector(self, sphere: str, limit: int = 3):
#         """Получить упражнения для указанной сферы"""
#         try:
#             result = list(self.db.cinema.aggregate([
#                 {"$match": {"sector": sphere}},
#                 {"$unwind": "$films"},
#                 {"$sample": {"size": 1}}
#             ]))
#             return result[0]['films']  if result else None
#         except Exception as e:
#             logger.error(f"Ошибка получения упражнения: {e}")
#             return None
        
#     def get_lit_for_sector(self, sphere: str, limit: int = 3):
#         """Получить упражнения для указанной сферы"""
#         try:
#             result = list(self.db.literature.aggregate([
#                 {"$match": {"sector": sphere}},
#                 {"$unwind": "$content"},
#                 {"$sample": {"size": 1}}
#             ]))
#             return result[0]['content']  if result else None
#         except Exception as e:
#             logger.error(f"Ошибка получения упражнения: {e}")
#             return None
        
#         #return self.db.excersises.find({"sector": sphere})
    
    def get_libido_articles(self) -> List[Dict[str, Any]]:
        """Получить все статьи модуля либидо"""
        print(list(self.db.libido_articles.find().sort("order", 1)))
        return list(self.db.libido_articles.find().sort("order", 1))
    

    def get_libido_exercise(self, day):
        """Получить упражнение для конкретного дня"""
        # Конвертируем day в int, если нужно
        day_int = int(day)
        exercise = self.db.libido_exercises.find_one({"day": day_int})
        print(exercise)
        return exercise

    
    
    def get_libido_questionnaires(self) -> List[Dict[str, Any]]:
        """Получить все опросники модуля либидо"""
        try:
            return list(self.db.libido_questionnaires.find({}))
        except Exception as e:
            print(f"Error getting libido questionnaires: {e}")
            return []
        
    

    def get_libido_questionnaire(self, questionnaire_id: str):
        """Получить конкретный опросник по ID"""
        try:
            return self.db.libido_questionnaires.find_one({"_id": ObjectId(questionnaire_id)})
        except Exception as e:
            print(f"Error getting libido questionnaire: {e}")
            return None
        
            
    
    def get_exercise_by_day_and_category(self, day, category=None):
        """Получить упражнение по дню и категории"""
        query = {"day": day}
        if category:
            query["category"] = category
        return self.db.mental_exercises.find_one(query)
    
    def get_exercises_by_category(self, category):
        """Получить все упражнения определенной категории"""
        return list(self.db.mental_exercises.find({"category": category}))
    
    def get_all_exercises(self):
        """Получить все упражнения"""
        return list(self.db.mental_exercises.find())
    
    def get_exercise_count(self):
        """Получить количество упражнений в базе"""
        return self.db.mental_exercises.count_documents({})
    
    def get_exercise_details(self, day, category=None):
        """Получить детальную информацию об упражнении по дню и категории"""
        try:
            query = {"day": int(day)}
            if category:
                query["category"] = category
            return self.db.mental_exercises.find_one(query)
        except Exception as e:
            print(f"Ошибка при получении деталей упражнения: {e}")
            return None
    def get_exercise_by_day(self, day):
        """Получить упражнение по номеру дня (любой категории)"""
        try:
            return self.db.mental_exercises.find_one({"day": int(day)})
        except Exception as e:
            print(f"Ошибка при поиске упражнения дня {day}: {e}")
            return None

    def get_total_days(self):
        """Получить общее количество дней с упражнениями"""
        try:
            days = self.db.mental_exercises.distinct("day")
            return len(days)
        except Exception as e:
            print(f"Ошибка при получении количества дней: {e}")
            return 0

    def get_all_days(self):
        """Получить список всех дней с упражнениями"""
        try:
            days = self.db.mental_exercises.distinct("day")
            return sorted(days)
        except Exception as e:
            print(f"Ошибка при получении списка дней: {e}")
            return []

    
    
    def close(self):
        """Закрыть соединение с базой данных"""
        self.client.close()