from multiprocessing import Process
from time import sleep

import pytest

from dora_api.app import app
from dora_api.startup import startup


def run_api():
    app.run('localhost', 5170)


def run_test_api():
    startup(is_test_env=True)


@pytest.fixture(scope="session")
def api():
    process = Process(target=run_test_api)
    process.start()

    sleep(3)

    yield

    process.terminate()
    process.join()
