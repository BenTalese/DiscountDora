"""End-to-end coverage for the structured logging stack (I1+I2 round A).

Exercises the bits we can verify over HTTP without poking the
filesystem: the X-Request-Id round-trip header, the /api/client-logs
endpoint, and the rate limit.
"""
import requests


CLIENT_LOGS_URL = "http://localhost:5170/api/client-logs"


def test__request_middleware__echoes_request_id_header(api):
    sent = "test-request-id-abc123"
    response = requests.get(
        "http://localhost:5170/api/health",
        headers={"X-Request-Id": sent},
    )
    assert response.status_code == 200
    assert response.headers.get("X-Request-Id") == sent


def test__request_middleware__generates_request_id_when_missing(api):
    response = requests.get("http://localhost:5170/api/health")
    assert response.status_code == 200
    rid = response.headers.get("X-Request-Id")
    assert rid is not None and len(rid) >= 16


def test__client_logs__valid_payload__is_accepted(api):
    response = requests.post(CLIENT_LOGS_URL, json={
        "level": "warn",
        "message": "tab moved while drag in flight",
        "context": {"route": "/stock"},
    })
    assert response.status_code == 204


def test__client_logs__unknown_level__is_400(api):
    response = requests.post(CLIENT_LOGS_URL, json={
        "level": "fatal",
        "message": "anything",
    })
    assert response.status_code == 400


def test__client_logs__without_auth__still_accepted(api):
    # `submit_client_log` is in PUBLIC_ENDPOINTS so login-screen crashes
    # can still report. A fresh session (no cookies) should be accepted.
    fresh = requests.Session()
    response = fresh.post(CLIENT_LOGS_URL, json={
        "level": "error",
        "message": "boot crashed",
    })
    assert response.status_code == 204


def test__client_logs__rate_limit__drops_silently_above_threshold(api):
    # The session-fixture client is one bucket; spam well past the 10-per-
    # 60s cap and confirm every response is still 204 (rate limit returns
    # 204 silently so the SPA doesn't have to retry-loop).
    for i in range(15):
        response = requests.post(CLIENT_LOGS_URL, json={
            "level": "warn",
            "message": f"spam {i}",
        })
        assert response.status_code == 204
