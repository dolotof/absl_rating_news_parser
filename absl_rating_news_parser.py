import os
import requests
from bs4 import BeautifulSoup
from telegram import Bot
import asyncio
import json
import logging
import time

# Настройка логирования
logging.basicConfig(
    filename='parser.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация
CHAT_ID = os.environ['CHAT_ID']  # Используем секрет
BOT_TOKEN = os.environ['BOT_TOKEN']  # Используем секрет
BASE_URL = 'https://absolute-rating.mirtesen.ru/?page=1'
DB_FILE = 'processed_news.json'

# Инициализация бота
bot = Bot(token=BOT_TOKEN)


def load_processed_news():
    """Загрузка уже обработанных новостей"""
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"Ошибка при загрузке обработанных новостей: {e}")
        return []


def save_processed_news(processed_news):
    """Сохранение обработанных новостей"""
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(processed_news, f, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Ошибка при сохранении обработанных новостей: {e}")


async def parse_page():
    """Парсинг страницы"""
    try:
        response = requests.get(BASE_URL)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        news_items = soup.select('article.post-card')
        news_list = []

        for item in news_items:
            try:
                link_elem = item.select_one('a.post-card__pubdate')
                time_elem = item.select_one('a.post-card__pubdate')

                if link_elem and time_elem:
                    link = 'https:' + link_elem['href']
                    time_str = time_elem.text.strip()

                    news_list.append({'link': link, 'time': time_str})
            except Exception as e:
                logger.error(f"Ошибка при парсинге новости: {e}")
                continue

        return news_list
    except Exception as e:
        logger.error(f"Ошибка при парсинге страницы: {e}")
        return []


async def send_to_telegram(link):
    """Отправка новости в Telegram"""
    try:
        await bot.send_message(chat_id=CHAT_ID, text=link)
        logger.info(f"Отправлена новость: {link}")
    except Exception as e:
        logger.error(f"Ошибка при отправке в Telegram: {e}")


async def main():
    """Основная логика"""
    processed_news = load_processed_news()
    processed_links = {news['link'] for news in processed_news}

    # Первый запуск или проверка новых новостей
    logger.info("Проверка новостей")
    news_list = await parse_page()
    new_news = [
        news for news in news_list if news['link'] not in processed_links
    ]

    if new_news:
        new_news.sort(key=lambda x: x['time'], reverse=True)
        for news in reversed(new_news):
            await send_to_telegram(news['link'])
            processed_news.append(news)
            processed_links.add(news['link'])
        save_processed_news(processed_news)
    else:
        logger.info("Новых новостей не найдено")


if __name__ == "__main__":
        asyncio.run(main())

print("Updated for workflow")
