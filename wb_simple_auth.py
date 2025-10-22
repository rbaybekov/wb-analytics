#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Упрощенная авторизация в Wildberries Seller через браузер
"""

import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleWildberriesAuth:
    """Упрощенная авторизация через браузер"""
    
    def __init__(self):
        self.driver = None
        self.session_cookies = {}
    
    def setup_driver(self):
        """Настройка Chrome драйвера"""
        try:
            logger.info("Настройка Chrome драйвера...")
            
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            
            # Используем старый способ инициализации для совместимости
            self.driver = webdriver.Chrome(
                executable_path=ChromeDriverManager().install(),
                options=chrome_options
            )
            self.driver.implicitly_wait(10)
            
            logger.info("Chrome драйвер настроен успешно")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка настройки драйвера: {e}")
            return False
    
    def manual_login(self, phone):
        """Ручная авторизация с помощью пользователя"""
        try:
            logger.info(f"Открытие страницы авторизации для номера: {phone}")
            
            # Переходим на страницу авторизации
            seller_url = "https://seller.wildberries.ru/"
            logger.info(f"Переход на: {seller_url}")
            
            self.driver.get(seller_url)
            time.sleep(3)
            
            print(f"\n{'='*60}")
            print("ИНСТРУКЦИИ ДЛЯ АВТОРИЗАЦИИ:")
            print("1. В открывшемся браузере найдите поле для ввода телефона")
            print(f"2. Введите номер телефона: {phone}")
            print("3. Нажмите кнопку 'Отправить код' или 'Получить код'")
            print("4. Введите SMS код, который придет на телефон")
            print("5. Нажмите кнопку 'Войти' или 'Подтвердить'")
            print("6. Дождитесь успешной авторизации")
            print("7. Вернитесь в консоль и нажмите Enter")
            print(f"{'='*60}\n")
            
            input("Нажмите Enter после успешной авторизации...")
            
            # Проверяем текущий URL
            current_url = self.driver.current_url
            logger.info(f"Текущий URL: {current_url}")
            
            if "seller.wildberries.ru" in current_url and "login" not in current_url:
                logger.info("Авторизация успешна!")
                return True
            else:
                logger.warning("Возможно, авторизация не завершена")
                return True  # Продолжаем в любом случае
                
        except Exception as e:
            logger.error(f"Ошибка при авторизации: {e}")
            return False
    
    def extract_tokens(self):
        """Извлечение токенов из браузера"""
        try:
            logger.info("Извлечение токенов из браузера...")
            
            # Получаем все cookies
            cookies = self.driver.get_cookies()
            logger.info(f"Найдено {len(cookies)} cookies")
            
            # Ищем токены в cookies
            for cookie in cookies:
                cookie_name = cookie['name'].lower()
                if any(keyword in cookie_name for keyword in ['token', 'jwt', 'auth', 'session', 'wb']):
                    logger.info(f"Найден cookie: {cookie['name']}")
                    self.session_cookies[cookie['name']] = cookie['value']
            
            # Ищем токены в localStorage
            try:
                local_storage = self.driver.execute_script("return window.localStorage;")
                logger.info(f"Найдено {len(local_storage)} элементов в localStorage")
                
                for key, value in local_storage.items():
                    if any(keyword in key.lower() for keyword in ['token', 'jwt', 'auth', 'wb']):
                        logger.info(f"Найден localStorage: {key}")
                        self.session_cookies[f"local_{key}"] = value
            except Exception as e:
                logger.warning(f"Ошибка при чтении localStorage: {e}")
            
            # Ищем токены в sessionStorage
            try:
                session_storage = self.driver.execute_script("return window.sessionStorage;")
                logger.info(f"Найдено {len(session_storage)} элементов в sessionStorage")
                
                for key, value in session_storage.items():
                    if any(keyword in key.lower() for keyword in ['token', 'jwt', 'auth', 'wb']):
                        logger.info(f"Найден sessionStorage: {key}")
                        self.session_cookies[f"session_{key}"] = value
            except Exception as e:
                logger.warning(f"Ошибка при чтении sessionStorage: {e}")
            
            logger.info(f"Всего найдено токенов: {len(self.session_cookies)}")
            return len(self.session_cookies) > 0
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении токенов: {e}")
            return False
    
    def test_api_access(self):
        """Тестирование доступа к API с полученными токенами"""
        try:
            logger.info("Тестирование доступа к API...")
            
            # Создаем сессию requests
            session = requests.Session()
            
            # Добавляем cookies в сессию
            for cookie_name, cookie_value in self.session_cookies.items():
                if not cookie_name.startswith(('local_', 'session_')):
                    session.cookies.set(cookie_name, cookie_value)
            
            # Добавляем заголовки
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
                'Referer': 'https://seller.wildberries.ru/',
            })
            
            # Тестовые API endpoints
            test_endpoints = [
                "https://seller.wildberries.ru/ns/sm/supplier-manager/api/v1/supplier/products",
                "https://seller.wildberries.ru/ns/sm/supplier-manager/api/v1/supplier/info",
                "https://seller.wildberries.ru/api/v1/supplier/products",
            ]
            
            success_count = 0
            
            for endpoint in test_endpoints:
                try:
                    response = session.get(endpoint, timeout=10)
                    logger.info(f"{endpoint}: {response.status_code}")
                    
                    if response.status_code == 200:
                        logger.info(f"✅ Успех: {endpoint}")
                        success_count += 1
                        
                        try:
                            data = response.json()
                            logger.info(f"Данные получены: {len(str(data))} символов")
                            
                            # Если это список товаров, показываем количество
                            if isinstance(data, dict) and 'data' in data:
                                if isinstance(data['data'], list):
                                    logger.info(f"Найдено товаров: {len(data['data'])}")
                                else:
                                    logger.info(f"Структура данных: {list(data['data'].keys())}")
                        except:
                            logger.info(f"Ответ: {response.text[:100]}...")
                    else:
                        logger.warning(f"❌ Ошибка {response.status_code}: {endpoint}")
                        
                except Exception as e:
                    logger.error(f"❌ Исключение для {endpoint}: {e}")
            
            logger.info(f"Успешных запросов: {success_count}/{len(test_endpoints)}")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Ошибка при тестировании API: {e}")
            return False
    
    def save_tokens(self, filename="wb_tokens.json"):
        """Сохранение токенов в файл"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.session_cookies, f, indent=2, ensure_ascii=False)
            logger.info(f"Токены сохранены в файл: {filename}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении токенов: {e}")
            return False
    
    def close(self):
        """Закрытие браузера"""
        if self.driver:
            self.driver.quit()
            logger.info("Браузер закрыт")

def main():
    """Основная функция"""
    phone = "+79264845850"
    
    print("Авторизация в Wildberries Seller через браузер")
    print("=" * 50)
    
    auth = SimpleWildberriesAuth()
    
    try:
        # Настройка драйвера
        if not auth.setup_driver():
            print("Ошибка настройки браузера")
            return
        
        # Авторизация
        if not auth.manual_login(phone):
            print("Ошибка авторизации")
            return
        
        # Извлечение токенов
        if not auth.extract_tokens():
            print("Токены не найдены")
            return
        
        # Тестирование API
        if auth.test_api_access():
            print("✅ Доступ к API получен!")
        else:
            print("❌ Доступ к API не получен")
        
        # Сохранение токенов
        auth.save_tokens()
        
        # Показываем найденные токены
        print(f"\nНайденные токены ({len(auth.session_cookies)}):")
        for name, value in auth.session_cookies.items():
            print(f"- {name}: {value[:50]}...")
        
        input("\nНажмите Enter для закрытия браузера...")
        
    except KeyboardInterrupt:
        print("\nПрервано пользователем")
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        auth.close()

if __name__ == "__main__":
    main()
