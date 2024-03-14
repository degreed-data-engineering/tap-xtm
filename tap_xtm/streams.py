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
from singer_sdk.exceptions import FatalAPIError
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


class ProjectDetails(TapXtmStream):
    name = "projectdetails"  # Stream name
    parent_stream_type = Projects
    path = "/projects/{project_id}/"  # API endpoint after base_url
    primary_keys = ["id"]
    records_jsonpath = "$[*]"  # https://jsonpath.com Use requests response json to identify the json path
    replication_key = None

    schema = th.PropertiesList(
        th.Property("id", th.NumberType),
        th.Property("name", th.StringType),
        th.Property("activity", th.StringType),
        th.Property("creatorId", th.NumberType),
        th.Property("customerId", th.NumberType),
        th.Property("customerName", th.StringType),
        th.Property("projectManagerId", th.NumberType),
        th.Property("sourceLanguage", th.StringType),
        th.Property("targetLanguages", th.StringType),
        th.Property("templateId", th.NumberType),
        th.Property("filterTemplateId", th.StringType),
        th.Property("createDate", th.NumberType),
        th.Property("startDates", th.NumberType),
        th.Property("finishDate", th.NumberType),
        th.Property("dueDate", th.NumberType),
        th.Property("proposalApprovalStatus", th.StringType),
        th.Property("subjectMatterId", th.NumberType),
        th.Property("subjectMatterName", th.StringType),
        th.Property("tmPenaltyProfileId", th.NumberType),
        th.Property("qaProfileId", th.NumberType),
        th.Property("segmentLockingType", th.StringType),
    ).to_dict()

    def post_process(self, row: dict, context: Optional[dict]) -> dict:
        row["project_id"] = context["project_id"]
        return row

    def request_records(self, context: Optional[dict]) -> Iterable[dict]:
        """Request records for the stream, handling 404 errors specifically."""
        try:
            yield from super().request_records(context)
        except FatalAPIError as e:
            if "404 Client Error" in str(e):
                self.logger.warn(
                    f"Project ID {context.get('project_id')} not found. Skipping."
                )
            else:
                raise


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


class ProjectMetrics(TapXtmStream):
    name = "projectmetrics"  # Stream name
    parent_stream_type = Projects
    path = "/projects/{project_id}/metrics/"  # API endpoint after base_url
    primary_keys = ["project_id", "targetLanguage"]
    records_jsonpath = "$[*]"  # https://jsonpath.com Use requests response json to identify the json path
    replication_key = None

    schema = th.PropertiesList(
        th.Property("project_id", th.NumberType),
        th.Property("targetLanguage", th.StringType),
        th.Property(
            "coreMetrics",
            th.ObjectType(
                th.Property("iceMatchCharacters", th.NumberType),
                th.Property("iceMatchSegments", th.NumberType),
            ),
        ),
        th.Property(
            "metricsProgress",
            th.ObjectType(
                th.Property("wordsToBeDone", th.NumberType),
                th.Property("wordsDone", th.NumberType),
            ),
        ),
        th.Property(
            "jobsMetrics",
            th.ArrayType(
                th.ObjectType(
                    th.Property("jobId", th.NumberType),
                    th.Property(
                        "coreMetrics",
                        th.ObjectType(
                            th.Property("iceMatchCharacters", th.NumberType),
                            th.Property("iceMatchSegments", th.NumberType),
                        ),
                    ),
                    th.Property(
                        "metricsProgress",
                        th.ObjectType(
                            th.Property("MT Post editing1", th.NumberType),
                        ),
                    ),
                )
            ),
        ),
    ).to_dict()

    def post_process(self, row: dict, context: Optional[dict]) -> dict:
        row["project_id"] = context["project_id"]
        return row
