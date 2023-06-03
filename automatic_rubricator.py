import asyncio
import os
import time
from concurrent.futures import ProcessPoolExecutor
from functools import partial, reduce
from multiprocessing import cpu_count

import numpy
from gensim.models import KeyedVectors
from pymystem3 import Mystem

from SVM_model import get_topic
from get_vector_from_pretrain_w2v import get_vector
from preprocess_data import preprocess
from parsing_data import parse_data


def initial():
    api_key_url = 'https://console.cloud.google.com/apis/dashboard?project=midyear-choir-384317'
    url_channel = input('Введите URL-адрес YouTube канала:\n<<<')
    developer_key = input(f'Введите ваш GOOGLE-API-KEY [получить {api_key_url}]:\n<<<')
    video_count = int(input(f'Введите количество видео для получения данных:\n<<<'))
    mystem = Mystem()
    stop_words = [line.strip() for line in open('stop_words.txt', 'r', encoding='utf-8')]
    project_path = os.getcwd()
    vectors_data_filename = project_path + '/fasttext_vectors_data/word2vecWIKI.model'
    w2v_model = KeyedVectors.load(vectors_data_filename, mmap='r')
    return mystem, stop_words, w2v_model, url_channel, developer_key, video_count


async def main():
    mystem, stop_words, w2v_model, url_channel, developer_key, video_count = initial()
    start_parsing = time.time()
    data = parse_data(url_channel, developer_key, video_count)
    print(f'Время загрузки данных: {time.time() - start_parsing:.2f} сек\n'
          f'Удалось загрузить {len(data)} строк')

    # делим массив данных на подмассивы в количество ядер процессора
    delimiter = len(data) // cpu_count()
    data = [' '.join(text for text in data[i: i + delimiter]) for i in range(0, len(data), delimiter)]

    start_preprocessing = time.time()
    print(f'\nСоздается {cpu_count()} процессов')
    with ProcessPoolExecutor() as process_pool:
        loop = asyncio.get_running_loop()
        calls = [partial(preprocess, text, mystem, stop_words) for text in data]
        call_coros = [loop.run_in_executor(process_pool, call) for call in calls]
        results = await asyncio.gather(*call_coros)
    print(f'Время обработки текстов: {time.time() - start_preprocessing:.2f} сек\n')

    # соединяем данные после предварительной обработки
    tokens = reduce(lambda x, y: x + y, results)
    tokens = set(tokens)

    # получаем веторное представление слов
    vectors = [get_vector(w2v_model, token) for token in tokens]
    vectors = [vector for vector in vectors if isinstance(vector, numpy.memmap)]
    print(f'Удалось получить {len(vectors)} векторов\n')

    #классифицируем данные с помощью предварительно обученной модели SVM
    topic = get_topic(vectors, w2v_model)
    print(f'Тема YouTube-канала [{url_channel}] >>> {topic}')


if __name__ == '__main__':
    asyncio.run(main())