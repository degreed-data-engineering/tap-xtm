"""xtm tap class."""

from pathlib import Path
from typing import List
import logging
import click
from singer_sdk import Tap, Stream
from singer_sdk import typing as th

from tap_xtm.streams import (
    Projects,
    ProjectDetails,
    ProjectStats,
    ProjectMetrics,
)

PLUGIN_NAME = "tap-xtm"

STREAM_TYPES = [Projects, ProjectDetails, ProjectStats, ProjectMetrics]


class TapXtm(Tap):
    """xtm tap class."""

    name = "tap-xtm"
    config_jsonschema = th.PropertiesList(
        th.Property(
            "url_base",
            th.StringType,
            required=False,
            description="Url base for the source endpoint",
        ),
        th.Property("api_url", th.StringType, required=False, description="API URL"),
        th.Property(
            "api_token",
            th.StringType,
            required=False,
            description="api token for Basic auth",
        ),
    ).to_dict()

    def discover_streams(self) -> List[Stream]:
        """Return a list of discovered streams."""
        streams = [stream_class(tap=self) for stream_class in STREAM_TYPES]

        return streams


# CLI Execution:
cli = TapXtm.cli
