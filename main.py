import asyncio
import logging
import time
from contextlib import contextmanager
from enum import Enum

import aiohttp
import aionursery
import pymorphy2
from async_timeout import timeout

import text_tools
from adapters import inosmi_ru

TEST_ARTICLES = [
    'https://inosmi.ru/social/20200126/246679119.html',
    'https://inosmi.ru/politic/20200126/246701782.html',
    'https://inosmi.ru/politic/20200125/246700581.html',
    'https://inosmi.ru/politic/20200125/246700442.html'
]


class ProcessingStatus(Enum):
    OK = 'OK'
    FETCH_ERROR = 'FETCH_ERROR'
    PARSING_ERROR = 'PARSING_ERROR'
    TIMEOUT = 'TIMEOUT'


@contextmanager
def work_timer():
    start_time = time.monotonic()
    try:
        yield
    finally:
        end_time = time.monotonic()
        work_time = end_time - start_time
        logging.info(f'Анализ закончен за {work_time} сек')


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


def process_result(result):
    pass


async def main():
    logging.basicConfig(level=logging.INFO)
    morph = pymorphy2.MorphAnalyzer()
    async with aiohttp.ClientSession() as session:
        async with aionursery.Nursery() as nursery:
            tasks = []
            for article in TEST_ARTICLES:
                tasks.append(nursery.start_soon(process_article(article, morph, session)))
                results = await asyncio.wait(tasks)
            for result in results[0]:
                print(result.result())


async def process_article(article, morph, session):
    try:
        with timeout(3):
            html = await fetch(session, article)
        clean_text = inosmi_ru.sanitize(html, True)
        with timeout(0.02):
            with work_timer():
                words = text_tools.split_by_words(morph, clean_text)
        charged_words = text_tools.get_charged_words('charged_dict/charged_dict')
        rate = text_tools.calculate_jaundice_rate(words, charged_words)
        return rate
    except inosmi_ru.ArticleNotFound as e:
        status = ProcessingStatus.PARSING_ERROR
    except (aiohttp.ClientConnectorError, aiohttp.ClientResponseError) as e:
        status = ProcessingStatus.FETCH_ERROR
    except asyncio.TimeoutError as e:
        status = ProcessingStatus.TIMEOUT

asyncio.run(main())
