import json
import os

from urllib.request import Request, urlopen
from youtube_transcript_api import YouTubeTranscriptApi
import googleapiclient.discovery

from parsing_data.data_from_url import get_username, get_yt_channel_id


# получаем id первых n видео с канала
def get_id_video_from_channel(channel_id, api_key, n):
    base_search_url = 'https://www.googleapis.com/youtube/v3/search?'

    first_url = base_search_url + \
                'key={}&channelId={}&part=snippet,id&order=date&maxResults=25'.format(api_key,channel_id)

    video_links = []
    url = first_url
    while True:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        inp = urlopen(req)
        resp = json.load(inp)

        try:
            for i in resp['items']:
                if i['id']['kind'] == "youtube#video":
                    video_links.append(i['id']['videoId'])
                    if len(video_links) == n:
                        raise Exception

            next_page_token = resp['nextPageToken']
            url = first_url + '&pageToken={}'.format(next_page_token)
        except Exception:
            break
    return video_links


# Функция для скачивания корневых комментариев
def get_comments(video_id, api_key, nextPageToken=None):
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"

    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=api_key)

    request = youtube.commentThreads().list(
        part="id,snippet",
        maxResults=100,
        order="relevance",
        pageToken=nextPageToken,
        videoId=video_id
    )
    response = request.execute()
    return response


# Функция для скачивания ответов на комментарии
def get_child_comments(NextParentId, api_key, nextPageToken=None):
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"

    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=api_key)

    request = youtube.comments().list(
        part="id,snippet",
        maxResults=100,
        pageToken=nextPageToken,
        parentId=NextParentId
    )
    response = request.execute()
    return response


# Главная функция
def parse_data(url_channel, api_key, video_count):
    user_name = get_username(url_channel)
    print(f'Имя канала {user_name}')

    id_channel = get_yt_channel_id(url_channel)
    print(f'ID канала {id_channel}\n')

    url_template = 'https://www.youtube.com/watch?v={id_video}&ab_channel={user_name}'
    videos_id = get_id_video_from_channel(id_channel, api_key, video_count)
    data = []
    for number, id in enumerate(videos_id):
        print(f'Загрузка данных видео №{number + 1}')
        print(f'ID видео [{id}]\t')
        print(f'url адрес видео [{url_template.format(id_video=id, user_name=user_name)}]')
        try:
            response = get_comments(id, api_key)
        except Exception:
            print(f'Невозможно загрузить данные видео: {id}\n')
            continue
        items = response.get("items")
        nextPageToken = response.get("nextPageToken")  # скачивается порциями, на каждую следующую выдаётся указатель

        try:
            while nextPageToken is not None:
                response = get_comments(id, api_key, nextPageToken)
                nextPageToken = response.get("nextPageToken")
                items = items + response.get("items")
        except Exception:
            pass

        print(f'Загружено комментариев >>> {len(items)}')  # Отображаем количество скачаных комментариев

        # Скачиваем реплаи на комментарии
        replies = []
        for line in items:  # Проходим по корневым комментам
            if line.get("snippet").get("totalReplyCount") > 0:  # если есть реплаи
                try:
                    response = get_child_comments(line.get("snippet").get("topLevelComment").get("id"), api_key)
                except Exception:
                    continue
                replies = replies + response.get("items")
                nextPageToken = response.get("nextPageToken")

                try:
                    while nextPageToken is not None:  # догружаем реплаи, если есть ещё порции
                        response = get_child_comments(line.get("snippet").get("topLevelComment").get("id"),
                                                      api_key,
                                                      nextPageToken)
                        nextPageToken = response.get("nextPageToken")
                        replies = replies + response.get("items")
                except:
                    pass

        print(f'Загружено ответов на комментарии >>> {len(replies)}')

        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(id, languages=['ru'])
            print(f'Загружено строк субтитров >>> {len(transcript_list)}\n')
            for item in transcript_list:
                data.append(item['text'])
        except Exception:
            print(f'Невозможно загрузить субтитры видео: {id}\n')

        for item in items:
            data.append(item['snippet']['topLevelComment']['snippet']['textOriginal'])

        for item in replies:
            data.append(item['snippet']['textOriginal'])

    return data

