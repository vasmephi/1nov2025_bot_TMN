# init_couple_collections.py
import sys
import os
from datetime import datetime

# Добавляем путь для импорта модулей проекта
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database_couples import Database
import config

class CoupleCollectionsInitializer:
    def __init__(self, db: Database):
        self.db = db
    
    def initialize_all_collections(self):
        """Инициализирует все коллекции для парной системы"""
        print("🚀 Начинаем инициализацию коллекций для парной системы...")
        
        try:
            # Проверяем соединение с MongoDB
            self.db.client.admin.command('ping')
            print("✅ Соединение с MongoDB установлено")
            
            # Инициализируем коллекции
            self.init_couples_collection()
            self.init_invites_collection()
            self.init_couple_surveys_collection()
            
            print("🎉 Все коллекции для парной системы инициализированы успешно!")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка инициализации: {e}")
            return False
    
    def init_couples_collection(self):
        """Инициализирует коллекцию пар"""
        try:
            # Создаем индексы для быстрого поиска
            self.db.couples.create_index("couple_id", unique=True)
            self.db.couples.create_index("user1_id")
            self.db.couples.create_index("user2_id")
            self.db.couples.create_index("created_at")
            self.db.couples.create_index("status")
            
            # Составной индекс для поиска пар по пользователям
            self.db.couples.create_index([("user1_id", 1), ("user2_id", 1)])
            
            print("✅ Коллекция 'couples' инициализирована")
            print("   Индексы: couple_id(unique), user1_id, user2_id, created_at, status")
            
        except Exception as e:
            print(f"❌ Ошибка инициализации couples: {e}")
    
    def init_invites_collection(self):
        """Инициализирует коллекцию приглашений"""
        try:
            # Уникальный индекс для токенов
            self.db.invites.create_index("token", unique=True)
            
            # Индекс для поиска по пользователю
            self.db.invites.create_index("user_id")
            
            # TTL индекс - автоматическое удаление просроченных приглашений (24 часа)
            self.db.invites.create_index(
                "expires_at", 
                expireAfterSeconds=0  # Удалять сразу после expires_at
            )
            
            # Индекс для поиска активных приглашений
            self.db.invites.create_index([("user_id", 1), ("used", 1), ("expires_at", 1)])
            
            print("✅ Коллекция 'invites' инициализирована")
            print("   Индексы: token(unique), user_id, expires_at(TTL), composite_index")
            
        except Exception as e:
            print(f"❌ Ошибка инициализации invites: {e}")
    
    def init_couple_surveys_collection(self):
        """Инициализирует коллекцию парных опросников"""
        try:
            # Индекс для поиска по паре
            self.db.couple_surveys.create_index("couple_id")
            
            # Индекс для сортировки по дате завершения
            self.db.couple_surveys.create_index("completed_at")
            
            # Составной индекс для быстрого поиска истории опросников пары
            self.db.couple_surveys.create_index([("couple_id", 1), ("completed_at", -1)])
            
            # Индекс для поиска по версии опросника
            self.db.couple_surveys.create_index("survey_version")
            
            print("✅ Коллекция 'couple_surveys' инициализирована")
            print("   Индексы: couple_id, completed_at, composite_index, survey_version")
            
        except Exception as e:
            print(f"❌ Ошибка инициализации couple_surveys: {e}")
    
    def check_existing_collections(self):
        """Проверяет существующие коллекции и их размер"""
        print("\n📊 Проверка существующих коллекций:")
        
        collections = self.db.db.list_collection_names()
        couple_collections = ['couples', 'invites', 'couple_surveys']
        
        for coll_name in couple_collections:
            if coll_name in collections:
                count = self.db.db[coll_name].count_documents({})
                print(f"   {coll_name}: {count} документов")
            else:
                print(f"   {coll_name}: коллекция не существует")
    
    def create_test_couple(self):
        """Создает тестовую пару для проверки (опционально)"""
        print("\n🧪 Создаем тестовую пару...")
        try:
            # Тестовые ID пользователей
            test_user1 = 100001
            test_user2 = 100002
            
            # Создаем тестовых пользователей если их нет
            if not self.db.users.find_one({"user_id": test_user1}):
                self.db.users.insert_one({
                    "user_id": test_user1,
                    "first_name": "Тест_Пользователь_1",
                    "username": "test_user_1",
                    "created_at": datetime.now()
                })
                print("✅ Создан тестовый пользователь 1")
            
            if not self.db.users.find_one({"user_id": test_user2}):
                self.db.users.insert_one({
                    "user_id": test_user2,
                    "first_name": "Тест_Пользователь_2", 
                    "username": "test_user_2",
                    "created_at": datetime.now()
                })
                print("✅ Создан тестовый пользователь 2")
            
            # Используем метод create_couple из класса Database
            success = self.db.create_couple(test_user1, test_user2)
            if success:
                print("✅ Тестовая пара создана успешно")
            else:
                print("⚠️ Тестовая пара уже существует")
                
        except Exception as e:
            print(f"❌ Ошибка создания тестовой пары: {e}")

def main():
    """Основная функция инициализации"""
    print("=" * 60)
    print("🔄 ИНИЦИАЛИЗАЦИЯ КОЛЛЕКЦИЙ ДЛЯ ПАРНОЙ СИСТЕМЫ")
    print("=" * 60)
    
    # Параметры командной строки
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Использование:")
        print("  python init_couple_collections.py          # Базовая инициализация")
        print("  python init_couple_collections.py --test   # С тестовыми данными")
        print("  python init_couple_collections.py --check  # Только проверка")
        return
    
    only_check = "--check" in sys.argv
    with_test = "--test" in sys.argv

    try:
        # Создаем подключение к базе
        db = Database()
        initializer = CoupleCollectionsInitializer(db)
        
        # Проверяем существующие коллекции
        initializer.check_existing_collections()
        
        if not only_check:
            # Инициализируем коллекции
            success = initializer.initialize_all_collections()
            
            if success and with_test:
                initializer.create_test_couple()
            
            # Финальная проверка
            print("\n" + "=" * 40)
            initializer.check_existing_collections()
            
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()