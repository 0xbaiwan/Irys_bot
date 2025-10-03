import asyncio
import os
import sys

from sys import exit
from collections import deque
from better_proxy import Proxy
from loguru import logger


class ProxyManager:
    def __init__(self, check_uniqueness: bool) -> None:
        self.check_uniqueness = check_uniqueness
        self.proxies = deque()
        self.lock = asyncio.Lock()
        self.active_proxies = set()

    def load_proxy(self, proxies: list[str]) -> None:
        self.proxies = deque([Proxy.from_str(proxy) for proxy in proxies])

    async def get_proxy(self) -> Proxy | None:
        async with self.lock:
            if self.proxies: # If there are proxies, proceed as before
                proxy = self.proxies.popleft()
                if self.check_uniqueness:
                    if proxy in self.active_proxies:
                        # If proxy is already active and uniqueness is checked, try next one
                        # Re-add to the end of the deque to avoid infinite loop if all are active
                        self.proxies.append(proxy)
                        return await self.get_proxy() # Recursive call to get next available
                    else:
                        self.active_proxies.add(proxy)
                        return proxy
                else:
                    return proxy
            else: # If no proxies, return None
                logger.warning("代理文件为空，将使用本地网络连接。") # Change to warning
                return None

    async def release_proxy(self, proxy: Proxy | str) -> None:
        async with self.lock:
            self.proxies.append(proxy)
            if proxy in self.active_proxies:
                self.active_proxies.remove(proxy)

    async def remove_proxy(self, proxy: Proxy | str) -> bool:
        async with self.lock:
            try:
                self.proxies.remove(proxy)
                if proxy in self.active_proxies:
                    self.active_proxies.remove(proxy)

                return True
            except ValueError:
                return False
