#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест существующего токена с различными заголовками
"""

import requests
import json
import base64
import time

def decode_jwt_token(token):
    """Декодирование JWT токена"""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        payload = parts[1]
        payload += '=' * (4 - len(payload) % 4)
        
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except Exception as e:
        print(f"Ошибка декодирования: {e}")
        return None

def test_existing_token():
    """Тест существующего токена"""
    
    # Существующий токен
    jwt_token = "eyJhbGciOiJFUzI1NiIsImtpZCI6IjIwMjUwOTA0djEiLCJ0eXAiOiJKV1QifQ.eyJlbnQiOjEsImV4cCI6MTc3NjkwNTgyNywiaWQiOiIwMTlhMGJmZS05ZThjLTdjMDgtOGRkZC0yNTJlMDFhN2U3ZmUiLCJpaWQiOjMzMzkzMDI5LCJvaWQiOjIxNDE3NiwicyI6MjQsInNpZCI6ImIzYzNjM2M3LTYwYmEtNGU2OS04ZTAxLTI4YTE5MzU5MTZiOCIsInQiOmZhbHNlLCJ1aWQiOjMzMzkzMDI5fQ.nQrQCZttlSk4N4WX1sd5UPYvk5Ext-PvV7hVpAqWj7Z-NuHC_q0CjsiG9i4DAO4QAsxasqhSDXfXlugadRPe3w"
    
    print("Анализ существующего токена")
    print("=" * 40)
    
    # Анализируем токен
    payload = decode_jwt_token(jwt_token)
    if payload:
        print("Содержимое токена:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        
        # Проверяем срок действия
        exp = payload.get('exp', 0)
        current_time = int(time.time())
        
        if exp > current_time:
            print(f"\nТокен действителен до: {time.ctime(exp)}")
            print("Токен валиден!")
        else:
            print(f"\nТокен истек: {time.ctime(exp)}")
            print("Токен невалиден!")
            return
    
    print("\nТест различных способов использования токена")
    print("=" * 50)
    
    # Различные варианты использования токена
    auth_methods = [
        {
            'name': 'Bearer в Authorization',
            'headers': {
                'Authorization': f'Bearer {jwt_token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
        },
        {
            'name': 'JWT в Authorization',
            'headers': {
                'Authorization': f'JWT {jwt_token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
        },
        {
            'name': 'Token в заголовке',
            'headers': {
                'Token': jwt_token,
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
        },
        {
            'name': 'X-Auth-Token',
            'headers': {
                'X-Auth-Token': jwt_token,
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
        },
        {
            'name': 'Cookie авторизация',
            'headers': {
                'Cookie': f'WBToken={jwt_token}; wb_token={jwt_token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
        },
        {
            'name': 'Bearer + дополнительные заголовки',
            'headers': {
                'Authorization': f'Bearer {jwt_token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://seller.wildberries.ru/',
                'Origin': 'https://seller.wildberries.ru',
                'X-Requested-With': 'XMLHttpRequest',
            }
        }
    ]
    
    # Тестовые endpoints
    test_endpoints = [
        'https://seller.wildberries.ru/ns/sm/supplier-manager/api/v1/supplier/products',
        'https://seller.wildberries.ru/ns/sm/supplier-manager/api/v1/supplier/products/182168410',
        'https://seller.wildberries.ru/ns/sm/supplier-manager/api/v1/supplier/info',
        'https://seller.wildberries.ru/ns/sm/supplier-manager/api/v1/supplier/statistics',
        'https://seller.wildberries.ru/api/v1/supplier/products',
        'https://seller.wildberries.ru/api/v1/supplier/info',
    ]
    
    for method in auth_methods:
        print(f"\n{method['name']}:")
        
        session = requests.Session()
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
        else:
            print(f"  😞 Успешных запросов: 0/{len(test_endpoints)}")

if __name__ == "__main__":
    test_existing_token()
