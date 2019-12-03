import asyncio
from enum import Enum
from typing import List

import aiohttp
from async_timeout import timeout as async_timeout
import pymorphy2

from adapters import ArticleNotFound, AdapterNotImplemented
from text_tools import (split_by_words,
                        calculate_jaundice_rate,
                        sanitize_html)
from utils import timing_manager


PROCESSING_TIMEOUT = 3
RESPONSE_TIMEOUT = 10


class ProcessingStatus(Enum):
    OK = 'OK'
    FETCH_ERROR = 'FETCH_ERROR'
    PARSING_ERROR = 'PARSING_ERROR'
    TIMEOUT = 'TIMEOUT'

    def __str__(self):
        return str(self.value)


async def fetch(session: aiohttp.ClientSession, url: str) -> str:
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


async def process_article(session: aiohttp.ClientSession,
                          morph: pymorphy2.MorphAnalyzer,
                          charged_words: List[str],
                          url: str,
                          timeout=PROCESSING_TIMEOUT) -> dict:
    score, words_count = None, None
    try:
        async with async_timeout(RESPONSE_TIMEOUT):
            html = await fetch(session, url)

        text = sanitize_html(html, url)

        async with timing_manager(timeout):
            words = await split_by_words(morph, text)

        score = calculate_jaundice_rate(words, charged_words)
        words_count = len(words)
        status = ProcessingStatus.OK

    except aiohttp.ClientError:
        status = ProcessingStatus.FETCH_ERROR

    except asyncio.TimeoutError:
        status = ProcessingStatus.TIMEOUT

    except (ArticleNotFound, AdapterNotImplemented):
        status = ProcessingStatus.PARSING_ERROR

    response = {'status': status.value, 'url': url,
                'score': score, 'words_count': words_count}
    return response
