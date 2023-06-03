import os
import time

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC

from get_vector_from_pretrain_w2v import get_vector


class SvmModel:
    def __init__(self, embedding_data_filename, w2v):
        data = pd.read_csv(embedding_data_filename,delimiter=';', encoding='cp1251')
        self.x, y = np.asarray(data['Associations']), np.asarray(data['Topics'])
        self.svm_classifier = SVC(kernel='sigmoid')
        self.label_map = {cat: index for index, cat in enumerate(np.unique(y))}
        self.y_prep = np.asarray([self.label_map[l] for l in y])
        self.x_data = np.asarray([np.asarray(get_vector(w2v, token)) for token in self.x])

    def train_model(self):
        x_train, x_test, y_train, y_test = train_test_split(self.x_data, self.y_prep, test_size=0.2, random_state=42)
        self.svm_classifier.fit(x_train, y_train)
        return self.svm_classifier.score(x_test, y_test)

    def predict(self, list_vectors):
        res = [self.svm_classifier.predict(vector.reshape(1, -1)) for vector in list_vectors]
        return res


def get_topic(vectors, w2v_model):
    print('Обучение модели SVM')
    emb_data_path = os.getcwd() + '/SVM_model/'
    emb_data_filename = emb_data_path + 'emb_data.csv'
    svm_model = SvmModel(emb_data_filename, w2v_model)
    score = svm_model.train_model()
    print(f'Точность модели составила >>> {round(score * 100)}%\n')

    start_classification = time.time()
    result = svm_model.predict(vectors)
    print(f'Время классификации составило: {time.time() - start_classification:.2f} сек\n')

    russian_topic = ('Автомобили', 'Еда и кулинария', 'IT-сфера', 'Политика')
    russian_label_map = {key: val for key, val in zip(svm_model.label_map, russian_topic)}
    values, counts = np.unique(result, return_counts=True)
    ind = np.argmax(counts)
    num_topic = values[ind]
    for key, val in svm_model.label_map.items():
        if num_topic == val:
            return russian_label_map[key]


