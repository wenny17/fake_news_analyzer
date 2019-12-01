import asyncio

import aiohttp
import pymorphy2
import pytest

from process import process_article
from text_tools import get_charged_words


PROCESSING_TIMEOUT = 3


@pytest.fixture(scope='module')
def morph():
    return pymorphy2.MorphAnalyzer()


@pytest.fixture(scope='module', params=[
    ('https://inosmi.ru/social/20191129/246343400.html',
     {'status': 'OK'},
     PROCESSING_TIMEOUT),

    ('https://inosmi.ru/social/20191127/246324673.html',
     {'status': 'OK'},
     PROCESSING_TIMEOUT),

    ('http://example.com',
     {'status': 'PARSING_ERROR', 'score': None, 'words_count': None},
     PROCESSING_TIMEOUT),

    ('https://inosmi.ru/economic/20190629/245384784.html',
     {'status': 'TIMEOUT', 'score': None, 'words_count': None},
     0.01),

    ('http://127.0.0.1:8000/',
     {'status': 'FETCH_ERROR', 'score': None, 'words_count': None},
     PROCESSING_TIMEOUT)
])
def params(request):
    return request.param


@pytest.fixture(scope='module')
def words():
    return get_charged_words()


async def _test_process_article(morph, params, words):
    url, expected_output, timeout = params
    async with aiohttp.ClientSession() as session:
        result = await process_article(session, morph, words, url, timeout)

        assert type(result) is dict

        for param in expected_output:
            assert result[param] == expected_output[param]


def test_process_article(morph, params, words):
    asyncio.run(_test_process_article(morph, params, words))
