# flake8: noqa

import sys
from multiprocessing import Process
from pathlib import Path
from time import sleep

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
    _Process = Process(target=run_api)
    _Process.start()
    sleep(3)

    yield

    _Process.terminate()
    _Process.join()

#endregion setup

#region ---------------- health_check_async tests ----------------

def test__health_check_async__ApiIsHealthy__GetsOkayResponse(api):
    _Response = requests.get(base_route)

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json() == True

#endregion health_check_async tests
