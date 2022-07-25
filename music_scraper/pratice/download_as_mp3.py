import requests
from selenium import webdriver

if __name__ == "__main__":

    browser = webdriver.Chrome

    with open("dunsin oyekan.txt", "r+")as file:
        for link in file:
            browser.get("https://files.soundof9ja.com/wp-content/uploads/2022/01/At-the-Cross-Hillsong-WorshipSOUNDOFNAJIA.mp3")

