from multiprocessing import Process
from time import sleep
import pytest_asyncio

from framework.dora_api.app import app
from framework.dora_api.startup import startup


def run_api():
    app.run('localhost', 5170)


@pytest_asyncio.fixture(scope="session")
async def api():
    await startup(is_test_env = True)
    process = Process(target=run_api)
    process.start()
    sleep(3)

    yield

    process.terminate()
    process.join()
