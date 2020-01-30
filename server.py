import asyncio
import logging
from functools import partial

import aionursery
import pymorphy2
from aiohttp import ClientSession
from aiohttp import web
from aiohttp.web_response import json_response

from main import process_article
from text_tools import get_charged_words

MAX_URLS_TO_PROCESS = 15


async def handle(request, morph, charged_words):
    urls = request.query.get('urls')
    if not urls:
        return json_response(data={'error': 'no articles to process'}, status=400)
    urls_list = urls.split(',')
    if len(urls_list) > MAX_URLS_TO_PROCESS:
        return json_response(data={'error': 'to many articles to process'}, status=400)

    async with ClientSession() as session:
        async with aionursery.Nursery() as nursery:
            tasks = []
            for article in urls_list:
                tasks.append(nursery.start_soon(process_article(article, morph, session)))
                results = await asyncio.wait(tasks)
            for result in results[0]:
                print(result.result())
    return web.json_response(status=200)


def main():
    logging.basicConfig(level=logging.INFO)
    morph = pymorphy2.MorphAnalyzer()
    charged_words = get_charged_words('charged_dict')
    app = web.Application()
    app.add_routes([web.get('/', partial(handle, morph, charged_words))])
    web.run_app(app)


if __name__ == '__main__':
    main()
