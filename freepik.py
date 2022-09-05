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
    return resp.json()['url']


if __name__ == '__main__':
    # f = Freepik(os.environ['FREEPIK_GR_TOKEN'])
    # print(f.id2download_url(26521084))
    pass
