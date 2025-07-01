import json
import asyncio
import aiohttp
import aiofiles
import traceback
import config.config as cfg
from bs4 import BeautifulSoup
from pyvirtualdisplay import Display
from botasaurus.browser import browser, Driver
from utils.utils import write_file_logs


async def get_new_model(data_car: dict) -> str:
    try:
        if cfg.is_server:
            display = Display(backend="xvfb", visible=True, size=(1920, 1080))
            await asyncio.to_thread(display.start)

        @browser(
            output=None,
            wait_for_complete_page_load=False,
            add_arguments=['--no-sandbox']
        )
        def scrape(driver: Driver, data):
            try:
                brand = data["brand"].lower()
                model = data["model"].lower()
                models = set()
                brands = set()
                driver.get(f"https://duckduckgo.com/?t=h_&q={brand}+{model}+auto.drom.ru&ia=web")
                links_elems = driver.select_all(".Rn_JXVtoPVAFyGkcaXyK.VkOimy54PtIClAT3GMbr")[:3]
                for link_elem in links_elems:
                    link = link_elem.get_attribute("href")
                    if "drom" not in link.split("/")[2]:
                        continue
                    if len(link.split("/")) >= 5:
                        models.add(link.split("/")[4])
                    if len(link.split("/")) >= 6:
                        models.add(link.split("/")[5])
                if len(link.split("/")) >= 4:
                    brands.add(link.split("/")[3])
                if len(link.split("/")) >= 5:
                    brands.add(link.split("/")[4])
                text_success = f"Данные из duckduckgo получены: b:{brands}, m:{models}"
                return (list(brands), list(models)), text_success
            except Exception:
                text_error = f"Ошибка при поиски в duckduckgo:\n{traceback.format_exc()}"
                return ("", ""), text_error

        result = await asyncio.to_thread(scrape, data_car)
        await write_file_logs(result[1])
    finally:
        if cfg.is_server:
            await asyncio.to_thread(display.stop)
    return result[0]


async def get_price_car_request(data_car: dict) -> dict | bool:
    try:
        brand = data_car["brand"].lower()
        year = str(data_car["year"])

        async with aiofiles.open("database/models_for_drom.json", "r+", encoding="utf-8") as file_1:
            data_1 = json.loads(await file_1.read())

            if data_car["model"] in data_1 and data_1[data_car["model"]] != "":
                model = data_1[data_car["model"]]
            else:
                async with aiofiles.open("database/brands_models_drom.json", encoding="utf-8") as file_2:
                    data_2 = json.loads(await file_2.read())
                model = data_car["model"].replace(" ", "_")
                if brand in data_2:
                    values = data_2[brand]
                    find_result = model in values
                    brand_status = True
                else:
                    find_result = False
                    brand_status = False
                
                if not find_result:
                    for _ in range(2):
                        brands, models = await get_new_model(data_car)
                        if models:
                            if brands and not brand_status:
                                brand = next(b for b in brands if b in data_2)
                                values = data_2[brand]
                            model = next((m for m in models if m in values), "")
                            data_1[data_car["model"]] = model
                            await file_1.seek(0)
                            await file_1.write(json.dumps(data_1, ensure_ascii=False, indent=4))
                            await file_1.truncate()
                            if not model:
                                return False
                            break
                    else:
                        return False

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        
        url = f"https://auto.drom.ru/{brand}/{model.lower()}/year-{year}/?damaged=2&unsold=1&whereabouts[]=0"
        url_min_price = url + "&order=price"

        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, headers=headers) as response:
                response_text = await response.text()

                soup = BeautifulSoup(response_text, 'lxml')

                prices = []
                elem_prices = soup.find_all("div", class_="eyvqki91")
                count = int(soup.find("div", class_="eckkbc90").text.split()[0])
                if len(elem_prices) > count:
                    elem_prices = elem_prices[:count]
                for elem in elem_prices:
                    price = elem.find_all("span")[1].text
                    price = int(price.replace("\xa0", ""))
                    prices.append(price)

                avg_price = int(sum(prices) / len(prices))
                avg_price = f"{avg_price:,}".replace(",", ".")

            async with session.get(url=url_min_price, headers=headers) as response:
                response_text = await response.text()

                soup = BeautifulSoup(response_text, 'lxml')

                min_price = soup.find("div", class_="eyvqki91").find_all("span")[1].text
                min_price = int(min_price.replace("\xa0", ""))
                if min(prices) < min_price:
                    min_price = min(prices)
                min_price = f"{min_price:,}".replace(",", ".")

        data_car["min_price"] = min_price
        data_car["avg_price"] = avg_price
        data_car["url"] = url

        log_text = f'[SUCCESSFUL REQUEST] Цены получены. {data_car["number"]}'
        return data_car
    except Exception:
        log_text = f'[ERROR REQUEST] Цены не получены. {data_car["number"]}'
        return {}
    finally:
        await write_file_logs(log_text)
    

async def get_price_car(data_car: dict):
    if data_car:
        for _ in range(3):
            task1 = await asyncio.create_task(get_price_car_request(data_car))
            if task1 is False:
                break
            if task1:
                return task1
            else:
                await asyncio.sleep(3)
    return data_car
