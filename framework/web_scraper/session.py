from requests import PreparedRequest, Response
from requests.adapters import HTTPAdapter, Retry
import requests_cache


class DefaultTimeoutAdapter(HTTPAdapter):
    def __init__(self, *args, timeout: float, **kwargs):
        self.timeout = timeout
        super().__init__(*args, **kwargs)

    def send(self, request: PreparedRequest, **kwargs) -> Response:
        kwargs['timeout'] = kwargs.get('timeout') or self.timeout
        return super().send(request, **kwargs)


def create_session(
        user_agent: str = "DiscountDora",
        max_retries: int = 3,
        timeout: int = 10) -> requests_cache.CachedSession:
    session = requests_cache.CachedSession(backend='memory')

    retry_strategy = Retry(
        total=max_retries,
        backoff_factor = 2,
        status_forcelist=[429, 500, 502, 503, 504]
    )

    session.mount('http://', DefaultTimeoutAdapter(timeout=timeout, max_retries=retry_strategy))
    session.mount('https://', DefaultTimeoutAdapter(timeout=timeout, max_retries=retry_strategy))

    session.hooks = {
        'response': lambda r, *args, **kwargs: r.raise_for_status()
    }
    session.headers.update({'User-Agent': user_agent})

    return session
