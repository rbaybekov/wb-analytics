#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Финальная версия парсера Wildberries с официальным Seller API
"""

import requests
import json
import time
import random
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ProductInfo:
    """Класс для хранения информации о товаре"""
    article: str
    name: str
    price: float
    old_price: Optional[float] = None
    discount: Optional[int] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    url: str = ""
    stock: Optional[int] = None
    sales: Optional[int] = None
    brand: Optional[str] = None
    category: Optional[str] = None

class WildberriesSellerParser:
    """Парсер для работы с официальным Seller API Wildberries"""
    
    def __init__(self, token: str = None):
        self.token = token
        self.session = requests.Session()
        self.base_url = "https://seller.wildberries.ru"
        
        # Настройка сессии
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://seller.wildberries.ru/',
        })
        
        # Если токен предоставлен, добавляем его
        if self.token:
            self.set_token(self.token)
    
    def set_token(self, token: str):
        """Установка токена авторизации"""
        self.token = token
        
        # Пробуем разные способы авторизации
        auth_methods = [
            {'Authorization': f'Bearer {token}'},
            {'X-Auth-Token': token},
            {'Cookie': f'WBToken={token}; wb_token={token}'}
        ]
        
        for method in auth_methods:
            self.session.headers.update(method)
    
    def load_token_from_file(self, filename: str = "wb_token.json") -> bool:
        """Загрузка токена из файла"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                token_data = json.load(f)
            
            token = token_data.get('token')
            if token:
                self.set_token(token)
                logger.info(f"Токен загружен из файла: {filename}")
                return True
            else:
                logger.error("Токен не найден в файле")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка при загрузке токена: {e}")
            return False
    
    def get_product_info(self, article: str) -> Optional[ProductInfo]:
        """
        Получить информацию о товаре по артикулу
        
        Args:
            article: Артикул товара
            
        Returns:
            ProductInfo или None если товар не найден
        """
        try:
            logger.info(f"Получение информации о товаре: {article}")
            
            # Различные endpoints для получения информации о товаре
            endpoints = [
                f"/ns/sm/supplier-manager/api/v1/supplier/products/{article}",
                f"/ns/sm/supplier-manager/api/v1/supplier/products/{article}/info",
                f"/api/v1/supplier/products/{article}",
                f"/api/v1/products/{article}",
            ]
            
            for endpoint in endpoints:
                url = self.base_url + endpoint
                logger.info(f"Запрос к API: {url}")
                
                try:
                    response = self.session.get(url, timeout=15)
                    logger.info(f"Статус ответа: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        logger.info(f"Получены данные: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}...")
                        
                        # Парсим данные
                        product = self._parse_product_data(data, article)
                        if product:
                            return product
                    
                    elif response.status_code == 404:
                        logger.warning(f"Товар {article} не найден в endpoint {endpoint}")
                        continue
                    else:
                        logger.warning(f"Ошибка {response.status_code} для endpoint {endpoint}")
                        logger.warning(f"Ответ: {response.text[:200]}...")
                        
                except requests.exceptions.RequestException as e:
                    logger.error(f"Ошибка запроса к {endpoint}: {e}")
                    continue
            
            # Если все endpoints не сработали, пробуем поиск
            return self._search_product(article)
            
        except Exception as e:
            logger.error(f"Неожиданная ошибка для артикула {article}: {e}")
            return None
    
    def _parse_product_data(self, data: dict, article: str) -> Optional[ProductInfo]:
        """Парсинг данных товара из ответа API"""
        try:
            # Различные возможные структуры ответа
            product_data = None
            
            if 'data' in data:
                product_data = data['data']
            elif 'product' in data:
                product_data = data['product']
            elif isinstance(data, dict) and 'id' in data:
                product_data = data
            else:
                logger.warning(f"Неизвестная структура данных: {list(data.keys())}")
                return None
            
            if not product_data:
                return None
            
            # Извлекаем информацию о товаре
            name = product_data.get('name', product_data.get('title', ''))
            price = self._extract_price(product_data)
            old_price = self._extract_old_price(product_data)
            discount = product_data.get('discount', product_data.get('sale', 0))
            rating = product_data.get('rating', product_data.get('reviewRating', 0))
            reviews_count = product_data.get('reviews', product_data.get('feedbacks', 0))
            stock = product_data.get('stock', product_data.get('quantity', 0))
            sales = product_data.get('sales', product_data.get('sold', 0))
            brand = product_data.get('brand', product_data.get('brandName', ''))
            category = product_data.get('category', product_data.get('categoryName', ''))
            
            result = ProductInfo(
                article=article,
                name=name,
                price=price,
                old_price=old_price,
                discount=discount,
                rating=rating,
                reviews_count=reviews_count,
                url=f"https://www.wildberries.ru/catalog/{article}/detail.aspx",
                stock=stock,
                sales=sales,
                brand=brand,
                category=category
            )
            
            logger.info(f"Успешно получена информация для артикула {article}: {result.name}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге данных товара: {e}")
            return None
    
    def _extract_price(self, product_data: dict) -> float:
        """Извлечь цену из данных товара"""
        price_fields = ['price', 'priceU', 'currentPrice', 'salePrice', 'priceRub']
        
        for field in price_fields:
            if field in product_data:
                price = product_data[field]
                if isinstance(price, (int, float)):
                    # Если цена в копейках, делим на 100
                    if price > 1000:  # Предполагаем, что если цена больше 1000, то это в копейках
                        return price / 100
                    return float(price)
        
        return 0.0
    
    def _extract_old_price(self, product_data: dict) -> Optional[float]:
        """Извлечь старую цену из данных товара"""
        old_price_fields = ['oldPrice', 'originalPrice', 'basePrice']
        
        for field in old_price_fields:
            if field in product_data:
                old_price = product_data[field]
                if isinstance(old_price, (int, float)) and old_price > 0:
                    if old_price > 1000:  # Предполагаем копейки
                        return old_price / 100
                    return float(old_price)
        
        return None
    
    def _search_product(self, article: str) -> Optional[ProductInfo]:
        """Поиск товара через API поиска"""
        try:
            search_url = f"{self.base_url}/ns/sm/supplier-manager/api/v1/supplier/products/search"
            
            search_params = {
                'query': article,
                'limit': 10
            }
            
            response = self.session.get(search_url, params=search_params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data and data['data']:
                    # Ищем точное совпадение по артикулу
                    for product in data['data']:
                        if str(product.get('id', '')) == str(article):
                            return self._parse_product_data(product, article)
            
            logger.warning(f"Товар {article} не найден через поиск")
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при поиске товара {article}: {e}")
            return None
    
    def get_multiple_products(self, articles: List[str], delay_range: tuple = (1.0, 2.0)) -> List[ProductInfo]:
        """
        Получить информацию о нескольких товарах
        
        Args:
            articles: Список артикулов
            delay_range: Диапазон задержек между запросами
            
        Returns:
            Список ProductInfo
        """
        results = []
        failed_articles = []
        
        for i, article in enumerate(articles):
            logger.info(f"Обработка артикула {i+1}/{len(articles)}: {article}")
            
            result = self.get_product_info(article)
            if result:
                results.append(result)
            else:
                failed_articles.append(article)
            
            # Задержка между запросами (кроме последнего)
            if i < len(articles) - 1:
                delay = random.uniform(delay_range[0], delay_range[1])
                logger.info(f"Ожидание {delay:.1f} секунд...")
                time.sleep(delay)
        
        # Статистика результатов
        success_rate = (len(results) / len(articles)) * 100 if articles else 0
        logger.info(f"Парсинг завершен: {len(results)}/{len(articles)} успешно ({success_rate:.1f}%)")
        
        if failed_articles:
            logger.warning(f"Неудачные артикулы: {', '.join(failed_articles)}")
        
        return results
    
    def get_products_list(self, limit: int = 100) -> List[ProductInfo]:
        """
        Получить список всех товаров продавца
        
        Args:
            limit: Максимальное количество товаров
            
        Returns:
            Список товаров
        """
        try:
            url = f"{self.base_url}/ns/sm/supplier-manager/api/v1/supplier/products"
            
            params = {
                'limit': limit,
                'offset': 0
            }
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                products = []
                if 'data' in data:
                    for product_data in data['data']:
                        article = str(product_data.get('id', ''))
                        product = self._parse_product_data(product_data, article)
                        if product:
                            products.append(product)
                
                logger.info(f"Получено {len(products)} товаров из списка")
                return products
            else:
                logger.error(f"Ошибка получения списка товаров: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Ошибка при получении списка товаров: {e}")
            return []
    
    def save_to_excel(self, products: List[ProductInfo], filename: str = "wb_products.xlsx"):
        """Сохранение товаров в Excel файл"""
        try:
            import pandas as pd
            
            # Преобразуем в DataFrame
            data = []
            for product in products:
                data.append({
                    'Артикул': product.article,
                    'Название': product.name,
                    'Цена': product.price,
                    'Старая цена': product.old_price,
                    'Скидка (%)': product.discount,
                    'Рейтинг': product.rating,
                    'Отзывов': product.reviews_count,
                    'Остаток': product.stock,
                    'Продаж': product.sales,
                    'Бренд': product.brand,
                    'Категория': product.category,
                    'URL': product.url
                })
            
            df = pd.DataFrame(data)
            df.to_excel(filename, index=False)
            logger.info(f"Данные сохранены в Excel файл: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении в Excel: {e}")
            return False
    
    def save_to_json(self, products: List[ProductInfo], filename: str = "wb_products.json"):
        """Сохранение товаров в JSON файл"""
        try:
            data = []
            for product in products:
                data.append({
                    'article': product.article,
                    'name': product.name,
                    'price': product.price,
                    'old_price': product.old_price,
                    'discount': product.discount,
                    'rating': product.rating,
                    'reviews_count': product.reviews_count,
                    'stock': product.stock,
                    'sales': product.sales,
                    'brand': product.brand,
                    'category': product.category,
                    'url': product.url
                })
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Данные сохранены в JSON файл: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении в JSON: {e}")
            return False

def main():
    """Тестирование парсера"""
    print("Wildberries Seller Parser - Тест")
    print("=" * 40)
    
    # Создаем парсер
    parser = WildberriesSellerParser()
    
    # Пробуем загрузить токен из файла
    if parser.load_token_from_file():
        print("✅ Токен загружен из файла")
    else:
        print("❌ Токен не найден. Запустите wb_manual_auth.py для авторизации")
        return
    
    # Тестируем получение списка товаров
    print("\nПолучение списка товаров...")
    products = parser.get_products_list(limit=5)
    
    if products:
        print(f"✅ Найдено {len(products)} товаров:")
        for product in products:
            print(f"- {product.name} ({product.article}): {product.price:.2f} руб.")
        
        # Сохраняем результаты
        parser.save_to_excel(products)
        parser.save_to_json(products)
        
    else:
        print("❌ Товары не найдены")
    
    # Тестируем поиск конкретного товара
    test_article = "182168410"
    print(f"\nПоиск товара {test_article}...")
    product = parser.get_product_info(test_article)
    
    if product:
        print(f"✅ Найден товар: {product.name}")
        print(f"Цена: {product.price:.2f} руб.")
        if product.stock is not None:
            print(f"Остаток: {product.stock}")
        if product.sales is not None:
            print(f"Продаж: {product.sales}")
    else:
        print("❌ Товар не найден")

if __name__ == "__main__":
    main()
