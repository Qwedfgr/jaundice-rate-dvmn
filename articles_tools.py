import asyncio
import logging
import time
from contextlib import contextmanager
from enum import Enum

import aiohttp
from async_timeout import timeout
import pytest
import pymorphy2

import text_tools
from adapters import inosmi_ru


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


def process_result(status, article, score=None, words_count=None):
    return {
        'status': status,
        'url': article,
        'score': score,
        'words_count': words_count,
    }


async def process_article(article, morph, session, charged_words):
    try:
        with timeout(3):
            html = await fetch(session, article)
        clean_text = inosmi_ru.sanitize(html, True)
        with timeout(0.02):
            with work_timer():
                words = text_tools.split_by_words(morph, clean_text)
        rate = text_tools.calculate_jaundice_rate(words, charged_words)
        status = ProcessingStatus.OK
        return process_result(status, article, rate, len(words))
    except inosmi_ru.ArticleNotFound as e:
        status = ProcessingStatus.PARSING_ERROR
        return process_result(status, article)
    except (aiohttp.ClientConnectorError, aiohttp.ClientResponseError) as e:
        status = ProcessingStatus.FETCH_ERROR
        return process_result(status, article)
    except asyncio.TimeoutError as e:
        status = ProcessingStatus.TIMEOUT
        return process_result(status, article)


