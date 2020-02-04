import asyncio
import json
import logging
from functools import partial

import aionursery
import pymorphy2
from aiohttp import ClientSession
from aiohttp import web
from aiohttp.web_response import json_response

from articles_tools import process_article
from text_tools import get_charged_words


async def handle(morph, charged_words, request, max_url_to_process=5):
    urls = request.query.get('urls')
    if not urls:
        return json_response(data={'error': 'no articles to process'}, status=400)
    urls_list = urls.split(',')
    if len(urls_list) > max_url_to_process:
        return json_response(data={'error': 'to many articles to process'}, status=400)

    async with ClientSession() as session:
        async with aionursery.Nursery() as nursery:
            tasks = []
            for article in urls_list:
                tasks.append(nursery.start_soon(process_article(article, morph, session, charged_words)))
                results, _ = await asyncio.wait(tasks)
                data = [result.result() for result in results]
            return web.json_response(data, status=200)


def main():
    logging.basicConfig(level=logging.INFO)
    morph = pymorphy2.MorphAnalyzer()
    charged_words = get_charged_words('charged_dict')
    app = web.Application()
    app.add_routes([web.get('/', partial(handle, morph, charged_words))])
    web.run_app(app)


if __name__ == '__main__':
    main()
