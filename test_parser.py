#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простой тест парсера Wildberries
"""

import requests
from fake_useragent import UserAgent
import json

def test_parser():
    print('Тест парсера Wildberries')
    print('=' * 30)

    # Создаем сессию
    ua = UserAgent()
    session = requests.Session()
    session.headers.update({
        'User-Agent': ua.random,
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
    })

    # Тестовый артикул
    article = '182168410'
    url = f'https://card.wb.ru/cards/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={article}'

    print(f'Тестируем артикул: {article}')

    try:
        response = session.get(url, timeout=10)
        print(f'Статус ответа: {response.status_code}')
        
        if response.status_code == 200:
            try:
                data = response.json()
                
                if data.get('data', {}).get('products'):
                    product = data['data']['products'][0]
                    name = product.get('name', 'Неизвестно')
                    price = float(product.get('priceU', 0)) / 100
                    
                    print('Товар найден!')
                    print(f'Название: {name}')
                    print(f'Цена: {price:.2f} руб.')
                    print('Парсер работает!')
                else:
                    print('Товар не найден в ответе')
            except json.JSONDecodeError:
                print('Ошибка парсинга JSON')
                print(f'Ответ сервера: {response.text[:200]}...')
        else:
            print(f'Ошибка HTTP: {response.status_code}')
            
    except Exception as e:
        print(f'Ошибка: {e}')

if __name__ == "__main__":
    test_parser()