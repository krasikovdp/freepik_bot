import requests
import os
import re


class Freepik:
    def __init__(self, gr_token: str):
        self.gr_token = gr_token

    def input_url2download_url(self, input_url: str):
        return self.id2download_url(self.input_url2id(input_url))

    def input_url2id(self, input_url: str):
        return re.search(r'(\d+)\.htm', input_url).group(1)

    def id2download_url(self, id_):
        url = f'https://www.freepik.com/xhr/download-url/{id_}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:104.0) Gecko/20100101 Firefox/104.0',
            'x-requested-with': 'XMLHttpRequest',
            'Cookie': f'GR_TOKEN={self.gr_token}',
        }
        resp = requests.get(url, headers=headers)
        return resp.json()['url']


if __name__ == '__main__':
    f = Freepik(os.environ['FREEPIK_GR_TOKEN'])
    print(f.id2download_url(26521084))
