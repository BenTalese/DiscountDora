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


def get_cached_session(
        user_agent: str = "DiscountDora",
        max_retries: int = 3,
        timeout: int = 10) -> requests_cache.CachedSession:
    _Session = requests_cache.CachedSession(backend='memory')

    _RetryStrategy = Retry(
        total = max_retries,
        backoff_factor = 2,
        status_forcelist = [429, 500, 502, 503, 504]
    )

    _Session.mount('http://', DefaultTimeoutAdapter(timeout=timeout, max_retries=_RetryStrategy))
    _Session.mount('https://', DefaultTimeoutAdapter(timeout=timeout, max_retries=_RetryStrategy))

    _Session.hooks = {
        'response': lambda r, *args, **kwargs: r.raise_for_status()
    }
    _Session.headers.update({'User-Agent': user_agent})

    return _Session
