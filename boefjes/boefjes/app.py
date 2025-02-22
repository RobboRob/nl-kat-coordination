import logging
import os
import time
from multiprocessing import Pool
from typing import Callable

from pydantic import ValidationError
from requests import HTTPError

from boefjes.clients.scheduler_client import (
    SchedulerAPIClient,
    SchedulerClientInterface,
    TaskStatus,
)
from boefjes.config import Settings
from boefjes.job_handler import BoefjeHandler, NormalizerHandler
from boefjes.katalogus.local_repository import get_local_repository
from boefjes.local import LocalBoefjeJobRunner, LocalNormalizerJobRunner
from boefjes.runtime_interfaces import Handler, RuntimeManager

logger = logging.getLogger(__name__)


class SchedulerRuntimeManager(RuntimeManager):
    def __init__(
        self,
        item_handler: Handler,
        client_factory: Callable[[], SchedulerClientInterface],
        settings: Settings,
        log_level: str,  # TODO: (re)move?
    ):
        self.item_handler = item_handler
        self.client_factory = client_factory
        self.settings = settings

        logger.setLevel(log_level)

    def run(self, queue: RuntimeManager.Queue) -> None:
        logger.info("Creating worker pool for queue '%s'", queue.value)
        pool_size = self.settings.pool_size

        with Pool(processes=pool_size) as pool:
            try:
                # Workers pull tasks from the scheduler
                pool.starmap(
                    start_working,
                    [(self.client_factory(), self.item_handler, self.settings, queue) for _ in range(pool_size)],
                )
            except Exception:  # noqa
                logger.exception("An error occurred")

            logger.info("Closing worker pool")


def start_working(
    scheduler_client: SchedulerClientInterface,
    item_handler: Handler,
    settings: Settings,
    queue_to_handle: RuntimeManager.Queue,
) -> None:
    """
    This function runs in parallel and polls the scheduler for queues and jobs.
    Hence, it should catch most errors and give proper, granular feedback to the user.
    """

    logger.info("Started worker process [pid=%d]", os.getpid())

    while True:
        try:
            queues = scheduler_client.get_queues()
        except HTTPError:
            # Scheduler is having issues, so make note of it and try again
            logger.exception("Getting the queues from the scheduler failed")
            time.sleep(10 * settings.poll_interval)  # But not immediately
            continue

        # We do not target a specific queue since we start one runtime for all organisations
        # and queue ids contain the organisation_id
        queues = [q for q in queues if q.id.startswith(queue_to_handle.value)]

        logger.debug("Found queues: %s", [queue.id for queue in queues])

        all_queues_empty = True

        for queue in queues:
            logger.debug("Popping from queue %s", queue.id)

            try:
                p_item = scheduler_client.pop_item(queue.id)
            except (HTTPError, ValidationError):
                logger.exception("Popping task from scheduler failed, sleeping 10 seconds")
                time.sleep(10)
                continue

            if not p_item:
                logger.debug("Queue %s empty", queue.id)
                continue

            all_queues_empty = False

            logger.info("Handling task[%s]", p_item.data.id)
            status = TaskStatus.FAILED

            try:
                item_handler.handle(p_item.data)
                status = TaskStatus.COMPLETED
            except Exception:
                logger.exception("An error occurred handling scheduler item %s", p_item.data.id)
                continue
            except:  # noqa
                logger.exception("Exiting worker...")
                return
            finally:
                logger.info("Patching scheduler task task[%s] to %s", p_item.data.id, status.value)

                try:
                    scheduler_client.patch_task(str(p_item.id), status)
                except HTTPError:
                    logger.exception("Could not patch scheduler task to %s", status.value)

        if all_queues_empty:
            logger.debug("All queues empty, sleeping %f seconds", settings.poll_interval)
            time.sleep(settings.poll_interval)


def get_runtime_manager(settings: Settings, queue: RuntimeManager.Queue, log_level: str) -> RuntimeManager:
    # Not a lambda since multiprocessing tries and fails to pickle lambda's
    def client_factory():
        return SchedulerAPIClient(settings.scheduler_api)

    if queue is RuntimeManager.Queue.BOEFJES:
        item_handler = BoefjeHandler(LocalBoefjeJobRunner(get_local_repository()), get_local_repository())
    else:
        item_handler = NormalizerHandler(LocalNormalizerJobRunner(get_local_repository()))

    return SchedulerRuntimeManager(
        item_handler,
        client_factory,  # Do not share a session between workers
        settings,
        log_level,
    )
