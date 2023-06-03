from urllib.parse import urlparse
from bs4 import BeautifulSoup
import requests


def get_username(url):
    query = urlparse(url)
    if 'featured' in query.path:
        return query.path.split('@')[1].split('/')[0]
    return query.path.split('@')[1]


def get_id(url):
    query = url.split('/')
    return query[-1]


def get_yt_channel_id(url):
    modern_url = url
    soup = BeautifulSoup(requests.get(modern_url).content, "html.parser")

    try:
        return soup.find("meta", {"itemprop": "channelId"})["content"]
    except TypeError:
        try:
            id = get_id(soup.find('link', {"itemprop": "url"})["href"])
            return id
        except TypeError:
            return "Некорректное имя пользователя."

