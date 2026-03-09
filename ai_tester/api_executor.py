from __future__ import annotations

from typing import Optional

import httpx

from .models import APIAction


class APIExecutor:
    """
    ╨Я╤А╨╛╤Б╤В╨╛╨╣ HTTP-╨║╨╗╨╕╨╡╨╜╤В ╨┐╨╛╨▓╨╡╤А╤Е httpx ╨┤╨╗╤П ╨▓╤Л╨┐╨╛╨╗╨╜╨╡╨╜╨╕╤П APIAction.
    """

    def __init__(self, base_url: Optional[str] = None) -> None:
        self._base_url = base_url

    async def run_action(self, action: APIAction) -> str:
        async with httpx.AsyncClient(base_url=self._base_url, timeout=30) as client:
            resp = await client.request(
                method=action.method,
                url=action.path,
                params=action.query or None,
                headers=action.headers or None,
                json=action.body,
            )

            if resp.status_code != action.expected_status:
                return f"╨Ю╨╢╨╕╨┤╨░╨╗╤Б╤П ╤Б╤В╨░╤В╤Г╤Б {action.expected_status}, ╨┐╨╛╨╗╤Г╤З╨╡╨╜ {resp.status_code}. ╨в╨╡╨╗╨╛: {resp.text[:500]}"

            if action.expected_body_contains is not None:
                try:
                    data = resp.json()
                except ValueError:
                    return f"╨Ю╨╢╨╕╨┤╨░╨╗╤Б╤П JSON-╨╛╤В╨▓╨╡╤В, ╨┐╨╛╨╗╤Г╤З╨╡╨╜ ╤В╨╡╨║╤Б╤В: {resp.text[:200]}"

                for key, value in action.expected_body_contains.items():
                    if data.get(key) != value:
                        return (
                            f"╨Ю╨╢╨╕╨┤╨░╨╗╨╛╤Б╤М ╨┐╨╛╨╗╨╡ {key}={value!r}, ╤Д╨░╨║╤В╨╕╤З╨╡╤Б╨║╨╕ {data.get(key)!r}. "
                            f"╨з╨░╤Б╤В╤М ╤В╨╡╨╗╨░: {str(data)[:500]}"
                        )

            return f"╨г╤Б╨┐╨╡╤И╨╜╤Л╨╣ ╨╛╤В╨▓╨╡╤В {resp.status_code}"

