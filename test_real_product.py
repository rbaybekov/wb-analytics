#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест парсинга реального товара Wildberries
"""

import requests
from fake_useragent import UserAgent
import json
import time

def test_real_product():
    print('Тест парсинга реального товара')
    print('=' * 40)
    
    # Реальный URL товара
    url = 'https://www.wildberries.ru/catalog/182168410/detail.aspx'
    article = '182168410'
    
    print(f'URL товара: {url}')
    print(f'Артикул: {article}')
    
    # Создаем сессию с разными настройками
    ua = UserAgent()
    session = requests.Session()
    
    # Попробуем разные наборы заголовков
    headers_variants = [
        {
            'User-Agent': ua.random,
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
            'Referer': 'https://www.wildberries.ru/',
        },
        {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
            'Referer': 'https://www.wildberries.ru/',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        },
        {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
            'Accept-Language': 'ru-RU,ru;q=0.9',
        }
    ]
    
    # Разные API endpoints
    api_endpoints = [
        f'https://card.wb.ru/cards/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={article}',
        f'https://card.wb.ru/cards/detail?nm={article}',
        f'https://card.wb.ru/cards/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={article}&regions=68,64,83,4,38,80,69,70,30,40,86,75,76,1,31,66,110,48,22,114,111',
        f'https://product-order.wb.ru/card/catalog?nm={article}',
    ]
    
    for i, headers in enumerate(headers_variants, 1):
        print(f'\n{i}. Тест с набором заголовков {i}')
        session.headers.update(headers)
        
        for j, api_url in enumerate(api_endpoints, 1):
            print(f'  {j}. API endpoint: {api_url}')
            
            try:
                response = session.get(api_url, timeout=15)
                print(f'     Статус: {response.status_code}')
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f'     JSON загружен успешно')
                        
                        if data.get('data', {}).get('products'):
                            product = data['data']['products'][0]
                            name = product.get('name', 'Неизвестно')
                            price = float(product.get('priceU', 0)) / 100
                            
                            print(f'     УСПЕХ! Товар найден:')
                            print(f'     Название: {name}')
                            print(f'     Цена: {price:.2f} руб.')
                            
                            # Дополнительная информация
                            if product.get('salePriceU'):
                                sale_price = float(product['salePriceU']) / 100
                                print(f'     Цена со скидкой: {sale_price:.2f} руб.')
                            
                            if product.get('sale'):
                                print(f'     Скидка: {product["sale"]}%')
                                
                            if product.get('reviewRating'):
                                print(f'     Рейтинг: {product["reviewRating"]}')
                                
                            if product.get('feedbacks'):
                                print(f'     Отзывов: {product["feedbacks"]}')
                            
                            return True
                        else:
                            print(f'     Товар не найден в ответе')
                            print(f'     Структура ответа: {list(data.keys()) if isinstance(data, dict) else "не словарь"}')
                    except json.JSONDecodeError as e:
                        print(f'     Ошибка JSON: {e}')
                        print(f'     Ответ: {response.text[:200]}...')
                else:
                    print(f'     Ошибка HTTP: {response.status_code}')
                    
            except Exception as e:
                print(f'     Ошибка запроса: {e}')
            
            time.sleep(0.5)  # Небольшая задержка
    
    # Попробуем парсинг HTML страницы
    print(f'\n4. Попробуем парсинг HTML страницы')
    try:
        response = session.get(url, timeout=15)
        print(f'Статус HTML: {response.status_code}')
        
        if response.status_code == 200:
            html = response.text
            print(f'HTML загружен, размер: {len(html)} символов')
            
            # Ищем данные в HTML
            if 'price' in html.lower():
                print('Найдено упоминание цены в HTML')
            
            if article in html:
                print('Артикул найден в HTML')
                
            # Попробуем найти JSON данные в HTML
            import re
            json_pattern = r'window\.__NUXT__\s*=\s*({.*?});'
            matches = re.findall(json_pattern, html)
            if matches:
                print(f'Найдено {len(matches)} JSON блоков в HTML')
                try:
                    data = json.loads(matches[0])
                    print('JSON из HTML успешно загружен')
                    print(f'Ключи: {list(data.keys()) if isinstance(data, dict) else "не словарь"}')
                except:
                    print('Ошибка парсинга JSON из HTML')
        else:
            print(f'Ошибка загрузки HTML: {response.status_code}')
            
    except Exception as e:
        print(f'Ошибка HTML запроса: {e}')
    
    return False

if __name__ == "__main__":
    success = test_real_product()
    if success:
        print('\nПарсер работает! Можно запускать GUI.')
    else:
        print('\nНужно дополнительное исследование API.')
