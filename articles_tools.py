import asyncio
import logging
import time
from contextlib import contextmanager
from enum import Enum

import aiohttp
import pymorphy2
import pytest
from async_timeout import timeout

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
        "status": status,
        "url": article,
        "score": score,
        "words_count": words_count,
    }


async def process_article(article, morph, session, charged_words, fetch_timeout=3, process_timeout=3):
    try:
        async with timeout(fetch_timeout):
            html = await fetch(session, article)
        clean_text = inosmi_ru.sanitize(html, True)
        with work_timer():
            async with timeout(process_timeout):
                words = await text_tools.split_by_words(morph, clean_text)
            rate = text_tools.calculate_jaundice_rate(words, charged_words)
        status = ProcessingStatus.OK.value
        return process_result(status, article, rate, len(words))
    except inosmi_ru.ArticleNotFound as e:
        status = ProcessingStatus.PARSING_ERROR.value
        return process_result(status, article)
    except (aiohttp.ClientConnectorError, aiohttp.ClientResponseError) as e:
        status = ProcessingStatus.FETCH_ERROR.value
        return process_result(status, article)
    except asyncio.TimeoutError as e:
        status = ProcessingStatus.TIMEOUT.value
        return process_result(status, article)


@pytest.mark.asyncio
async def test_process_article():
    morph = pymorphy2.MorphAnalyzer()
    charged_words = text_tools.get_charged_words('charged_dict')

    async with aiohttp.ClientSession() as session:
        article_processing_results = await process_article(
            session=session,
            article='https://inosmi.ru/politic/20200125/246700442.html',
            morph=morph,
            charged_words=charged_words,
        )
        assert article_processing_results['status'] == ProcessingStatus.OK.value

        article_processing_results = await process_article(
            session=session,
            article='https://inosmi.ru/politic/20200125/2467004432.html',
            morph=morph,
            charged_words=charged_words,
        )
        assert article_processing_results['status'] == ProcessingStatus.FETCH_ERROR.value

        article_processing_results = await process_article(
            session=session,
            article='https://google.com',
            morph=morph,
            charged_words=charged_words
        )
        assert article_processing_results['status'] == ProcessingStatus.PARSING_ERROR.value

        article_processing_results = await process_article(
            session=session,
            article='https://inosmi.ru/politic/20200125/246700442.html',
            morph=morph,
            charged_words=charged_words,
            fetch_timeout=0.1
        )
        assert article_processing_results['status'] == ProcessingStatus.TIMEOUT.value

        article_processing_results = await process_article(
            session=session,
            article='https://inosmi.ru/politic/20200125/246700442.html',
            morph=morph,
            charged_words=charged_words,
            process_timeout=0.1
        )
        assert article_processing_results['status'] == ProcessingStatus.TIMEOUT.value
