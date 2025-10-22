#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простая авторизация в Wildberries Seller через браузер
"""

import time
import json
import requests
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def manual_browser_auth():
    """Ручная авторизация через браузер"""
    
    phone = "+79264845850"
    
    print("Авторизация в Wildberries Seller через браузер")
    print("=" * 50)
    
    print(f"\n{'='*60}")
    print("ИНСТРУКЦИИ ДЛЯ АВТОРИЗАЦИИ:")
    print("1. Откройте браузер Chrome")
    print("2. Перейдите на https://seller.wildberries.ru/")
    print(f"3. Введите номер телефона: {phone}")
    print("4. Нажмите кнопку 'Отправить код' или 'Получить код'")
    print("5. Введите SMS код, который придет на телефон")
    print("6. Нажмите кнопку 'Войти' или 'Подтвердить'")
    print("7. Дождитесь успешной авторизации")
    print("8. Откройте инструменты разработчика (F12)")
    print("9. Перейдите на вкладку 'Application' или 'Приложение'")
    print("10. В левом меню найдите 'Cookies' -> 'https://seller.wildberries.ru'")
    print("11. Найдите cookie с именем содержащим 'token', 'jwt', 'auth' или 'wb'")
    print("12. Скопируйте значение этого cookie")
    print(f"{'='*60}\n")
    
    token = input("Вставьте скопированный токен: ").strip()
    
    if not token:
        print("Токен не введен")
        return None
    
    print(f"Получен токен: {token[:50]}...")
    
    # Тестируем токен
    return test_token(token)

def test_token(token):
    """Тестирование токена"""
    try:
        logger.info("Тестирование токена...")
        
        # Создаем сессию requests
        session = requests.Session()
        
        # Различные способы использования токена
        auth_methods = [
            {
                'name': 'Bearer Token',
                'headers': {
                    'Authorization': f'Bearer {token}',
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Referer': 'https://seller.wildberries.ru/',
                }
            },
            {
                'name': 'Cookie Token',
                'headers': {
                    'Cookie': f'WBToken={token}; wb_token={token}',
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Referer': 'https://seller.wildberries.ru/',
                }
            },
            {
                'name': 'X-Auth-Token',
                'headers': {
                    'X-Auth-Token': token,
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Referer': 'https://seller.wildberries.ru/',
                }
            }
        ]
        
        # Тестовые API endpoints
        test_endpoints = [
            "https://seller.wildberries.ru/ns/sm/supplier-manager/api/v1/supplier/products",
            "https://seller.wildberries.ru/ns/sm/supplier-manager/api/v1/supplier/info",
            "https://seller.wildberries.ru/api/v1/supplier/products",
        ]
        
        for method in auth_methods:
            print(f"\n{method['name']}:")
            
            session.headers.update(method['headers'])
            success_count = 0
            
            for endpoint in test_endpoints:
                try:
                    response = session.get(endpoint, timeout=10)
                    
                    if response.status_code == 200:
                        print(f"  ✅ {endpoint}: {response.status_code}")
                        success_count += 1
                        
                        try:
                            data = response.json()
                            print(f"    Данные получены: {len(str(data))} символов")
                            
                            # Если это список товаров, показываем количество
                            if isinstance(data, dict) and 'data' in data:
                                if isinstance(data['data'], list):
                                    print(f"    Найдено товаров: {len(data['data'])}")
                                else:
                                    print(f"    Структура данных: {list(data['data'].keys())}")
                        except:
                            print(f"    Ответ: {response.text[:100]}...")
                            
                    elif response.status_code == 401:
                        print(f"  ❌ {endpoint}: {response.status_code} (Unauthorized)")
                    elif response.status_code == 403:
                        print(f"  ⚠️  {endpoint}: {response.status_code} (Forbidden)")
                    elif response.status_code == 404:
                        print(f"  ❓ {endpoint}: {response.status_code} (Not Found)")
                    else:
                        print(f"  ⚠️  {endpoint}: {response.status_code}")
                        
                except Exception as e:
                    print(f"  ❌ {endpoint}: Ошибка - {e}")
            
            if success_count > 0:
                print(f"  🎉 Успешных запросов: {success_count}/{len(test_endpoints)}")
                
                # Сохраняем рабочий токен
                save_token(token, method['name'])
                return token
            else:
                print(f"  😞 Успешных запросов: 0/{len(test_endpoints)}")
        
        print("\n❌ Ни один метод авторизации не сработал")
        return None
        
    except Exception as e:
        logger.error(f"Ошибка при тестировании токена: {e}")
        return None

def save_token(token, method):
    """Сохранение токена в файл"""
    try:
        token_data = {
            'token': token,
            'method': method,
            'timestamp': time.time(),
            'date': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with open('wb_token.json', 'w', encoding='utf-8') as f:
            json.dump(token_data, f, indent=2, ensure_ascii=False)
        
        logger.info("Токен сохранен в файл: wb_token.json")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при сохранении токена: {e}")
        return False

def load_token():
    """Загрузка токена из файла"""
    try:
        with open('wb_token.json', 'r', encoding='utf-8') as f:
            token_data = json.load(f)
        
        token = token_data.get('token')
        method = token_data.get('method', 'Unknown')
        date = token_data.get('date', 'Unknown')
        
        logger.info(f"Токен загружен из файла (метод: {method}, дата: {date})")
        return token
        
    except Exception as e:
        logger.warning(f"Не удалось загрузить токен из файла: {e}")
        return None

def main():
    """Основная функция"""
    print("Wildberries Seller API - Авторизация")
    print("=" * 40)
    
    # Пробуем загрузить существующий токен
    existing_token = load_token()
    
    if existing_token:
        print(f"Найден существующий токен: {existing_token[:50]}...")
        use_existing = input("Использовать существующий токен? (y/n): ").strip().lower()
        
        if use_existing in ['y', 'yes', 'да', 'д']:
            if test_token(existing_token):
                print("✅ Существующий токен работает!")
                return
            else:
                print("❌ Существующий токен не работает")
    
    # Новая авторизация
    token = manual_browser_auth()
    
    if token:
        print("✅ Авторизация успешна!")
        print("Теперь можно использовать парсер с официальным API")
    else:
        print("❌ Авторизация не удалась")

if __name__ == "__main__":
    main()
