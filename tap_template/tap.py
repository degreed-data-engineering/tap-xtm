"""template tap class."""

from pathlib import Path
from typing import List
import logging
import click
from singer_sdk import Tap, Stream
from singer_sdk import typing as th

from tap_template.streams import (
    Events,
)

PLUGIN_NAME = "tap-template"

STREAM_TYPES = [ 
    Events,
]

class TapTemplate(Tap):
    """template tap class."""

    name = "tap-template"
    config_jsonschema = th.PropertiesList(
        th.Property("api_key", th.StringType, required=True, description="datadog api key"),
        th.Property("app_key", th.StringType, required=True, description="datadog app key"),
        th.Property("start_date", th.StringType, required=True, description="start date for sync"),
    ).to_dict()

    def discover_streams(self) -> List[Stream]:
        """Return a list of discovered streams."""
        streams =  [stream_class(tap=self) for stream_class in STREAM_TYPES]

        return streams


# # CLI Execution:
# cli = TapTemplate.cli
if __name__ == "__main":
    TapTemplate.cli()