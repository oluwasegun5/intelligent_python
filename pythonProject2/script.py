import urllib
import time
from datetime import datetime, timedelta

import requests
from requests import adapters
import ssl
from urllib3 import poolmanager
from lxml import html
import json

from twocaptcha import TwoCaptcha

from workers_main import dramatiq
from redis_proxy import set_course_cookie, get_course_cookie, set_course_token, get_course_token
from course_cred import USERNAME_1, PASSWORD_1, USERNAME_2, PASSWORD_2

API_KEY = 'xxxxxxxxxxxxxxxxxxxx'


headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'ru-RU,ru;q=0.9',
    'Connection': 'keep-alive',
    'Host': 'www.of.moncompteformation.gouv.fr',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36'
}

credentials = {
    '1': {
        "USERNAME": USERNAME_1,
        "PASSWORD": PASSWORD_1
    },
    '2': {
        "USERNAME": USERNAME_2,
        "PASSWORD": PASSWORD_2
        }}

class TLSAdapter(adapters.HTTPAdapter):

    def init_poolmanager(self, connections, maxsize, block=False):
        """Create and initialize the urllib3 PoolManager."""
        ctx = ssl.create_default_context()
        ctx.set_ciphers('DEFAULT@SECLEVEL=1')
        self.poolmanager = poolmanager.PoolManager(
                num_pools=connections,
                maxsize=maxsize,
                block=block,
                ssl_version=ssl.PROTOCOL_TLS,
                ssl_context=ctx)

def wrapper(url, credentials_type):
    url = url.replace('/#', '?')
    query_params = urllib.parse.urlparse(url)
    query_params = dict(urllib.parse.parse_qsl(query_params.query))
    token = f'{query_params["token_type"]} {query_params["access_token"]}'
    print(token)
    set_course_token(credentials_type, token)

def autorization(credentials_type):
    session = requests.Session()
    session.mount('https://', TLSAdapter())
    print(f'start aytorization {credentials_type}')
    credentials_type = str(credentials_type)
    start_url = 'https://www.of.moncompteformation.gouv.fr/idp/edof/authorize'

    response = session.get(start_url, headers=headers)
    page = html.fromstring(response.content)
    exectuion_value = page.xpath('//*[@name="execution"]/@value')[0].strip()
    sitekey_value = page.xpath('//button/@data-sitekey')[0].strip()

    url = response.url
    print('2recaptcha')
    solver = TwoCaptcha(API_KEY)
    result = solver.recaptcha(
        sitekey=sitekey_value,
        url=url,
        invisible=1
    )
    recaptcha_response = result.get('code')

    login_data = {
        'username': credentials[credentials_type]['USERNAME'],
        'password': credentials[credentials_type]['PASSWORD'],
        'execution': exectuion_value,
        '_eventId': 'submit',
        'submit': 'Se connecter',
        'g-recaptcha-response': recaptcha_response
    }

    print('step', 2, url)
    response = session.post(url, data=login_data, headers=headers)
    print('step', 3, url)
    response = session.get(start_url, headers=headers)
    wrapper(response.url, credentials_type)

def result_processed(json_data):
    try:
        data = {}
        data['dossierId'] = json_data.get('id', '')
        data['student'] = {}
        student_data = json_data.get('attendee', {})
        data['student']['firstname'] = student_data.get('firstName', '').encode().decode("UTF-8")
        data['student']['lastname'] = student_data.get('lastName', '').encode().decode("UTF-8")
        data['student']['email'] = student_data.get('email', '')
        data['student']['phone'] = student_data.get('phoneNumber', '')
        addres_data = student_data.get('address', {})
        address_keys = ["number", "roadType", "roadName", "residence"]
        address_list = []
        for key in address_keys:
            item = addres_data.get(key, None)
            if item:
                address_list.append(item.encode().decode("UTF-8"))
        data['student']['address'] = " ".join(address_list)
        data['student']['postalcode'] = addres_data.get('zipCode', '')
        data['student']['city'] = addres_data.get('city', '')
        data['course'] = {}
        course_data = json_data.get('trainingActionInfo', '')
        data['course']['title'] = course_data.get('title', '').encode().decode("UTF-8")
        data['course']['courseID'] = json_data.get('trainingId', ' _ ').split('_')[1].strip()
        data['course']['actionID'] = json_data.get('trainingActionId', ' _ ').split('_')[1].strip()
        data['course']['sessionID'] = course_data.get('sessionId', ' _ ').split('_')[1].strip()
        data['course']['price'] = course_data.get('totalIncl', '')
        data['course']['duration'] = course_data.get('indicativeDuration', '')
        data['history'] = []
        for item in json_data['history']:
            data['history'].append(f'{item["date"]} {item["label"].encode().decode("UTF-8")}')
        return {'status': 'ok', 'data': data}
    except Exception as e:
        return {
            'status': 'failed',
            'error': f'{e}'
        }


@dramatiq.actor(queue_name='course_parser', store_results=True, max_retries=1, max_age=300000)
def course_parser(url_code, credentials_type):
    print(f"{url_code}, {credentials_type}")
    current_headers = headers.copy()
    url = f'https://www.of.moncompteformation.gouv.fr/edof-api/v1/api/private/organisms/current/registration-folders/{url_code}'
    for _ in range(2):
        current_headers['Authorization'] = get_course_token(credentials_type)
        print(current_headers['Authorization'] )
        try:
            response = requests.get(url, headers=current_headers, timeout=15)
            print("get_data", response)
            if response.status_code == 200:
                break
            elif response.status_code == 401:
                autorization(credentials_type)
            elif response.status_code == 404:
                return {"status": "ko", "id": url_code}
        except:
            pass
        try:
            autorization(credentials_type)
        except:
            return {"status": "ko", "id": url_code}
    return response.json()

@dramatiq.actor(queue_name='course_parser', store_results=True, max_retries=1, max_age=300000)
def monocourse_parser(query, first=False):
    session = requests.Session()
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "content-type": "application/json",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    }
    start_url = f"https://www.moncompteformation.gouv.fr/espace-prive/sl6-portail-web/public/publication/alertes?_t={time.time() * 1000}"
    url = f"https://www.moncompteformation.gouv.fr/espace-prive/sl6-portail-web/public/formations?_t={time.time() * 1000}"
    session.get(start_url, headers=headers)
    response = session.post(url, data=query, headers=headers)
    data = response.json()
    if first:
        items = data["numberOfItem"]
        pages = items//10
        pages += 1 if items % 10 != 0 else 0
        query = json.loads(query)
        query_list = [json.dumps({**query, "debutPagination": page}) for page in range(2, pages+1)]
        groups_task = dramatiq.group([monocourse_parser.message(query) for query in query_list]).run()
        for res in groups_task.get_results(block=True, timeout=30_000):
            data['item'].extend(res['item'])
    return data


def mono_start(query):
    data = monocourse_parser.send(query, True)
    data = data.get_result(block=True, timeout=300_000)
    return data


def course_start(url, credentials_type):
    url = str(url).strip()
    credentials_type = str(credentials_type).strip()
    data = course_parser.send(url, credentials_type)
    data = data.get_result(block=True, timeout=300_000)
    return data


@dramatiq.actor(queue_name='course_parser', store_results=True, max_retries=1, max_age=300000)
def in_func(data):
    current_headers = headers.copy()
    url = f"https://www.of.moncompteformation.gouv.fr/edof-api/v1/api/private/organisms/current/registration-folders/{data['dossier']}/status"
    credentials_type = str(data['of'])
    date = data.get("date", datetime.now().date().isoformat())
    #date = datetime.fromisoformat(date) - timedelta(days=1)
    #date = date.replace(hour=23)
    #date = date.isoformat() + ".000Z"
    put_data = {
            "date": date,
            "state": "IN_TRAINING"
        }
    for _ in range(2):
        current_headers['Authorization'] = get_course_token(credentials_type)
        print(current_headers['Authorization'] )
        try:
            response = requests.put(url, json=put_data, headers=current_headers, timeout=15)
            print("in_func")
            if response.status_code == 200:
                break
            elif response.status_code == 404:
                return "ko"
            elif response.status_code == 401:
                autorization(credentials_type)
            else:
                return "ko"
        except:
            pass
        try:
            autorization(credentials_type)
        except:
            return "ko"
    return "ok"


@dramatiq.actor(queue_name='course_parser', store_results=True, max_retries=1, max_age=300000)
def out_func(data):
    current_headers = headers.copy()
    url = f"https://www.of.moncompteformation.gouv.fr/edof-api/v1/api/private/organisms/current/registration-folders/{data['dossier']}/status"
    credentials_type = str(data['of'])
    date = data.get("date", datetime.now().date().isoformat())
    #date = datetime.fromisoformat(date) - timedelta(days=1)
    #date = date.replace(hour=23)
    #date = date.isoformat() + ".000Z"
    put_data = {
        "terminatedDate": date,
        "quitReason": {
                "code": "8",
                "label": "Fin prévue de l'action de formation"
            },
        "state": "TERMINATED"
    }
    for _ in range(2):
        current_headers['Authorization'] = get_course_token(credentials_type)
        print(current_headers['Authorization'] )
        try:
            response = requests.put(url, json=put_data, headers=current_headers, timeout=15)
            print("out_func")
            if response.status_code == 200:
                break
            elif response.status_code == 404:
                return "ko"
            elif response.status_code == 401:
                autorization(credentials_type)
            else:
                return "ko"
        except:
            pass
        try:
            autorization(credentials_type)
        except:
            return "ko"
    return "ok"


@dramatiq.actor(queue_name='course_parser', store_results=True, max_retries=1, max_age=300000)
def update_func(in_data):
    try:
        current_headers = headers.copy()
        credentials_type = in_data['of']
        url = f"https://www.of.moncompteformation.gouv.fr/edof-api/v1/api/private/organisms/current/registration-folders/{in_data['dossier']}"
        data = course_parser(in_data["dossier"], str(in_data["of"]).strip())
        data['trainingActionInfo']['companyName'] = in_data['companyName']
        data['trainingId'] = in_data['trainingId']
        data['trainingActionInfo']['title'] = in_data['title']
        data['trainingActionInfo']['trainingGoal'] = in_data['trainingGoal']
        data['trainingActionId'] = in_data['trainingActionId']
        data['trainingActionInfo']['isConditionsPrerequisites'] = True if in_data['isConditionsPrerequisites'] != "Non" else False
        data['trainingActionInfo']['sessionStartDate'] = in_data["sessionStartDate"]
        data['trainingActionInfo']['sessionEndDate'] = in_data["sessionEndDate"]
        data['trainingActionInfo']['sessionId'] = in_data['sessionId']
        data['trainingActionInfo']['teachingModalities'] = str(in_data['teachingModalities'])
        if not data['trainingActionInfo']['address']:
            data['trainingActionInfo']['address'] = {}
        data['trainingActionInfo']['address']['additionalAddress'] = in_data['additionalAddress'] if in_data['additionalAddress'] else None
        data['trainingActionInfo']['address']['residence'] = in_data['residence'] if in_data['residence'] else None
        data['trainingActionInfo']['address']['number'] = str(in_data['number']) if in_data['number'] else None
        data['trainingActionInfo']['address']['repetitionIndex'] = str(in_data['repetitionIndex']) if in_data['repetitionIndex'] else None
        data['trainingActionInfo']['address']['roadType'] = str(in_data['roadType']).upper() if in_data['roadType'] else None
        data['trainingActionInfo']['address']['roadName'] = str(in_data['roadName']) if in_data['roadName'] else None
        data['trainingActionInfo']['address']['postBox'] = str(in_data['postBox']) if in_data['postBox'] else None
        data['trainingActionInfo']['address']['zipCode'] = str(in_data['zipCode']) if in_data['zipCode'] else None
        data['trainingActionInfo']['address']['city'] = str(in_data['city']) if in_data['city'] else None
        data['trainingActionInfo']['expectedResult'] = in_data['expectedResult']
        data['trainingActionInfo']['content'] = in_data['content']
        data['trainingActionInfo']['typeOfTrainingCourse'] = int(in_data['typeOfTrainingCourse'])
        data['trainingActionInfo']['conditionsPrerequisitesDetails'] = in_data['conditionsPrerequisitesDetails'] if in_data['conditionsPrerequisitesDetails'] and in_data['conditionsPrerequisitesDetails'] != "N/A" else None
        t_paces = [int(key.split("_")[1]) for key in in_data.keys() if "trainingPace" in key]
        paces = [0 for _ in range(len(t_paces))]
        for pace in t_paces:
            paces[pace-1] = str(in_data[f"trainingPace_{pace}"])
        data['trainingActionInfo']['trainingPaces'] = paces
        data['trainingActionInfo']['additionalFees'] = int(in_data['additionalFees']) if in_data['additionalFees'] else 0
        data['trainingActionInfo']['additionalFeesDetails'] = in_data['additionalFeesDetails'] if in_data['additionalFeesDetails'] else None
        data['trainingActionInfo']['vat'] = int(float(in_data['vat'])) if in_data['vat'] else 0
        data['trainingActionInfo']['vatExclTax5'] = in_data['vatExclTax5'] if in_data['vatExclTax5'] else 0
        data['trainingActionInfo']['vatInclTax5'] = in_data['vatInclTax5'] if in_data['vatInclTax5'] else 0
        data['trainingActionInfo']['vatExclTax20'] = in_data['vatExclTax20'] if in_data['vatExclTax20'] else 0
        data['trainingActionInfo']['vatInclTax20'] = in_data['vatInclTax20'] if in_data['vatInclTax20'] else 0
        data['trainingActionInfo']['totalExcl'] = int(float(in_data['totalExcl'])) if in_data['totalExcl'] else 0
        data['trainingActionInfo']['totalIncl'] = int(float(in_data['totalIncl'])) if in_data['totalIncl'] else 0
        data['trainingActionInfo']['weeklyDuration'] = int(in_data['weeklyDuration']) if in_data['weeklyDuration'] else 0
        data['trainingActionInfo']['indicativeDuration'] = int(in_data['indicativeDuration']) if in_data['indicativeDuration'] else 0
        data['trainingActionInfo']['hoursInCenter'] = int(in_data['hoursInCenter']) if in_data['hoursInCenter'] else 0
        data['trainingActionInfo']['hoursInCompany'] = in_data['hoursInCompany'] if in_data['hoursInCompany'] else 0
    except Exception as e:
        print(e)
        return "ko"
    for _ in range(2):
        current_headers['Authorization'] = get_course_token(credentials_type)
        print(current_headers['Authorization'] )
        try:
            print(json.dumps(data))
            response = requests.put(url, json=data, headers=current_headers, timeout=15)
            print("update_func")
            print(response)
            print(response.text)
            if response.status_code == 200:
                break
            elif response.status_code == 404:
                return "ko"
            elif response.status_code == 401:
                autorization(credentials_type)
            else:
                return "ko"
        except:
            pass
        try:
            autorization(credentials_type)
        except:
            return "ko"
    return "ok"


@dramatiq.actor(queue_name='course_parser', store_results=True, max_retries=1, max_age=300000)
def done_func(in_data):
    current_headers = headers.copy()
    credentials_type = in_data['of']
    url = f"https://www.of.moncompteformation.gouv.fr/edof-api/v1/api/private/organisms/current/registration-folders/{in_data['dossier']}/status"
    put_data = {
        "completed":True,
        "absenceUnit":"",
        "absenceDuration":0,
        "achievementRate":100,
        "forceMajeureAbsence":False,
        "state":"SERVICE_DONE_DECLARED"
        }
    for _ in range(2):
        current_headers['Authorization'] = get_course_token(credentials_type)
        print(current_headers['Authorization'] )
        try:
            response = requests.put(url, json=put_data, headers=current_headers, timeout=15)
            print("done_func")
            if response.status_code == 200:
                break
            elif response.status_code == 404:
                return "ko"
            elif response.status_code == 401:
                autorization(credentials_type)
            else:
                return "ko"
        except:
            pass
        try:
            autorization(credentials_type)
        except:
            return "ko"
    return "ok"


@dramatiq.actor(queue_name='course_parser', store_results=True, max_retries=1, max_age=300000)
def approve_func(in_data):
    current_headers = headers.copy()
    credentials_type = in_data['of']
    url = f"https://www.of.moncompteformation.gouv.fr/edof-api/v1/api/private/organisms/current/registration-folders/{in_data['dossier']}/status"
    put_data = {"state":"VALIDATED"}
    for _ in range(2):
        current_headers['Authorization'] = get_course_token(credentials_type)
        print(current_headers['Authorization'] )
        try:
            response = requests.put(url, json=put_data, headers=current_headers, timeout=15)
            print("approve_func")
            if response.status_code == 200:
                break
            elif response.status_code == 404:
                return "ko"
            elif response.status_code == 401:
                autorization(credentials_type)
            else:
                return "ko"
        except:
            pass
        try:
            autorization(credentials_type)
        except:
            return "ko"
    return "ok"


def file_parser(json_data):
    results = []
    for item in json_data:
        dossier = item["dossier"]
        event = item["event"]
        if event == "in":
            result = in_func.send(item)
            result = result.get_result(block=True, timeout=300_000)
        elif event == "out":
            result = out_func.send(item)
            result = result.get_result(block=True, timeout=300_000)
        elif event == "update":
            result = update_func.send(item)
            result = result.get_result(block=True, timeout=300_000)
        elif event == "done":
            result = done_func.send(item)
            result = result.get_result(block=True, timeout=300_000)
        elif event == "approve":
            result = done_func.send(item)
            result = result.get_result(block=True, timeout=300_000)
        else:
            result = "ko"
        results.append({"dossier": str(dossier), "status": result})
    return results