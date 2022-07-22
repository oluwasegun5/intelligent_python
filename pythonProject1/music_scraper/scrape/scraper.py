from bs4 import BeautifulSoup
import requests
from wget import download, detect_filename


def preferred_website():
    website = int(input(""""
    1 => praisezion.com
    2 => soundof9ja.com
    """))
    if website == 1:
        return 'praisezion.com'
    elif website == 2:
        return "soundof9ja.com"
    else:
        preferred_website()


def get_first_link(website=preferred_website(), number_of_pages=1, artist_name="travins greene"):
    url = f"https://{website}/page/{number_of_pages}/?s={artist_name}"
    page = requests.get(url)
    soup = BeautifulSoup.find()
    soup
