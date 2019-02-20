from base64 import b64encode

import yaml

import requests

try:
    config = yaml.safe_load(open("../config.yml"))
except IOError:
    raise Exception("Please, create config.yml from config.yml.example")

BASE_JIRA_URL = config.get("jira")
ZAPI_URL = config.get("zapi")
ZAPI_VERSION = config.get("zapi_version")
JIRA_LOGIN = config.get("login")
JIRA_PASSWORD = config.get("password")
JIRA_PROJECT = config.get("project")
TEST_CYCLE = config.get("test_cycle")
LABELS = config.get("search_by")
STATUS_FROM = config.get("status_from")
STATUS_TO = config.get("status_to")

DEFAULT_HEADERS = {"Authorization": "Basic %s" % b64encode(JIRA_LOGIN + ":" + JIRA_PASSWORD),
                   "Content-Type": "application/json"}

STATUSES = {
    "PASSED": 1,
    "FAILED": 2,
    "WIP": 3,
    "BLOCKED": 4,
    "SCHEDULED": -1
}


class ZapiCalls(object):
    GET_ZQL_FIELDS = "%s/zql/fields/values" % ZAPI_VERSION
    POST_EXECUTIONS = "%s/executions" % ZAPI_VERSION
    PUT_EXECUTION = "/rest/zapi/latest/execution"
    GET_EXECUTIONS_LIST = "%s/executions/search/cycle" % ZAPI_VERSION
    GET_ZQL_SEARCH = "/rest/zapi/latest/zql/executeSearch"
    GET_PROJECTS = "/rest/api/2/project"
    GET_CYCLES = "/rest/zapi/latest/cycle"


def get_request(endpoint, params=None):
    r = requests.get(BASE_JIRA_URL + endpoint, headers=DEFAULT_HEADERS, timeout=180, params=params)
    return handle_response_status(r)


def post_request(endpoint, payload=None):
    r = requests.post(BASE_JIRA_URL + endpoint, data=payload, headers=DEFAULT_HEADERS)
    return handle_response_status(r)


def put_request(endpoint, payload=None):
    r = requests.put(BASE_JIRA_URL + endpoint, data=payload, headers=DEFAULT_HEADERS)
    return handle_response_status(r)


def delete_request(endpoint, params=None):
    r = requests.delete(BASE_JIRA_URL + endpoint, headers=DEFAULT_HEADERS, params=params)
    return handle_response_status(r)


def handle_response_status(response):
    if response.status_code in (200, 201, 204):
        return response
    else:
        raise Exception(response.url, response.content, response.status_code)
