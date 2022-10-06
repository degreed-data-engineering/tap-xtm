"""Stream type classes for tap-datadog."""
import json
import pytz
import singer
import dateparser

from singer import metrics, utils, metadata, Transformer
from .context import Context
from .http import Paginator


# from .http import Paginator,DatadogNotFoundError



LOGGER = singer.get_logger()

class Stream():
    """Information about and functions for syncing streams for the Datadog API.

    Important class properties:

    :var tap_stream_id:
    :var pk_fields: A list of primary key fields
    :var indirect_stream: If True, this indicates the stream cannot be synced
    directly, but instead has its data generated via a separate stream."""
    def __init__(self, tap_stream_id, pk_fields, indirect_stream=False, path=None):
        self.tap_stream_id = tap_stream_id
        self.pk_fields = pk_fields
        # Only used to skip streams in the main sync function
        self.indirect_stream = indirect_stream
        self.path = path

    def __repr__(self):
        return "<Stream(" + self.tap_stream_id + ")>"
        
    def sync(self):
        page = Context.client.request(self.tap_stream_id, "POST", self.path)
        self.write_page(page)

    def write_page(self, page):
        stream = Context.get_catalog_entry(self.tap_stream_id)
        stream_metadata = metadata.to_map(stream.metadata)
        extraction_time = singer.utils.now()
        for rec in page:
            with Transformer() as transformer:
                rec = transformer.transform(rec, stream.schema.to_dict(), stream_metadata)
            singer.write_record(self.tap_stream_id, rec, time_extracted=extraction_time)
        with metrics.record_counter(self.tap_stream_id) as counter:
            counter.increment(len(page))

class Event_logs(Stream):
    def sync(self):
        query = Context.config.get("query")

        updated_bookmark = [self.tap_stream_id, "updated"]
        page_num_offset = [self.tap_stream_id, "offset", "page_num"]

        last_updated = Context.update_start_date_bookmark(updated_bookmark)
        timezone = Context.retrieve_timezone()
        start_date = last_updated.astimezone(pytz.timezone(timezone)).strftime("%Y-%m-%d %H:%M")


        params = json.dumps({
            "filter": {
                "query": "source:degreed.api env:production",
                "from": "2022-10-02T17:00:18+01:00",
                "to": "2022-10-03T17:00:18+01:00"
            },
            "page": {
                "limit": 10
            }
        })
        types = Context.client.request(self.tap_stream_id, "POST", path='/api/v2/logs/events/search', params=params)
        
        self.write_page(types)
        singer.write_state(Context.state)


EVENTLOGS = Event_logs("eventlogs", ["id"])

ALL_STREAMS = [EVENTLOGS]

ALL_STREAM_IDS = [s.tap_stream_id for s in ALL_STREAMS]



# class event_logs_old(Stream):
#     """Define custom stream."""
#     name = "event_logs"
#     path = None
#     primary_keys = ["id"]
#     replication_key = None
#     # Optionally, you may also use `schema_filepath` in place of `schema`:

#     schema = th.PropertiesList(
#         th.Property("id", th.StringType, required=True),
#         th.Property("type", th.StringType),
#         th.Property(
#             "attributes",
#             th.ObjectType(
#                 th.Property("status", th.StringType),
#                 th.Property("tags", th.ArrayType(th.StringType)),
#                 th.Property("timestamp", th.StringType),
#                 th.Property("host", th.StringType),
#                 th.Property(
#                     "attributes", 
#                     th.ObjectType(
#                         th.Property("level", th.StringType),
#                     )
#                 ),
#             )
#         ),
#     ).to_dict()

