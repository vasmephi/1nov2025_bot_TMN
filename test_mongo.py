# test_mongo.py
from pymongo import MongoClient

try:
    client = MongoClient('mongodb://localhost:27017/')
    # Попробуйте получить список баз данных
    dbs = client.list_database_names()
    print("✅ Успешное подключение к MongoDB!")
    print("📁 Доступные базы данных:", dbs)
    
    # Создаем тестовую запись
    test_db = client.test_database
    test_collection = test_db.test_collection
    test_collection.insert_one({"test": "data", "status": "working"})
    print("✅ Тестовая запись добавлена!")
    
except Exception as e:
    print("❌ Ошибка подключения:", e)