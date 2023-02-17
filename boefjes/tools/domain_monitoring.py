#!/usr/bin/python3

import datetime
import io
import json
import logging
import logging.handlers
import queue
import threading
import uuid
from enum import Enum
from typing import Set, Optional, Tuple, List, Sequence, Any, NoReturn

import certstream
import click
import tldextract

from boefjes.clients.bytes_client import BytesAPIClient
from boefjes.job_models import BoefjeMeta, Boefje

FULL_DOMAINS = (
    "minvws.nl",
    "coronamelder.nl",
    "brba.nl",
    "rdobeheer.nl",
    "autodiscovers",
    "gits",
    "gitlabs",  # we can also find certs that are submatches
    "ssh",
)

IGNORELIST = ("", "*", "www", "dev", "acc", "staging")  # ignore common stuff, cleans up the lists for speed
MIN_LENGTH = 3  # ignore parts that are too small


class MatchType(Enum):
    DIRECT = "direct"
    SUPERSTRING = "superstring"
    SUBSTRING = "substring"


class ExtendedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, MatchType):
            return o.value

        return super().default(o)


class MessageQueue:
    def __init__(self, client: BytesAPIClient, queue_size=1000, interval=datetime.timedelta(hours=2)):
        self._client = client
        self._messages = queue.Queue(maxsize=queue_size)
        self._interval = interval
        self._logger = logging.getLogger("MessageQueue")
        self._timer = None
        self.start_timer()

    # create and start timer
    def start_timer(self) -> None:
        # cancel timer if it exists or already running
        if self._timer is not None:
            self._timer.cancel()

        self._timer = threading.Timer(self._interval.total_seconds(), self._timer_callback)
        self._timer.daemon = True  # make sure the timer thread is killed when the main thread is killed
        self._logger.info("Started timer with interval of %d seconds", self._interval.total_seconds())
        self._timer.start()

    def _timer_callback(self) -> None:
        self._logger.info("Timed out, flushing queue")
        self.flush()

    def enqueue(self, message: Any) -> None:
        try:
            self._messages.put_nowait(message)
        except queue.Full:
            self._logger.info("Queue is full")
            self.flush()
            self._messages.put_nowait(message)

    def flush(self) -> None:
        self.start_timer()

        # skip if queue is empty
        if self._messages.empty():
            self._logger.warning("Queue is empty, skipping flush")
            return

        self._logger.info("Flushing queue (%d messages)", self._messages.qsize())
        stream = io.BytesIO()

        # write all messages to the stream as jsonlines
        while not self._messages.empty():
            message = self._messages.get_nowait()
            stream.write(json.dumps(message, cls=ExtendedJSONEncoder).encode("utf-8") + b"\r\n")

        # save the stream to bytes
        self._logger.info("Saving stream to bytes (%d bytes)", stream.tell())
        meta = BoefjeMeta(
            id=str(uuid.uuid4()),
            boefje=Boefje(id="domain-monitoring", version="0.1"),
            organization="",
            started_at=datetime.datetime.now(datetime.timezone.utc),
            ended_at=datetime.datetime.now(datetime.timezone.utc),
        )
        self._client.save_boefje_meta(meta)
        self._client.save_raw(meta.id, stream.getvalue(), {"application/jsonlines"})
        self._client.login()


def domain_match(input_domains: Set[str], domains: Sequence[str]) -> Optional[Tuple[MatchType, List[str]]]:
    # global input_domains
    domain_parts = clean_input(domains)

    # are there any cheap matches?
    direct_matches = list(input_domains.intersection(domain_parts))
    if direct_matches:
        return MatchType.DIRECT, direct_matches

    # are the certs domains partial matches to our list?
    for part in domain_parts:
        substring_matches = list(match for match in input_domains if part in match)
        if substring_matches:
            return MatchType.SUBSTRING, substring_matches

    # does our list partialy matches against the certs domains?
    for domain in input_domains:
        substring_matches = list(match for match in domain_parts if domain in match)
        if substring_matches:
            return MatchType.SUPERSTRING, substring_matches


def clean_input(domains: Sequence[str]) -> Set[str]:
    output = set()

    for domain in domains:
        domain = tldextract.extract(domain.lower())
        domain_parts = set(domain.subdomain.split("."))
        domain_parts.add(domain.domain)
        domain_parts = domain_parts.difference(IGNORELIST)
        output = output.union(filter(lambda x: len(x) >= MIN_LENGTH, domain_parts))

    return output


# todo: input_domains
class Monitor:
    def __init__(
        self,
        input_domains: Set[str],
        client: BytesAPIClient,
        message_queue: MessageQueue,
        stream_url: str = "wss://certstream.calidog.io",
    ):
        self._input_domains = input_domains
        self._stream_url = stream_url
        self._client = client
        self._queue = message_queue
        self._logger = logging.getLogger("Monitor")

    def start(self) -> None:
        self._logger.info("Logging in to Bytes API")
        self._client.login()  # todo: catch exception

        self._logger.info("Starting monitor")
        certstream.listen_for_events(self._message_callback, self._stream_url)
        # self._queue.flush() # todo: log and flush

    def _message_callback(self, message, context) -> None:
        self._logger.debug("Incoming message: %s", message)

        if message["message_type"] == "certificate_update":
            all_domains = message["data"]["leaf_cert"]["all_domains"]

            if all_domains and (match := domain_match(self._input_domains, all_domains)) is not None:
                match_type, match = match
                self._logger.info("Match (type %s) found for %s: %s", match_type, match, ", ".join(all_domains))
                self._queue.enqueue({"match_type": match_type, "match": match, "domains": all_domains})


# todo: input_domains
@click.command()
@click.option("--size", default=1000, help="Size of the message queue")
@click.option("--interval", default=3600, help="Interval in seconds to flush the queue")
@click.option("--bytes-api", default="http://localhost:8002", help="Bytes API uri", envvar="BYTES_API")
@click.option("--bytes-username", help="Bytes API username", envvar="BYTES_USERNAME")
@click.option("--bytes-password", help="Bytes API password", envvar="BYTES_PASSWORD")
def main(size: int, interval: int, bytes_api: str, bytes_username: str, bytes_password: str) -> NoReturn:
    client = BytesAPIClient(bytes_api, bytes_username, bytes_password)
    message_queue = MessageQueue(client, size, datetime.timedelta(seconds=interval))
    monitor = Monitor(clean_input(FULL_DOMAINS), client, message_queue)
    monitor.start()


# todo: create cli app
if __name__ == "__main__":
    logging.basicConfig(format="[%(levelname)s:%(name)s] %(asctime)s - %(message)s", level=logging.INFO)

    main()
