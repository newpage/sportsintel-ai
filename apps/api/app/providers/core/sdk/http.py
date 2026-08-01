import json
from dataclasses import dataclass
from time import perf_counter
from urllib.request import Request, urlopen


@dataclass
class HttpResponse:
    status_code: int
    body: bytes
    elapsed_ms: float

    def json(self):
        return json.loads(self.body.decode("utf-8"))


class ProviderHttpClient:
    def __init__(self, user_agent: str = "SportsIntelAI/0.1") -> None:
        self.user_agent = user_agent

    def get_json(self, url: str, timeout: int = 30):
        started = perf_counter()
        request = Request(url, headers={"User-Agent": self.user_agent})
        with urlopen(request, timeout=timeout) as response:
            body = response.read()
            return HttpResponse(
                status_code=response.status,
                body=body,
                elapsed_ms=round((perf_counter() - started) * 1000, 2),
            )
