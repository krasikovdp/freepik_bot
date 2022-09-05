import requests
from bs4 import BeautifulSoup


def flaticon_input_url2download_url(input_url: str):
    soup = BeautifulSoup(requests.get(input_url).text, parser='html.parser')
    return soup.find(class_='main-icon-without-slide').img.attrs['src']
