import requests
from requests import PreparedRequest, Response
from requests.adapters import HTTPAdapter, Retry


class DefaultTimeoutAdapter(HTTPAdapter):
    def __init__(self, *args, timeout: float, **kwargs):
        self.timeout = timeout
        super().__init__(*args, **kwargs)

    def send(self, request: PreparedRequest, **kwargs) -> Response:
        kwargs['timeout'] = kwargs.get('timeout') or self.timeout
        return super().send(request, **kwargs)


def create_session(
        user_agent: str = "DiscountDora/1.0.0 (ben.talese@gmail.com)",
        max_retries: int = 3,
        timeout: int = 10) -> requests.Session:
    session = requests.Session()

    session.headers.update({'User-Agent': user_agent})

    retry_strategy = Retry(
        total=max_retries,
        backoff_factor = 2,
        status_forcelist=[429, 500, 502, 503, 504]
    )

    session.hooks = {
        'response': lambda r, *args, **kwargs: r.raise_for_status()
    }

    session.mount('http://', DefaultTimeoutAdapter(timeout=timeout, max_retries=retry_strategy))
    session.mount('https://', DefaultTimeoutAdapter(timeout=timeout, max_retries=retry_strategy))

    return session
