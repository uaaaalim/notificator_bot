import asyncio
import aiohttp
from urllib.parse import urlparse


class RequestError(Exception):
    pass


async def request_json(
    session: aiohttp.ClientSession,
    method: str,
    url: str,
    *,
    logger,
    params: dict | None = None,
    headers: dict | None = None,
    json: dict | None = None,
    data=None,
    attempts: int = 3,
):
    parsed = urlparse(url)
    host = parsed.netloc
    path = parsed.path.lstrip("/")

    for attempt in range(1, attempts + 1):
        try:
            async with session.request(
                method=method,
                url=url,
                params=params,
                headers=headers,
                json=json,
                data=data,
            ) as resp:
                text = await resp.text()

                if 200 <= resp.status < 300:
                    try:
                        return await resp.json()
                    except Exception as e:
                        raise RequestError(
                            f"[{host}] {method} '{path}' returned non-JSON response: {text[:300]}"
                        ) from e

                if 500 <= resp.status < 600:
                    if attempt < attempts:
                        sleep_time = 2 ** attempt
                        logger.error(
                            f"[{host}] {method} '{path}' failed with {resp.status}. "
                            f"Attempt {attempt}/{attempts}. Retrying in {sleep_time}s"
                        )
                        await asyncio.sleep(sleep_time)
                        continue

                    raise RequestError(
                        f"[{host}] {method} '{path}' failed with {resp.status} after {attempts} attempts. "
                        f"Response: {text[:300]}"
                    )

                raise RequestError(
                    f"[{host}] {method} '{path}' failed with {resp.status}. "
                    f"Response: {text[:300]}"
                )

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            if attempt < attempts:
                sleep_time = 2 ** attempt
                logger.error(
                    f"[{host}] {method} '{path}' network error on attempt {attempt}/{attempts}: {e}. "
                    f"Retrying in {sleep_time}s"
                )
                await asyncio.sleep(sleep_time)
                continue

            raise RequestError(
                f"[{host}] {method} '{path}' failed after {attempts} attempts due to network error: {e}"
            ) from e

    raise RequestError(f"[{host}] {method} '{path}' failed")