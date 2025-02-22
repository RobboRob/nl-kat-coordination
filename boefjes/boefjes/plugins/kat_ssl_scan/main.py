from typing import List, Tuple, Union

import docker

from boefjes.job_models import BoefjeMeta

SSLSCAN_IMAGE = "breezethink/sslscan:latest"


def run(boefje_meta: BoefjeMeta) -> List[Tuple[set, Union[bytes, str]]]:
    client = docker.from_env()
    input_ = boefje_meta.arguments["input"]
    hostname = input_["hostname"]["name"]

    output = client.containers.run(SSLSCAN_IMAGE, ["--xml=-", hostname], remove=True)

    return [(set(), output)]
