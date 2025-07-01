import os
import json
import aiohttp
from utils.utils import write_file_logs


async def get_access_token() -> str:
    if os.getenv("SECRET") == "":
        return ""

    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

    payload={
        'scope': 'GIGACHAT_API_PERS'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': '55089962-e035-4f86-aedf-856c20f48be3',
        'Authorization': f'Basic {os.getenv("SECRET")}'
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=payload, ssl=False) as response:
            res = await response.json()
            return res["access_token"]


async def send_promt(data_car: dict) -> str:
    brand = data_car["brand"]
    model = data_car["model"]
    year = data_car["year"]

    access_token = await get_access_token()
    if not access_token:
        return "Описание недоступно. Отсутсвует токен."
    
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

    msg = f"Расскажи кратко и информативно про машину {brand} {model} {year} года. Напиши 8-9 предложений"

    payload = json.dumps({
        "model": "GigaChat",
        "messages": [
            {
                "role": "user",
                "content": msg
            }
        ]
    })
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, headers=headers, data=payload, ssl=False) as response:
            res = await response.json()
            text = res["choices"][0]["message"]["content"]
            tokens_answer = res["usage"]["completion_tokens"]
            log_text = f"Потрачено токенов: {tokens_answer}"
            await write_file_logs(log_text)

            return text


if __name__ == "__main__":
    data_car = {
        "number": "TOYOTA",
        "brand": "TOYOTA",
        "model": "RAV4",
        "year": "2020",
        "volume": "150",
        "power": "100",
        "color": "x",
    }
    # print(send_promt(data_car))