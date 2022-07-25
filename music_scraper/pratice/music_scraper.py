import requests
from bs4 import BeautifulSoup
import time


def get_link_per_page(page_number, artist_name):
    for letter in range(len(artist_name)):
        if artist_name[letter] == " ":
            artist_name = artist_name[:letter] + "+" + artist_name[letter+1:]
    link_of_music = []
    url = f"https://soundof9ja.com/page/{page_number}/?s={artist_name}"
    page = requests.get(url)

    soup = BeautifulSoup(page.content, "html.parser")
    results = soup.findAll("h3", class_="entry-title mh-loop-title")

    for line in results:
        tag = line.find('a')
        music_link = tag.get('href')

        if music_link.endswith("/"):
            link_of_music.append(music_link)
    return link_of_music


def get_downloadable_link_per_page(page_number, artist_name):
    link_of_music = get_link_per_page(page_number, artist_name)
    list_of_downloadable_link = []
    for link in range(len(link_of_music)):
        url = link_of_music[link]

        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")
        results = soup.find_all('a', class_="fasc-button fasc-size-medium fasc-type-flat")

        for line in results:
            with open(f"{artist_name}.txt", "a") as f:
                f.write(line.get('href') + "\n")
                list_of_downloadable_link.append(line.get('href'))


def download_song_links():
    artist_name = input("Enter the artist name: ")
    number_of_page = int(input("Enter the number of page: "))
    for page in range(number_of_page):
        print(f"page {page+1}")
        get_downloadable_link_per_page(page, artist_name)
        print("please wait for a while")
        time.sleep(30)


if __name__ == "__main__":
    download_song_links()
