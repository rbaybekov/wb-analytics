#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест парсера Wildberries по URL
"""

import requests
from fake_useragent import UserAgent
import json
import re

def extract_article_from_url(url):
    """Извлечь артикул из URL"""
    try:
        # Различные форматы URL Wildberries
        if '/catalog/' in url and '/detail.aspx' in url:
            # Формат: https://www.wildberries.ru/catalog/12345678/detail.aspx
            match = re.search(r'/catalog/(\d+)/detail\.aspx', url)
            if match:
                return match.group(1)
        elif '/catalog/' in url:
            # Формат: https://www.wildberries.ru/catalog/12345678/
            match = re.search(r'/catalog/(\d+)', url)
            if match:
                return match.group(1)
        return None
    except Exception as e:
        print(f'Ошибка при извлечении артикула: {e}')
        return None

def test_url_parsing():
    print('Тест парсера Wildberries по URL')
    print('=' * 40)

    # Тестовые URL
    urls = [
        'https://www.wildberries.ru/catalog/182168410/detail.aspx?targetUrl=SP',
        'https://www.wildberries.ru/catalog/275545719/detail.aspx?targetUrl=SP',
        'https://www.wildberries.ru/catalog/159808254/detail.aspx?targetUrl=SP'
    ]

    # Создаем сессию
    ua = UserAgent()
    session = requests.Session()
    session.headers.update({
        'User-Agent': ua.random,
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
        'Referer': 'https://www.wildberries.ru/',
    })

    for i, url in enumerate(urls, 1):
        print(f'\n{i}. Тестируем URL: {url}')
        
        # Извлекаем артикул из URL
        article = extract_article_from_url(url)
        if not article:
            print('Не удалось извлечь артикул из URL')
            continue
            
        print(f'Извлеченный артикул: {article}')
        
        # Формируем API URL
        api_url = f'https://card.wb.ru/cards/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={article}'
        print(f'API URL: {api_url}')
        
        try:
            response = session.get(api_url, timeout=15)
            print(f'Статус ответа: {response.status_code}')
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    if data.get('data', {}).get('products'):
                        product = data['data']['products'][0]
                        name = product.get('name', 'Неизвестно')
                        price = float(product.get('priceU', 0)) / 100
                        old_price = product.get('priceU', 0)
                        discount = product.get('sale', 0)
                        rating = product.get('reviewRating', 0)
                        reviews_count = product.get('feedbacks', 0)
                        
                        print('Товар найден!')
                        print(f'Название: {name}')
                        print(f'Цена: {price:.2f} руб.')
                        
                        if old_price and old_price != price * 100:
                            print(f'Старая цена: {old_price/100:.2f} руб.')
                        
                        if discount:
                            print(f'Скидка: {discount}%')
                            
                        if rating:
                            print(f'Рейтинг: {rating}')
                            
                        if reviews_count:
                            print(f'Отзывов: {reviews_count}')
                            
                        print('Успешно!')
                    else:
                        print('Товар не найден в ответе API')
                        print(f'Ответ: {response.text[:200]}...')
                except json.JSONDecodeError as e:
                    print(f'Ошибка парсинга JSON: {e}')
                    print(f'Ответ сервера: {response.text[:200]}...')
            else:
                print(f'Ошибка HTTP: {response.status_code}')
                print(f'Ответ: {response.text[:200]}...')
                
        except Exception as e:
            print(f'Ошибка запроса: {e}')

if __name__ == "__main__":
    test_url_parsing()
