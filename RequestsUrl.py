import aiohttp

class AddressService:
    def __init__(self, FASTAPI_URL: str):
        self.FASTAPI_URL = FASTAPI_URL

    async def get_request(self, address: str, json: dict | None = None) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(self.FASTAPI_URL + address, json=json) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    response.raise_for_status()  # Вызывает исключение для статусов 4xx и 5xx

    async def post_request(self, address: str, json: dict | None = None) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.post(self.FASTAPI_URL + address, json=json) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    response.raise_for_status()

    async def put_request(self, address: str, json: dict | None = None) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.put(self.FASTAPI_URL + address, json=json) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    response.raise_for_status()

    async def delete_request(self, address: str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.delete(self.FASTAPI_URL + address) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    response.raise_for_status()

service = AddressService("http://localhost:8000")
