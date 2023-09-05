import requests
from requests import PreparedRequest, Response
from requests.adapters import HTTPAdapter, Retry


class DefaultTimeoutAdapter(HTTPAdapter):
    def __init__(self, *args, timeout: float, **kwargs):
        self.timeout = timeout
        super().__init__(*args, **kwargs)

    def send(self, request: PreparedRequest, **kwargs) -> Response:
        kwargs['timeout'] = kwargs.get('timeout') or self.timeout
        try:
            return super().send(request, **kwargs)
        except requests.exceptions.ReadTimeout: #FIXME: Bad way to do a retry
            return super().send(request, **kwargs)


def new_session() -> requests.Session:
    """ Return requests.Session with batteries included; i.e. timeout, retries, error-raising. """
    session = requests.session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        #method_whitelist=["HEAD", "GET", "OPTIONS"]
    )
    session.mount('https://', DefaultTimeoutAdapter(timeout=5, max_retries=retry_strategy))
    session.hooks = {
        'response': lambda r, *args, **kwargs: r.raise_for_status() #FIXME: Will crash when product search is empty, e.g. ""
    }
    session.headers.update({
        'User-Agent': 'coles_vs_woolies'  # some User-Agent
    })
    return session
