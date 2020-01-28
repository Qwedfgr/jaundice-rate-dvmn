from functools import partial

from aiohttp import web


async def handle(request):
    data = {
        'status': 'status',
        'url': 'url'
    }
    return web.json_response(data)

app = web.Application()
app.add_routes([web.get('/', partial(handle))])


if __name__ == '__main__':
    web.run_app(app)