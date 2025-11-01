from pymongo import MongoClient
import json
import os

def import_json_to_collection():
    # Подключение к MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client['family_bot']
    
    print("Доступные JSON файлы в текущей директории:")
    
    # Показываем все JSON файлы
    json_files = [f for f in os.listdir('.') if f.endswith('.json')]
    
    if not json_files:
        print("JSON файлы не найдены в текущей директории!")
        return
    
    for i, filename in enumerate(json_files, 1):
        print(f"{i}. {filename}")
    
    # Выбор файла
    try:
        file_choice = int(input("\nВыберите номер файла: ")) - 1
        if file_choice < 0 or file_choice >= len(json_files):
            print("Неверный выбор!")
            return
        
        selected_file = json_files[file_choice]
        print(f"Выбран файл: {selected_file}")
        
    except ValueError:
        print("Введите корректный номер!")
        return
    
    # Загрузка JSON данных
    try:
        with open(selected_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
        print(f"JSON файл успешно загружен")
    except Exception as e:
        print(f"Ошибка загрузки JSON: {e}")
        return
    
    # Показываем существующие коллекции
    print("\nСуществующие коллекции в базе 'family_bot':")
    existing_collections = db.list_collection_names()
    for i, coll_name in enumerate(existing_collections, 1):
        coll = db[coll_name]
        print(f"{i}. {coll_name} - {coll.count_documents({})} документов")
    
    print("\nВы можете:")
    print("1. Выбрать существующую коллекцию")
    print("2. Создать новую коллекцию")
    
    try:
        choice = input("Введите 1 или 2: ")
        
        if choice == '1':
            # Выбор существующей коллекции
            coll_choice = int(input("Введите номер коллекции: ")) - 1
            if 0 <= coll_choice < len(existing_collections):
                collection_name = existing_collections[coll_choice]
            else:
                print("Неверный выбор!")
                return
                
        elif choice == '2':
            # Создание новой коллекции
            collection_name = input("Введите название новой коллекции: ").strip()
            if not collection_name:
                print("Название коллекции не может быть пустым!")
                return
        else:
            print("Неверный выбор!")
            return
            
    except ValueError:
        print("Введите корректный номер!")
        return
    
    # Импорт данных
    collection = db[collection_name]
    
    try:
        # Если данные - массив, вставляем все документы
        if isinstance(data, list):
            result = collection.insert_many(data)
            print(f"Успешно добавлено {len(result.inserted_ids)} документов в коллекцию '{collection_name}'")
        # Если данные - объект, вставляем один документ
        elif isinstance(data, dict):
            result = collection.insert_one(data)
            print(f"Успешно добавлен 1 документ в коллекцию '{collection_name}'")
        else:
            print("Неподдерживаемый формат JSON данных")
            return
            
        # Показываем статистику после импорта
        print(f"\nТекущее состояние коллекции '{collection_name}':")
        print(f"Количество документов: {collection.count_documents({})}")
        
    except Exception as e:
        print(f"Ошибка при импорте данных: {e}")
    
    # Закрываем соединение
    client.close()

if __name__ == "__main__":
    import_json_to_collection()