import asyncio
import logging
from typing import Dict, List, Optional

import aiohttp


logger = logging.getLogger("VibeOps.LobsterSkill")


class LobsterFetcherSkill:
    """
    Skill: high-concurrency async fetch with:
    - a semaphore for backpressure
    - retries with exponential backoff
    - short timeouts so demos don't hang
    """

    def __init__(
        self,
        concurrency_limit: int = 10,
        retries: int = 3,
        request_timeout_s: float = 5.0,
    ):
        self.concurrency_limit = concurrency_limit
        self.retries = retries
        self.request_timeout_s = request_timeout_s

    async def _fetch_target(self, session: aiohttp.ClientSession, target_id: int) -> Dict:
        url = f"https://jsonplaceholder.typicode.com/posts/{target_id}"
        headers = {"User-Agent": "Lobster/1.0 (VibeOps Portfolio)"}

        backoff_s = 0.3
        last_err: Optional[str] = None

        for attempt in range(1, self.retries + 1):
            try:
                async with session.get(url, headers=headers, timeout=self.request_timeout_s) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return {
                        "id": target_id,
                        "status": "success",
                        "length": len(str(data)),
                    }
            except Exception as e:
                last_err = f"{type(e).__name__}: {e}"
                logger.debug("Harvest failed id=%s attempt=%s/%s err=%s", target_id, attempt, self.retries, last_err)
                if attempt < self.retries:
                    await asyncio.sleep(backoff_s)
                    backoff_s *= 2.0

        return {"id": target_id, "status": "failed", "error": last_err or "unknown_error"}

    async def harvest_async(self, target_range: int) -> List[Dict]:
        semaphore = asyncio.Semaphore(self.concurrency_limit)
        connector = aiohttp.TCPConnector(limit=self.concurrency_limit)

        async with aiohttp.ClientSession(connector=connector) as session:
            async def bounded_fetch(i: int) -> Dict:
                async with semaphore:
                    return await self._fetch_target(session, i)

            tasks = [bounded_fetch(i) for i in range(1, target_range + 1)]
            return await asyncio.gather(*tasks)

    def harvest(self, target_range: int) -> List[Dict]:
        return asyncio.run(self.harvest_async(target_range))

