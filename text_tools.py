import asyncio
import os
import re
import string
from typing import List

import pymorphy2

from adapters import SANITIZERS, AdapterNotImplemented


CHARGED_DICT_DIRECTORY = 'charged_dict'
pattern = re.compile(r'\/\/([a-zA-Z0-9\.]+)')


def _clean_word(word):
    word = word.replace('«', '').replace('»', '').replace('…', '')
    # FIXME какие еще знаки пунктуации часто встречаются ?
    word = word.strip(string.punctuation)
    return word


async def split_by_words(morph, text):
    """Учитывает знаки пунктуации, регистр и словоформы, выкидывает предлоги.
    """
    words = []
    for word in text.split():
        cleaned_word = _clean_word(word)
        normalized_word = morph.parse(cleaned_word)[0].normal_form
        if len(normalized_word) > 2 or normalized_word == 'не':
            words.append(normalized_word)
        await asyncio.sleep(0)
    return words


async def __test_split_by_words():
    morph = pymorphy2.MorphAnalyzer()
    assert await split_by_words(morph,'Во-первых, он хочет, чтобы') == ['во-первых', 'хотеть', 'чтобы']

    assert await split_by_words(morph, '«Удивительно, но это стало началом!»') == ['удивительно', 'это', 'стать', 'начало']


def test_split_by_words():
    asyncio.run(__test_split_by_words())


def calculate_jaundice_rate(article_words, charged_words):
    """Расчитывает желтушность текста, принимает список "заряженных" слов и ищет их внутри article_words."""

    if not article_words:
        return 0.0

    found_charged_words = [word for word in article_words if word in set(charged_words)]

    score = len(found_charged_words) / len(article_words) * 100

    return round(score, 2)


def test_calculate_jaundice_rate():
    assert -0.01 < calculate_jaundice_rate([], []) < 0.01
    assert 33.0 < calculate_jaundice_rate(['все', 'аутсайдер', 'побег'], ['аутсайдер', 'банкротство']) < 34.0


def get_charged_words(path=CHARGED_DICT_DIRECTORY) -> List[str]:
    words = []
    words_path = os.path.join(os.getcwd(), CHARGED_DICT_DIRECTORY)
    for file in os.listdir(words_path):
        if file.endswith('.txt'):
            with open(os.path.join(words_path, file)) as f:
                words.extend(f.read().split())
    return words


def convert_domain_name(url: str) -> str:
    """Convert url
    something like: google.com -> google_com
    """
    domain = pattern.search(url).group(1)
    converted_domain = re.sub(r'\.', '_', domain)
    return converted_domain


def sanitize_html(html: str, url: str) -> str:
    converted_domain = convert_domain_name(url)
    sanitazer = SANITIZERS.get(converted_domain)
    if sanitazer is None:
        raise AdapterNotImplemented
    return sanitazer(html, plaintext=True)
