"""Stream class for tap-xtm."""

import base64
import json
from typing import Dict, Optional, Any, Iterable
from pathlib import Path
from singer_sdk import typing
from functools import cached_property
from singer_sdk import typing as th
from singer_sdk.streams import RESTStream
from singer_sdk.authenticators import SimpleAuthenticator
import requests


SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")

class TapXtmStream(RESTStream):
    """xtm stream class."""
    
    _LOG_REQUEST_METRIC_URLS: bool = True
    @property
    def url_base(self) -> str:
        """Base URL of source"""
        return self.config["api_url"]

    @property
    def http_headers(self) -> dict:
        """Return the http headers needed."""
        headers = {}
        headers["Content-Type"] = "application/json"
        headers["Accept"] = "application/json"
        return headers

    @property
    def authenticator(self):
        authorization_key = self.config.get("api_token")
        http_headers = {
            "Authorization": f'XTM-Basic {authorization_key}'
        }
        return SimpleAuthenticator(stream=self, auth_headers=http_headers)

class Projects(TapXtmStream):
    name = "projects" # Stream name 
    path = "/projects" # API endpoint after base_url 
    primary_keys = ["id"]
    records_jsonpath = "$[*]" 
    replication_key = None

    schema = th.PropertiesList(
        th.Property("id", th.NumberType),
        th.Property("name", th.StringType),
        th.Property("status", th.StringType),
        th.Property("activity", th.StringType),
        th.Property("joinFilesType", th.StringType),
    ).to_dict()
