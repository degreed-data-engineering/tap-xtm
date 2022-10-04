# """REST client handling, including Stream base class."""
# import json

# import requests
# from pathlib import Path
# from typing import Any, Dict, Optional, Union, List, Iterable

# from memoization import cached

# from singer_sdk.helpers.jsonpath import extract_jsonpath
# from singer_sdk.streams import RESTStream
# from singer_sdk.authenticators import APIKeyAuthenticator


# SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")


# class Client():

#     # TODO: Set the API's base URL here:
#     url_base = "https://api.datadoghq.com{}"

#     #records_jsonpath = "$[*]"  # Or override `parse_response`.
#     records_jsonpath = "$.data[*]"
#     next_page_token_jsonpath = "$.next_page"  # Or override `get_next_page_token`.

#     # @property
#     # def authenticator(self) -> APIKeyAuthenticator:
#     #     """Return a new authenticator object."""
#     #     return APIKeyAuthenticator.create_for_stream(
#     #         self,
#     #         key="x-api-key",
#     #         value=self.config.get("api_key"),
#     #         location="header"
#     #     )

#     @property
#     def http_headers(self) -> dict:
#         """Return the http headers needed."""
#         headers = {}
#         headers["Accept"] = 'application/json'
#         headers["Content-Type"] = 'application/json'
#         if "api_key" in self.config:
#             headers["DD-API-KEY"] = self.config.get("api_key")
#         if "app_key" in self.config:
#             headers["DD-APPLICATION-KEY"] = self.config.get("app_key")

#         # Creates the datadog headers: 
#         #        headers = {
#         #       'Accept': 'application/json',
#         #       'Content-Type': 'application/json'
#         #        }
#         print('HEADERS')
#         print(headers)
#         return headers

#     def get_next_page_token(
#         self, response: requests.Response, previous_token: Optional[Any]
#     ) -> Optional[Any]:
#         """Return a token for identifying next page or None if no more pages."""
#         # TODO: If pagination is required, return a token which can be used to get the
#         #       next page. If this is the final page, return "None" to end the
#         #       pagination loop.
#         # if self.next_page_token_jsonpath:
#         #     all_matches = extract_jsonpath(
#         #         self.next_page_token_jsonpath, response.json()
#         #     )
#         #     first_match = next(iter(all_matches), None)
#         #     next_page_token = first_match
#         # else:
#         #     next_page_token = response.headers.get("X-Next-Page", None)

#         return None

#     def get_url_params(
#         self, context: Optional[dict], next_page_token: Optional[Any]
#     ) -> Dict[str, Any]:
#         """Return a dictionary of values to be used in URL parameterization."""
#         params: dict = {}
#         if next_page_token:
#             params["page"] = next_page_token
#         if "start_date" in self.config:
#             params["start_date"] = self.config.get("start_date")
#         if "query" in self.config:
#             params["query"] = self.config.get("query")

#         params["limit"] = 10
        
#         print(params)
#         return params

#     def prepare_request_payload(
#         self, context: Optional[dict], next_page_token: Optional[Any]
#     ) -> Optional[dict]:
#         """Prepare the data payload for the REST API request."""
#         payload: dict = {}

#         payload['filter'] = {'query': self.config.get("query"), 'from': self.config.get("start_date")}
#         payload['page'] = {'limit': 10}

#         return payload

#     def parse_response(self, response: requests.Response) -> Iterable[dict]:
#         """Parse the response and return an iterator of result records."""
#         # TODO: Parse response body and return a set of records.
#         yield from extract_jsonpath(self.records_jsonpath, input=response.json())

#     def post_process(self, row: dict, context: Optional[dict]) -> dict:
#         """As needed, append or transform raw data to match expected structure."""
#         # TODO: Delete this method if not needed.
#         return row
