# flake8: noqa: E302

import sys
from multiprocessing import Process
from pathlib import Path
from time import sleep

import pytest
import pytest_asyncio
import requests

sys.path.append(str(Path(__file__).resolve().parents[3]))

from framework.dora_api.app import app
from framework.dora_api.startup import startup

#region ---------------- setup ----------------

base_route = 'http://localhost:5170/api/health'


def run_api():
    app.run('localhost', 5170)


@pytest_asyncio.fixture
async def api():
    await startup(is_test_env = True)
    process = Process(target=run_api)
    process.start()
    sleep(3)

    yield

    process.terminate()
    process.join()

#endregion setup

#region ---------------- health_check_async tests ----------------

@pytest.mark.asyncio
async def test_GetHealth(api):
    # Arrange

    # Act
    _Actual = requests.get(base_route)

    # Assert
    assert _Actual == 200

#endregion health_check_async tests
