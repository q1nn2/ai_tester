from __future__ import annotations

from typing import Optional

from playwright.async_api import Page, async_playwright

from .models import UIAction


class BrowserExecutor:
    """
    ╨Ю╨▒╤С╤А╤В╨║╨░ ╨╜╨░╨┤ Playwright ╨┤╨╗╤П ╨▓╤Л╨┐╨╛╨╗╨╜╨╡╨╜╨╕╤П UIAction.

    ╨Т╤Л╨┐╨╛╨╗╨╜╤П╨╡╤В ╨┐╤А╨╛╤Б╤В╤Л╨╡ ╤И╨░╨│╨╕:
    - open_url
    - click
    - fill
    - wait_for_text
    """

    def __init__(self, base_url: Optional[str] = None) -> None:
        self._base_url = base_url.rstrip("/") if base_url else None
        self._page: Optional[Page] = None
        self._playwright = None
        self._browser = None

    async def __aenter__(self) -> "BrowserExecutor":
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=True)
        context = await self._browser.new_context()
        self._page = await context.new_page()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def run_action(self, action: UIAction) -> str:
        if not self._page:
            raise RuntimeError("BrowserExecutor ╨╜╨╡ ╨╕╨╜╨╕╤Ж╨╕╨░╨╗╨╕╨╖╨╕╤А╨╛╨▓╨░╨╜. ╨Ш╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╣╤В╨╡ ╨║╨╛╨╜╤В╨╡╨║╤Б╤В╨╜╤Л╨╣ ╨╝╨╡╨╜╨╡╨┤╨╢╨╡╤А.")

        page = self._page

        if action.kind == "open_url":
            url = action.url
            if self._base_url and url and url.startswith("/"):
                url = f"{self._base_url}{url}"
            if not url:
                raise ValueError("╨Ф╨╗╤П ╨┤╨╡╨╣╤Б╤В╨▓╨╕╤П open_url ╤В╤А╨╡╨▒╤Г╨╡╤В╤Б╤П ╨┐╨╛╨╗╨╡ url.")
            await page.goto(url)
            return f"╨Ю╤В╨║╤А╤Л╤В URL: {url}"

        if action.kind == "click":
            if not action.selector:
                raise ValueError("╨Ф╨╗╤П ╨┤╨╡╨╣╤Б╤В╨▓╨╕╤П click ╤В╤А╨╡╨▒╤Г╨╡╤В╤Б╤П selector.")
            await page.click(action.selector)
            return f"╨Ъ╨╗╨╕╨║ ╨┐╨╛ ╤Б╨╡╨╗╨╡╨║╤В╨╛╤А╤Г {action.selector}"

        if action.kind == "fill":
            if not action.selector:
                raise ValueError("╨Ф╨╗╤П ╨┤╨╡╨╣╤Б╤В╨▓╨╕╤П fill ╤В╤А╨╡╨▒╤Г╨╡╤В╤Б╤П selector.")
            await page.fill(action.selector, action.text or "")
            return f"╨Т╨▓╨╛╨┤ ╤В╨╡╨║╤Б╤В╨░ ╨▓ {action.selector}"

        if action.kind == "wait_for_text":
            if not action.text:
                raise ValueError("╨Ф╨╗╤П ╨┤╨╡╨╣╤Б╤В╨▓╨╕╤П wait_for_text ╤В╤А╨╡╨▒╤Г╨╡╤В╤Б╤П text.")
            await page.wait_for_timeout(action.extra.get("timeout_ms", 5000))
            # ╨г╨┐╤А╨╛╤Й╤С╨╜╨╜╨░╤П ╤А╨╡╨░╨╗╨╕╨╖╨░╤Ж╨╕╤П: ╨╝╨╛╨╢╨╜╨╛ ╨┤╨╛╤А╨░╨▒╨╛╤В╨░╤В╤М ╨┤╨╛ ╨╛╨╢╨╕╨┤╨░╨╜╨╕╤П ╨║╨╛╨╜╨║╤А╨╡╤В╨╜╨╛╨│╨╛ ╤Б╨╡╨╗╨╡╨║╤В╨╛╤А╨░/╤В╨╡╨║╤Б╤В╨░.
            return f"╨Ю╨╢╨╕╨┤╨░╨╜╨╕╨╡ ╤В╨╡╨║╤Б╤В╨░ '{action.text}' (╨┐╤Б╨╡╨▓╨┤╨╛-╨╛╨╢╨╕╨┤╨░╨╜╨╕╨╡)"

        raise ValueError(f"╨Э╨╡╨╕╨╖╨▓╨╡╤Б╤В╨╜╤Л╨╣ ╤В╨╕╨┐ UIAction: {action.kind}")

