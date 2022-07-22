import requests
import wget
import os
from bs4 import BeautifulSoup

first_links = []
second_links = []
song_names = []


def get_link_per_page(page_number, artist_name):
    for letter in range(len(artist_name)):
        if artist_name[letter] == " ":
            artist_name = artist_name[:letter] + "+" + artist_name[letter + 1:]
    link_of_music = []
    url = f"https://praisezion.com/page/{page_number}/?s={artist_name}&submit_button=SEARCH"
    page = requests.get(url)

    soup = BeautifulSoup(page.content, "html.parser")
    results = soup.findAll("div", class_="title")

    for line in results:
        tag = line.find('a')
        link_of_music.append(tag.get('href'))
    return link_of_music


def get_downloadable_link_per_page(page_number, artist_name):
    link_of_music = get_link_per_page(page_number, artist_name)
    list_of_downloadable_link = []
    for link in range(len(link_of_music)):
        url = link_of_music[link]
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")
        results = soup.findAll("a", class_="fasc-button fasc-size-large fasc-type-glossy fasc-rounded-medium")

        for line in results:
            with open(f"{artist_name}.txt", "a") as f:
                the_link = line.get('href')
                f.write(the_link + "\n")
                list_of_downloadable_link.append(the_link)


artist_name = input("Enter the artist name: ")


def download_song_links():
    number_of_page = int(input("Enter the number of page: "))
    for page in range(number_of_page):
        print(f"page {page + 1}")
        get_downloadable_link_per_page(page, artist_name)
        print("please wait for a while")


temporary_file_name = "temp " + artist_name + '.txt'


# def write_temp_file(link):
#     os.system("cd")
#
#
#
#
#
#
#
#
# if __name__ == "__main__":
#     #download_song_links()
#     print("done")
