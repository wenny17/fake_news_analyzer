import asyncio
from collections import namedtuple

import aiohttp
from bs4 import BeautifulSoup
import pymorphy2
from utils import create_handy_nursery

from adapters import SANITIZERS
from text_tools import split_by_words, calculate_jaundice_rate


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


def get_charged_words():
    with open('charged_dict/negative_words.txt') as f:
        words = f.read()
    return words.split()


async def process_article(session, morph, charged_words, url):
    html = await fetch(session, url)
    soup = BeautifulSoup(html, 'lxml')
    title = soup.find('h1', class_='article-header__title').text
    sanitaze_html = SANITIZERS['inosmi_ru']
    text = sanitaze_html(html, plaintext=True)
    words = split_by_words(morph, text)
    rate = calculate_jaundice_rate(words, charged_words)
    Arcticle = namedtuple('Article', ('title', 'rate', 'words_count'))
    return Arcticle(title, rate, len(words))


async def main():
    TEST_ARTICLES = [
        'https://inosmi.ru/economic/20190629/245384784.html',
        'https://inosmi.ru/politic/20191123/246296868.html',
        'https://inosmi.ru/science/20191123/246295060.html',
        'https://inosmi.ru/science/20191123/246253054.html',
        'https://inosmi.ru/politic/20191123/246296472.html',
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
            #r = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            #print(r)
            while tasks:
                task = await asyncio.wait(tasks,
                                      return_when=asyncio.FIRST_COMPLETED)
                print(tasks)
                tasks.remove(task)


asyncio.run(main())
