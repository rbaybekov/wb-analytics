#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Авторизация в Wildberries Seller через браузер Chrome
"""

import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WildberriesBrowserAuth:
    """Авторизация через браузер Chrome"""
    
    def __init__(self, headless=False):
        self.driver = None
        self.headless = headless
        self.jwt_token = None
        self.session_cookies = {}
    
    def setup_driver(self):
        """Настройка Chrome драйвера"""
        try:
            logger.info("Настройка Chrome драйвера...")
            
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")
            
            # Дополнительные опции для стабильности
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            
            # Автоматическая установка ChromeDriver
            service = Service(ChromeDriverManager().install())
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(10)
            
            logger.info("Chrome драйвер настроен успешно")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка настройки драйвера: {e}")
            return False
    
    def login_to_seller(self, phone):
        """Авторизация в Seller панели"""
        try:
            logger.info(f"Авторизация в Seller панели для номера: {phone}")
            
            # Переходим на страницу авторизации
            seller_url = "https://seller.wildberries.ru/"
            logger.info(f"Переход на: {seller_url}")
            
            self.driver.get(seller_url)
            time.sleep(3)
            
            # Ищем поле для ввода телефона
            phone_selectors = [
                "input[type='tel']",
                "input[placeholder*='телефон']",
                "input[placeholder*='phone']",
                "input[name*='phone']",
                "input[id*='phone']",
                ".phone-input",
                "#phone",
                "[data-testid='phone-input']"
            ]
            
            phone_input = None
            for selector in phone_selectors:
                try:
                    phone_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    logger.info(f"Найдено поле телефона: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if not phone_input:
                logger.error("Поле для ввода телефона не найдено")
                return False
            
            # Вводим номер телефона
            phone_input.clear()
            phone_input.send_keys(phone)
            logger.info("Номер телефона введен")
            
            # Ищем кнопку отправки SMS
            send_button_selectors = [
                "button[type='submit']",
                "button:contains('Отправить')",
                "button:contains('Получить код')",
                ".send-sms-btn",
                "#send-sms",
                "[data-testid='send-sms']"
            ]
            
            send_button = None
            for selector in send_button_selectors:
                try:
                    if ":contains(" in selector:
                        # Используем XPath для текстового поиска
                        xpath = f"//button[contains(text(), 'Отправить') or contains(text(), 'Получить код')]"
                        send_button = self.driver.find_element(By.XPATH, xpath)
                    else:
                        send_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    logger.info(f"Найдена кнопка отправки: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if not send_button:
                logger.error("Кнопка отправки SMS не найдена")
                return False
            
            # Нажимаем кнопку отправки SMS
            send_button.click()
            logger.info("SMS код отправлен")
            
            # Ждем появления поля для ввода кода
            code_selectors = [
                "input[type='text'][placeholder*='код']",
                "input[placeholder*='code']",
                "input[name*='code']",
                "input[id*='code']",
                ".code-input",
                "#code",
                "[data-testid='code-input']"
            ]
            
            code_input = None
            for selector in code_selectors:
                try:
                    code_input = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    logger.info(f"Найдено поле для кода: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if not code_input:
                logger.error("Поле для ввода SMS кода не найдено")
                return False
            
            # Запрашиваем SMS код у пользователя
            sms_code = input("Введите SMS код: ").strip()
            
            if not sms_code:
                logger.error("SMS код не введен")
                return False
            
            # Вводим SMS код
            code_input.clear()
            code_input.send_keys(sms_code)
            logger.info("SMS код введен")
            
            # Ищем кнопку подтверждения
            confirm_button_selectors = [
                "button[type='submit']",
                "button:contains('Войти')",
                "button:contains('Подтвердить')",
                ".confirm-btn",
                "#confirm",
                "[data-testid='confirm']"
            ]
            
            confirm_button = None
            for selector in confirm_button_selectors:
                try:
                    if ":contains(" in selector:
                        xpath = "//button[contains(text(), 'Войти') or contains(text(), 'Подтвердить')]"
                        confirm_button = self.driver.find_element(By.XPATH, xpath)
                    else:
                        confirm_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    logger.info(f"Найдена кнопка подтверждения: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if not confirm_button:
                logger.error("Кнопка подтверждения не найдена")
                return False
            
            # Нажимаем кнопку подтверждения
            confirm_button.click()
            logger.info("Кнопка подтверждения нажата")
            
            # Ждем успешной авторизации
            time.sleep(5)
            
            # Проверяем, что мы авторизованы
            current_url = self.driver.current_url
            logger.info(f"Текущий URL: {current_url}")
            
            if "seller.wildberries.ru" in current_url and "login" not in current_url:
                logger.info("Авторизация успешна!")
                return True
            else:
                logger.error("Авторизация не удалась")
                return False
                
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
                if any(keyword in cookie_name for keyword in ['token', 'jwt', 'auth', 'session']):
                    logger.info(f"Найден cookie: {cookie['name']}")
                    self.session_cookies[cookie['name']] = cookie['value']
            
            # Ищем токены в localStorage
            try:
                local_storage = self.driver.execute_script("return window.localStorage;")
                logger.info(f"Найдено {len(local_storage)} элементов в localStorage")
                
                for key, value in local_storage.items():
                    if any(keyword in key.lower() for keyword in ['token', 'jwt', 'auth']):
                        logger.info(f"Найден localStorage: {key}")
                        self.session_cookies[key] = value
            except Exception as e:
                logger.warning(f"Ошибка при чтении localStorage: {e}")
            
            # Ищем токены в sessionStorage
            try:
                session_storage = self.driver.execute_script("return window.sessionStorage;")
                logger.info(f"Найдено {len(session_storage)} элементов в sessionStorage")
                
                for key, value in session_storage.items():
                    if any(keyword in key.lower() for keyword in ['token', 'jwt', 'auth']):
                        logger.info(f"Найден sessionStorage: {key}")
                        self.session_cookies[key] = value
            except Exception as e:
                logger.warning(f"Ошибка при чтении sessionStorage: {e}")
            
            # Ищем токены в JavaScript переменных
            try:
                js_tokens = self.driver.execute_script("""
                    var tokens = {};
                    for (var key in window) {
                        if (key.toLowerCase().includes('token') || key.toLowerCase().includes('jwt')) {
                            tokens[key] = window[key];
                        }
                    }
                    return tokens;
                """)
                
                if js_tokens:
                    logger.info(f"Найдено {len(js_tokens)} JS переменных с токенами")
                    for key, value in js_tokens.items():
                        logger.info(f"JS переменная: {key}")
                        if isinstance(value, str) and len(value) > 10:
                            self.session_cookies[f"js_{key}"] = value
            except Exception as e:
                logger.warning(f"Ошибка при поиске JS переменных: {e}")
            
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
                session.cookies.set(cookie_name, cookie_value)
            
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
    
    auth = WildberriesBrowserAuth(headless=False)  # Показываем браузер
    
    try:
        # Настройка драйвера
        if not auth.setup_driver():
            print("Ошибка настройки браузера")
            return
        
        # Авторизация
        if not auth.login_to_seller(phone):
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
