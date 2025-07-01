import re
import asyncio
import aiohttp
from googletrans import Translator
from utils.utils import write_file_logs


def tr(data_dict: dict):
    brand = data_dict["brand"]
    model = data_dict["model"]
    translator = lambda t: Translator().translate(text=t, src="ru", dest="en").text
    if bool(re.fullmatch(r'[А-Я]+', brand)):
        brand = translator(brand)
    if bool(re.search(r'[А-Я]', model)):
        model = translator(model)
    letters_ru_en = {"А": "A", "В": "B", "С": "C", "Е": "E", "Н": "H", "К": "K", "М": "M", "О": "O", "Р": "P", "Т": "T", "Х": "X", "У": "Y"}
    data_dict["brand"] = "".join([letters_ru_en.get(letter, letter) for letter in brand]).strip().upper()
    data_dict["model"] = "".join([letters_ru_en.get(letter, letter) for letter in model]).strip().upper()
    return data_dict


async def get_data_car_request(number_car: str) -> dict:
    headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0"
        }
    try:
        async def get_token(session):
            data = {
                'token': (None, ''),
                'carplate': (None, number_car),
            }
            url = "https://auto.drom.ru/ajax/?mode=check_autohistory_report_captha&crossdomain_ajax_request=3"
            
            async with session.post(url=url, headers=headers, data=data) as response:    
                response_data = await response.json()
                return response_data['token']
        
        async with aiohttp.ClientSession() as session:
            token = await get_token(session)
            await asyncio.sleep(4)

            files = {'token': (None, token)}
            url = "https://auto.drom.ru/ajax/?mode=check_autohistory_gibdd_info&crossdomain_ajax_request=3"
            async with session.post(url, headers=headers, data=files) as response:
                response_data = await response.json()

            car_info = response_data["carData"]
            car_brand = car_info["model"].split()[0]
            try:
                car_model = car_info["model"].split(f"{car_brand} ")[1]
            except:
                text_error = f"[ERROR REQUEST] Данные характеристик некорректны. {number_car}"
                await write_file_logs(text_error)
                return False
            car_year = str(car_info["year"])
            try:
                car_volume = str(car_info["volume"])
            except:
                car_volume = ""
            try:
                car_power = str(car_info["power"])
            except:
                car_power = ""
            try:
                car_color = car_info["color"].capitalize()
            except:
                car_color = ""

            data_car_dict = {
                "number": number_car,
                "brand": car_brand.upper(),
                "model": car_model.upper(),
                "year": car_year,
                "volume": car_volume,
                "power": car_power,
                "color": car_color
            }
            data_car_dict = await asyncio.to_thread(tr, data_car_dict)

            log_text = f"[SUCCESSFUL REQUEST] Характеристики получены. {number_car}"
            return data_car_dict
    except Exception:
        log_text = f"[ERROR REQUEST] Характеристики не получены. {number_car}"
        return {}
    finally:
        await write_file_logs(log_text)


async def get_data_car(number_car: str):
    """Объединение функций"""
    for _ in range(5):
        task1 = await asyncio.create_task(get_data_car_request(number_car))
        if task1:
            return task1
        else:
            if task1 is not False:
                await asyncio.sleep(4)
            else:
                break

    return {}


if __name__ == "__main__":
    d = {"brand": "LЕХUS", "model": "GХ460"}
    s = tr(d)
    a = s["brand"]
    b = s["model"]
    for i in a:
        print(ord(i))
