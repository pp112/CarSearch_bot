import re
from get_data.get_data_car import get_data_car
from get_data.get_price_car import get_price_car
from database.database_cars import add_data_db, get_data_db


async def search_car_number(carplate: str) -> dict:
    carplate = carplate.replace(" ", "").upper()
    pattern = r"^[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}$"
    if not re.fullmatch(pattern, carplate):
        message = "⚠️ Номер введен некорректно.\n\n✅ Пример номера: <b>А123АА145</b>\n\n🔄 Попробуйте еще раз."
        return message

    # Проверка наличия номера в базе
    result = await get_data_db(carplate)
    if not result:
        # Поиск данных машины
        result = await get_data_car(number_car=carplate)
        if result:
            await add_data_db(result)
        else:
            message = "😔 Не удалось найти данные по автомобилю"
            return message
        
    # Ищем цены 
    result_dict_with_price = await get_price_car(result)
    if "min_price" in result_dict_with_price:
        return result_dict_with_price
    
    return result


if __name__ == "__main__":
    import asyncio
    result = asyncio.run(search_car_number("Р381ОХ154"))
    print(result)
        
