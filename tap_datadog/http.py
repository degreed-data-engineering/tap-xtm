from datetime import datetime, timedelta
import time
import threading
import re
from requests.exceptions import (HTTPError, Timeout)
from requests.auth import HTTPBasicAuth
import requests
from singer import metrics
import singer
import backoff

REFRESH_TOKEN_EXPIRATION_PERIOD = 3500

# The project plan for this tap specified:
# > our past experience has shown that issuing queries no more than once every
# > 10ms can help avoid performance issues
TIME_BETWEEN_REQUESTS = timedelta(microseconds=10e3)

LOGGER = singer.get_logger()

# timeout requests after 300 seconds
REQUEST_TIMEOUT = 300

class DatadogError(Exception):
    def __init__(self, message=None, response=None):
        super().__init__(message)
        self.message = message
        self.response = response

class DatadogBackoffError(DatadogError):
    pass

class DatadogBadRequestError(DatadogError):
    pass

class DatadogUnauthorizedError(DatadogError):
    pass

class DatadogForbiddenError(DatadogError):
    pass

class DatadogSubRequestFailedError(DatadogError):
    pass

class DatadogBadGatewayError(DatadogError):
    pass

class DatadogConflictError(DatadogError):
    pass

class DatadogNotFoundError(DatadogError):
    pass

class DatadogRateLimitError(DatadogBackoffError):
    pass

class DatadogServiceUnavailableError(DatadogBackoffError):
    pass

class DatadogGatewayTimeoutError(DatadogError):
    pass

class DatadogInternalServerError(DatadogError):
    pass

class DatadogNotImplementedError(DatadogError):
    pass


ERROR_CODE_EXCEPTION_MAPPING = {
    400: {
        "raise_exception": DatadogBadRequestError,
        "message": "A validation exception has occurred."
    },
    401: {
        "raise_exception": DatadogUnauthorizedError,
        "message": "Invalid authorization credentials."
    },
    403: {
        "raise_exception": DatadogForbiddenError,
        "message": "User does not have permission to access the resource."
    },
    404: {
        "raise_exception": DatadogNotFoundError,
        "message": "The resource you have specified cannot be found."
    },
    409: {
        "raise_exception": DatadogConflictError,
        "message": "The request does not match our state in some way."
    },
    429: {
        "raise_exception": DatadogRateLimitError,
        "message": "The API rate limit for your organisation/application pairing has been exceeded."
    },
    449:{
        "raise_exception": DatadogSubRequestFailedError,
        "message": "The API was unable to process every part of the request."
    },
    500: {
        "raise_exception": DatadogInternalServerError,
        "message": "The server encountered an unexpected condition which prevented" \
            " it from fulfilling the request."
    },
    501: {
        "raise_exception": DatadogNotImplementedError,
        "message": "The server does not support the functionality required to fulfill the request."
    },
    502: {
        "raise_exception": DatadogBadGatewayError,
        "message": "Server received an invalid response."
    },
    503: {
        "raise_exception": DatadogServiceUnavailableError,
        "message": "API service is currently unavailable."
    },
    504: {
        "raise_exception": DatadogGatewayTimeoutError,
        "message": "API service time out, please check Datadog server."
    }
}

def check_status(response):
    # Forming a response message for raising custom exception
    try:
        response_json = response.json()
    except Exception: # pylint: disable=broad-except
        response_json = {}
    if response.status_code != 200:
        message = "HTTP-error-code: {}, Error: {}".format(
            response.status_code,
            response_json.get("errorMessages", [ERROR_CODE_EXCEPTION_MAPPING.get(
                response.status_code, {}).get("message", "Unknown Error")])[0]
        )
        exc = ERROR_CODE_EXCEPTION_MAPPING.get(
            response.status_code, {}).get("raise_exception", DatadogError)
        raise exc(message, response) from None

def get_request_timeout(config):
    # Get `request_timeout` value from config
    config_request_timeout = config.get('request_timeout')

    # if config request_timeout is other than 0, "0", or "" then use request_timeout
    if config_request_timeout and float(config_request_timeout):
        request_timeout = float(config_request_timeout)
    else:
        # If value is 0, "0", "", or not passed then it set default to 300 seconds
        request_timeout = REQUEST_TIMEOUT
    return request_timeout

class Client():
    def __init__(self, config):

        # self.session = requests.Session()
        # self.next_request_at = datetime.now()
        # self.user_agent = config.get("user_agent")
        # self.login_timer = None
        # self.timeout = get_request_timeout(config)
        self.login_timer = None
        # Assign False for cloud Datadog instance
        # self.is_on_prem_instance = False

        LOGGER.info("Using Basic Auth API authentication")
        self.base_url = config.get("base_url")
        self.api_key = config.get("api_key")
        self.app_key = config.get("app_key")
        self.start_date = config.get("start_date")

        #self.test_basic_credentials_are_authorized()

    def url(self, path):
        # defend against if the base_url does or does not provide https://
        base_url = self.base_url
        base_url = re.sub('^http[s]?://', '', base_url)
        base_url = 'https://' + base_url

        return base_url.rstrip("/") + "/" + path.lstrip("/")

    def _headers(self, headers):
        headers = headers.copy()
        headers["DD-API-KEY"] = self.api_key
        headers["DD-APPLICATION-KEY"] = self.app_key
        headers["Content-Type"] = 'application/json'
        headers["Accept"] = 'application/json'

        return headers

    def send(self, method, path, headers={}, **kwargs):

        request = requests.Request(method,
                                    self.url(path),
                                    headers=self._headers(headers),
                                    **kwargs)
        return self.session.send(request.prepare())


# class Paginator():
#     def __init__(self, client, page_num=0, order_by=None, items_key="values"):
#         self.client = client
#         self.next_page_num = page_num
#         self.order_by = order_by
#         self.items_key = items_key

#     def pages(self, *args, **kwargs):
#         """Returns a generator which yields pages of data. When a given page is
#         yielded, the next_page_num property can be used to know what the index
#         of the next page is (useful for bookmarking).

#         :param args: Passed to Client.request
#         :param kwargs: Passed to Client.request
#         """
#         params = kwargs.pop("params", {}).copy()
#         while self.next_page_num is not None:
#             params["startAt"] = self.next_page_num
#             if self.order_by:
#                 params["orderBy"] = self.order_by
#             response = self.client.request(*args, params=params, **kwargs)
#             if self.items_key:
#                 page = response[self.items_key]
#             else:
#                 page = response

#             # Accounts for responses that don't nest their results in a
#             # key by falling back to the params `maxResults` setting.
#             if 'maxResults' in response:
#                 max_results = response['maxResults']
#             else:
#                 max_results = params['maxResults']

#             if len(page) < max_results:
#                 self.next_page_num = None
#             else:
#                 self.next_page_num += max_results

#             if page:
#                 yield page
