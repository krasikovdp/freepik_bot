import requests
import os
import re
from twocaptcha import TwoCaptcha
import pickle
import threading


class Freepik:
    def __init__(self, username: str, password: str, _2captcha_key: str):
        self.username = username
        self.password = password
        self._2captcha_key = _2captcha_key
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:104.0) Gecko/20100101 Firefox/104.0'})
        self.solver = TwoCaptcha(_2captcha_key)
        self.xhr_headers = {'x-requested-with': 'XMLHttpRequest'}
        self.on_premium_end = None
        self.sitekey_re = re.compile(r'data-sitekey="(\S+)"')
        self.sitekey_re2 = re.compile(r"var RE_CAPTCHA_KEY_INVISIBLE = '(\S+)'")
        self.csrf_name_re = re.compile(r'name="csrf_name" value="(\S+)"')
        self.csrf_value_re = re.compile(r'name="csrf_value" value="(\S+)"')
        self.id_re = re.compile(r'(\d+)\.htm')

    def register_on_premium_end(self, f):
        self.on_premium_end = f

    def _solve_invisible_captcha(self, resp: requests.Response):
        try:
            sitekey = self.sitekey_re.search(resp.text).group(1)
        except AttributeError as e:
            sitekey = self.sitekey_re2.search(resp.text).group(1)
        try:
            with threading.Lock():
                return self.solver.recaptcha(sitekey=sitekey, url=resp.request.url, invisible=1)['code']
        except Exception as e:
            raise e

    def sign_in(self) -> bool:
        print('signing in')
        login_page_url = 'https://id.freepikcompany.com/login'
        sign_in_page_resp = self.session.get(login_page_url)
        csrf_name = self.csrf_name_re.search(sign_in_page_resp.text).group(1)
        csrf_value = self.csrf_value_re.search(sign_in_page_resp.text).group(1)
        captcha_token = self._solve_invisible_captcha(sign_in_page_resp)

        xhr_login_url = 'https://id.freepikcompany.com/xhr/login'
        form_data = {'client_id': 'freepik',
                     'secret': '',
                     'username': self.username,
                     'password': self.password,
                     'g-recaptcha-response': captcha_token,
                     'csrf_name': csrf_name,
                     'csrf_value': csrf_value}
        xhr_login_resp = self.session.post(xhr_login_url, form_data)

        oauth_url = xhr_login_resp.json()['data']['url']
        self.session.get(oauth_url)
        return 'GR_TOKEN' in self.session.cookies

    def _download_url_from_id(self, id_: int | str, captcha_token: str = None, retries: int = 1):
        url = f'https://www.freepik.com/xhr/download-url/{id_}'
        params = {}
        if captcha_token:
            params = {'token': captcha_token}
        resp_json = self.session.get(url, headers=self.xhr_headers, params=params).json()
        if resp_json.get('success'):
            return resp_json['url']
        elif resp_json['message'] == 'Manual validation needed':
            print(f'validating manually id_={id_}')
            if captcha_token:
                raise RuntimeError(f'Manual validation did not work {resp_json}')
            manual_validation_resp = self.session.get(resp_json['url'], headers=self.xhr_headers)
            return self._download_url_from_id(id_, self._solve_invisible_captcha(manual_validation_resp))
        elif resp_json['message'] == 'Resource is premium and user not':
            if self.on_premium_end:
                self.on_premium_end()
            else:
                raise RuntimeError(f'The premium subscription ended {resp_json}')
        else:
            raise RuntimeError(str(resp_json))

    def get_download_url(self, input_url: str):
        return self._download_url_from_id(self.id_re.search(input_url).group(1))


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
        raise RuntimeError(f"'hmac' not in download_url {resp.json()}")
    return download_url


if __name__ == '__main__':
    freepik = Freepik(os.environ['FREEPIK_USERNAME'], os.environ['FREEPIK_PASSWORD'], os.environ['2CAPTCHA_API_KEY'])
    if not os.path.exists('session.pickle'):
        print('creating new session')
        gr_token = freepik.sign_in()
        print(gr_token)
        if gr_token:
            with open('session.pickle', 'wb') as file:
                pickle.dump(freepik.session, file)
    else:
        print('loading cached session')
        with open('session.pickle', 'rb') as file:
            freepik.session = pickle.load(file)
    print(freepik._download_url_from_id(7971318))
