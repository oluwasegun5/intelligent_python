import requests
from bs4 import BeautifulSoup

if __name__ == "__main__":
    URL = "https://realpython.github.io/fake-jobs/"
    page = requests.get(URL)

    soup = BeautifulSoup(page.content, "html.parser")

    results = soup.find(id="ResultsContainer")
    job_elements = results.find_all("div", class_="card-content")

    python_jobs = results.find_all('h2', string=lambda text: "python" in text.lower())

    for job_element in job_elements:
        job = job_element.find("h2", class_='title')
        company = job_element.find("h3", class_='company')
        location = job_element.find("p", class_='location')
        print(f'job: {job.text.strip()}\ncompany: {company.text.strip()}\nlocation: {location.text.strip()}\n\n')
