from pymongo import MongoClient
import pprint

def clear_collections():
    # Подключение к MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client['family_bot']
    
    # Коллекции для очистки
    collections_to_clear = ['users', 'user_results', 'couples']
    
    print("Очистка коллекций...")
    
    # Очищаем указанные коллекции
    for collection_name in collections_to_clear:
        if collection_name in db.list_collection_names():
            collection = db[collection_name]
            count_before = collection.count_documents({})
            collection.delete_many({})  # Удаляем все документы
            count_after = collection.count_documents({})
            print(f"Коллекция '{collection_name}': было {count_before} записей, стало {count_after} записей")
        else:
            print(f"Коллекция '{collection_name}' не найдена")
    
    print("\n" + "="*50)
    print("Все коллекции в базе данных 'family_bot':")
    print("="*50)
    
    # Показываем все коллекции в базе
    all_collections = db.list_collection_names()
    for i, collection_name in enumerate(all_collections, 1):
        collection = db[collection_name]
        doc_count = collection.count_documents({})
        print(f"{i}. {collection_name} - {doc_count} документов")
    
    # Закрываем соединение
    client.close()

if __name__ == "__main__":
    clear_collections()