import aiosqlite
from utils.utils import write_file_logs


async def add_data_db(data_car: dict) -> None:
    number = data_car["number"]
    brand = data_car["brand"]
    model = data_car["model"]
    year = int(data_car["year"]) if data_car["year"] != "" else ""
    volume = float(data_car["volume"]) if data_car["volume"] != "" else ""
    power = round(float(data_car["power"])) if data_car["power"] != "" else ""
    color = data_car["color"]
    
    async with aiosqlite.connect("database/cars_database.db") as connection:
        cursor = await connection.cursor()

        id_value = {}
        table_data = [
            ("Brands", "name", brand),
            ("Models", "name", model),
            ("Years", "year", year),
            ("Volumes", "volume", volume),
            ("Powers", "power", power),
            ("Colors", "name", color),
        ]

        for t_name, col_name, value in table_data:
            # Добавляем данные. Если такие есть, то не добавляются
            await cursor.execute(f"INSERT OR IGNORE INTO {t_name}({col_name}) VALUES (?)", (value,))
            await connection.commit()
            # Получаем id
            await cursor.execute(f"SELECT id FROM {t_name} WHERE {col_name} = ?", (value,))
            id_value[t_name] = (await cursor.fetchone())[0]

        brand_id = id_value["Brands"]
        model_id = id_value["Models"]
        year_id = id_value["Years"]
        volume_id = id_value["Volumes"]
        power_id = id_value["Powers"]
        color_id = id_value["Colors"]

        await cursor.execute("SELECT COUNT(*) FROM Carplates WHERE number = ?", (number,))
        count = (await cursor.fetchone())[0]
        if count > 0:
            await cursor.execute("DELETE FROM Carplates WHERE number=?", (number,))
            await connection.commit()
        await cursor.execute("""
                    INSERT INTO Carplates(number, brand, model, year, volume, power, color)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (number, brand_id, model_id, year_id, volume_id, power_id, color_id))
        await connection.commit()
        

async def add_description(data_car: dict, text: str):
    try:
        brand = data_car["brand"]
        model = data_car["model"]
        year = int(data_car["year"])
        
        id_value = {}
        table_data = [
            ("Brands", "name", brand),
            ("Models", "name", model),
            ("Years", "year", year)
        ]

        async with aiosqlite.connect("database/cars_database.db") as connection:
            cursor = await connection.cursor()
            for t_name, col_name, value in table_data:
                await cursor.execute(f"SELECT id FROM {t_name} WHERE {col_name} = ?", (value,))
                id_value[t_name] = (await cursor.fetchone())[0]
            
            brand_id = id_value["Brands"]
            model_id = id_value["Models"]
            year_id = id_value["Years"]

            await cursor.execute(f"INSERT INTO Descriptions (brand, model, year, description) VALUES (?, ?, ?, ?)", 
                                (brand_id, model_id, year_id, text))
            await connection.commit()

    except Exception as ex:
        text_error = f"[ERROR] Не удалось добавить описание... Ошибка: {ex}"
        await write_file_logs(text_error)


async def get_description(data_car: dict) -> str:
    brand = data_car["brand"]
    model = data_car["model"]
    year = int(data_car["year"])
    result_text = ""
    
    async with aiosqlite.connect("database/cars_database.db") as connection:
        cursor = await connection.cursor()

        id_value = {}
        table_data = [
                ("Brands", "name", brand),
                ("Models", "name", model),
                ("Years", "year", year)
            ]
        for t_name, col_name, value in table_data:
            await cursor.execute(f"SELECT id FROM {t_name} WHERE {col_name} = ?", (value,))
            id_value[t_name] = (await cursor.fetchone())[0]

        brand_id = id_value["Brands"]
        model_id = id_value["Models"]
        year_id = id_value["Years"]

        await cursor.execute(f"SELECT description FROM Descriptions WHERE brand = ? AND model = ? AND year = ?", 
                            (brand_id, model_id, year_id))
        res = await cursor.fetchone()

        if res is not None:
            result_text = res[0]

    return result_text


async def get_data_db(car_number: str) -> dict:
    async with aiosqlite.connect("database/cars_database.db") as connection:
        cursor = await connection.cursor()

        query = f"SELECT * FROM Carplates WHERE number = ?"
        await cursor.execute(query, (car_number,))

        # Есть ли данные в базе
        result = await cursor.fetchone()
        if result:
            car_values = {"number": car_number}
            table_data = [
                ("Brands", "name", "brand"),
                ("Models", "name", "model"),
                ("Years", "year", "year"),
                ("Volumes", "volume", "volume"),
                ("Powers", "power", "power"),
                ("Colors", "name", "color"),
            ]

            # Извлекаем данные
            for t_name, col_name, col_name_cp in table_data:
                await cursor.execute(f"""
                                    SELECT {t_name}.{col_name} FROM {t_name}
                                    INNER JOIN Carplates
                                        ON Carplates.{col_name_cp} = {t_name}.id
                                    WHERE Carplates.number = '{car_number}'
                                    """)
                try:
                    car_values[col_name_cp] = (await cursor.fetchone())[0]
                except TypeError:
                    await cursor.execute("DELETE FROM Carplates WHERE number=?", (car_number,))
                    await connection.commit()
                    return {}
            return car_values
        return {}
