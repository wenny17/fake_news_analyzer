import asyncio
from collections import namedtuple
from enum import Enum
import re

import aiohttp
from bs4 import BeautifulSoup
import pymorphy2

from utils import create_handy_nursery
from adapters import SANITIZERS, ArticleNotFound
from text_tools import split_by_words, calculate_jaundice_rate


Article = namedtuple('Article', ('title', 'status', 'rate', 'words_count'))
pattern = re.compile(r'\/\/([a-zA-Z0-9\.]+)')


class ProcessingStatus(Enum):
    OK = 'OK'
    FETCH_ERROR = 'FETCH_ERROR'
    PARSING_ERROR = 'PARSING_ERROR'
    TIMEOUT = 'TIMEOUT'

    def __str__(self):
        return str(self.value)


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


def get_charged_words():
    with open('charged_dict/negative_words.txt') as f:
        words = f.read()
    return words.split()


def convert_domain_name(url):
    domain = pattern.search(url).group(1)
    converted_domain = re.sub(r'\.', '_', domain)
    return converted_domain, domain


async def process_article(session, morph, charged_words, url):
    try:
        html = await fetch(session, url)
    except aiohttp.ClientError:
        return Article('URL not exist',
                       ProcessingStatus.FETCH_ERROR,
                       None, None)

    converted_domain, domain = convert_domain_name(url)
    sanitaze_html = SANITIZERS['inosmi_ru']

    # try:
    #     sanitaze_html = SANITIZERS[converted_domain]
    # except KeyError:
    #     return Article(f'Статья на {domain}',
    #                    ProcessingStatus.PARSING_ERROR,
    #                    None, None)

    try:
        text = sanitaze_html(html, plaintext=True)
    except ArticleNotFound:
        return Article(f'Статья на {domain}',
                       ProcessingStatus.PARSING_ERROR,
                       None, None)

    soup = BeautifulSoup(html, 'lxml')
    title = soup.find('h1', class_='article-header__title').text
    words = split_by_words(morph, text)
    rate = calculate_jaundice_rate(words, charged_words)
    return Article(title, ProcessingStatus.OK, rate, len(words))


async def main():
    TEST_ARTICLES = [
        'https://inosmi.ru/economic/20190629/245384784.html',
        'https://inosmi.ru/politic/20191123/246296868.html',
        'https://inosmi.ru/science/20191123/246295060.html',
        'https://inosmi.ru/science/20191123/246253054.html',
        'https://inosmi.ru/politic/20191123/246296472.html',
        'https://inosmi.ru/politic/20191123/246296472.html5',
        'https://lenta.ru/news/2019/11/24/penalty/',
    ]
    morph = pymorphy2.MorphAnalyzer()
    charged_words = get_charged_words()
    async with aiohttp.ClientSession() as session:
        async with create_handy_nursery() as nursery:
            tasks = []
            for url in TEST_ARTICLES:
                task = nursery.start_soon(process_article(session, morph,
                                                          charged_words, url))
                tasks.append(task)
        for i in tasks:
            print(i.result().title)
            print(i.result().status)
            print(i.result().rate)
            print(i.result().words_count)


asyncio.run(main())
