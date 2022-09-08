import requests
import os
import re


def freepik_input_url2download_url(input_url: str):
    return freepik_id2download_url(freepik_input_url2id(input_url))


def freepik_input_url2id(input_url: str):
    return re.search(r'(\d+)\.htm', input_url).group(1)


def freepik_id2download_url(id_):
    url = f'https://www.freepik.com/xhr/download-url/{id_}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:104.0) Gecko/20100101 Firefox/104.0',
        'x-requested-with': 'XMLHttpRequest',
        'Cookie': f'GR_TOKEN={os.environ["FREEPIK_GR_TOKEN"]}',
    }
    resp = requests.get(url, headers=headers)
    download_url = resp.json()['url']
    if 'hmac' not in download_url:
        raise RuntimeError("'hmac' not in download_url, maybe update FREEPIK_GR_TOKEN")
    return


if __name__ == '__main__':
    print(freepik_id2download_url(11712558))  # 16618863 com 11712558 es
    pass
