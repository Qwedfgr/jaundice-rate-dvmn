import asyncio

import aiohttp
import aionursery
import pymorphy2

import text_tools
from adapters import inosmi_ru

TEST_ARTICLES = [
    'https://inosmi.ru/social/20200126/246679119.html',
    'https://inosmi.ru/politic/20200126/246701782.html',
    'https://inosmi.ru/politic/20200125/246700581.html',
    'https://inosmi.ru/politic/20200125/246700442.html'
]


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


def process_result(result):
    pass


async def main():
    morph = pymorphy2.MorphAnalyzer()
    async with aionursery.Nursery() as nursery:
        tasks = []
        for article in TEST_ARTICLES:
            tasks.append(nursery.start_soon(process_article(article, morph)))
        results = await asyncio.wait(tasks)
        for result in results[0]:
            print(result.result())


async def process_article(article, morph):
    async with aiohttp.ClientSession() as session:
        html = await fetch(session, article)
        clean_text = inosmi_ru.sanitize(html, True)
        words = text_tools.split_by_words(morph, clean_text)
        charged_words = text_tools.get_charged_words('charged_dict/charged_dict')
        rate = text_tools.calculate_jaundice_rate(words, charged_words)
        return rate

asyncio.run(main())
