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
        http_headers = {"Authorization": f"XTM-Basic {authorization_key}"}
        return SimpleAuthenticator(stream=self, auth_headers=http_headers)


class Projects(TapXtmStream):
    name = "projects"  # Stream name
    path = "/projects"  # API endpoint after base_url
    primary_keys = ["id"]
    records_jsonpath = "$[*]"  # https://jsonpath.com Use requests response json to identify the json path
    replication_key = None

    schema = th.PropertiesList(
        th.Property("id", th.NumberType),
        th.Property("name", th.StringType),
        th.Property("status", th.StringType),
        th.Property("activity", th.StringType),
        th.Property("joinFilesType", th.StringType),
    ).to_dict()

    def get_child_context(self, record: dict, context: Optional[dict]) -> dict:
        """Return a context dictionary for child streams."""
        return {"project_id": record["id"]}

    def get_next_page_token(
        self, response: requests.Response, previous_token: Optional[Any]
    ) -> Optional[Any]:
        """Return a token for identifying next page or None if no more pages."""
        current_page = int(response.headers.get("xtm-page", 1))
        max_item_size = int(response.headers.get("xtm-page-size", 1000))
        page_item_count = int(response.headers.get("xtm-page-items-count", 1000))

        if max_item_size == page_item_count:
            return current_page + 1

        return None

    def get_url_params(
        self, context: Optional[dict], next_page_token: Optional[Any]
    ) -> Dict[str, Any]:
        """Return a dictionary of values to be used in URL parameterization."""
        params: dict = {}
        if next_page_token:
            params["page"] = next_page_token
        return params


class ProjectStats(TapXtmStream):
    name = "projectstats"  # Stream name
    parent_stream_type = Projects
    path = "/projects/{project_id}/statistics?"  # API endpoint after base_url
    primary_keys = ["project_id", "targetLanguage"]
    records_jsonpath = "$[*]"  # https://jsonpath.com Use requests response json to identify the json path
    replication_key = None

    schema = th.PropertiesList(
        th.Property("project_id", th.NumberType),
        th.Property("targetLanguage", th.StringType),
        th.Property(
            "usersStatistics",
            th.ArrayType(
                th.ObjectType(
                    th.Property("userId", th.NumberType),
                    th.Property("userType", th.StringType),
                    th.Property(
                        "stepsStatistics",
                        th.ArrayType(
                            th.ObjectType(
                                th.Property("workflowStepName", th.StringType),
                                th.Property(
                                    "jobsStatistics",
                                    th.ArrayType(
                                        th.ObjectType(
                                            th.Property("jobId", th.NumberType),
                                            th.Property(
                                                "sourceStatistics",
                                                th.ObjectType(
                                                    th.Property(
                                                        "totalSegments", th.NumberType
                                                    ),
                                                    th.Property(
                                                        "totalWords", th.NumberType
                                                    ),
                                                ),
                                            ),
                                            th.Property(
                                                "targetStatistics",
                                                th.ObjectType(
                                                    th.Property(
                                                        "totalSegments", th.NumberType
                                                    ),
                                                    th.Property(
                                                        "totalWords", th.NumberType
                                                    ),
                                                ),
                                            ),
                                            th.Property("creationDate", th.NumberType),
                                        )
                                    ),
                                ),
                            )
                        ),
                    ),
                )
            ),
        ),
    ).to_dict()

    def post_process(self, row: dict, context: Optional[dict]) -> dict:
        row["project_id"] = context["project_id"]
        return row
