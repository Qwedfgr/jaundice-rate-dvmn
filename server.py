import logging
from functools import partial

import pymorphy2
from aiohttp import web
from aiohttp.web_response import json_response

from text_tools import get_charged_words


async def handle(request, morph, charged_words):
    urls = request.query.get('urls')
    if not urls:
        return json_response(data={'error': 'no articles to process'}, status=400)
    data = {
        'status': 'status',
        'url': 'url'
    }
    return web.json_response(data=data, status=200)


def main():
    logging.basicConfig(level=logging.INFO)
    morph = pymorphy2.MorphAnalyzer()
    charged_words = get_charged_words('charged_dict')
    app = web.Application()
    app.add_routes([web.get('/', partial(handle, morph, charged_words))])
    web.run_app(app)


if __name__ == '__main__':
    main()
