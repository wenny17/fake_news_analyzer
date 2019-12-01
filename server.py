from functools import partial
import logging
from typing import List

import aiohttp
from aiohttp import web
import pymorphy2

from process import process_article
from text_tools import get_charged_words
from utils import create_handy_nursery


async def handler(charged_words: List[str],
                  morph: pymorphy2.MorphAnalyzer,
                  request: web.Request) -> web.Response:

    urls = request.query.get('urls')
    if not urls:
        return web.json_response({'error': 'no urls given'}, status=400)
    urls_list = urls.rstrip(',').split(',')

    if len(urls_list) > 10:
        response = {'error': 'too many urls in request, should be 10 or less'}
        return web.json_response(response, status=400)

    async with aiohttp.ClientSession() as session:
        async with create_handy_nursery() as nursery:
            tasks = []
            for url in urls_list:
                task = nursery.start_soon(process_article(session, morph,
                                                          charged_words, url))
                tasks.append(task)

    list_of_results = [task.result() for task in tasks]
    return web.json_response(list_of_results)


def main():
    formatter = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO,
                        format=formatter)

    charged_words = get_charged_words()
    morph = pymorphy2.MorphAnalyzer()
    handler_wrapper = partial(handler, charged_words, morph)

    app = web.Application()
    app.add_routes([
        web.get('/', handler_wrapper),
    ])
    web.run_app(app)


if __name__ == '__main__':
    main()
