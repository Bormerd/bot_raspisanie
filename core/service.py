import httpx
from typing import Optional, Dict, Any

async def get_request(url: str) -> Optional[Dict[str, Any]]:
    """Выполняет GET запрос к API"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"http://localhost:8000{url}")
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as e:
            print(f"Ошибка при выполнении запроса {url}: {e}")
            return None