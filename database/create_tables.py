import aiosqlite

async def create_tables_db() -> None:
    async with aiosqlite.connect("cars_database.db") as connection:
        cursor = await connection.cursor()

        # Удаление таблиц, для создания новых
        await cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = await cursor.fetchall()
        for table in tables:
            if table[0] != 'sqlite_sequence':
                await cursor.execute(f"DROP TABLE IF EXISTS {table[0]}")


        # Таблица брендов
        await cursor.execute("""
            CREATE TABLE Brands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE
            )
        """)

        # Таблица моделей
        await cursor.execute("""
            CREATE TABLE Models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE
            )
        """)

        # Таблица годов
        await cursor.execute("""
            CREATE TABLE Years (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER UNIQUE
            )
        """)

        # Таблица объемов двигателя
        await cursor.execute("""
            CREATE TABLE Volumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                volume INTEGER UNIQUE
            )
        """)

        # Таблица мощностей двигателя
        await cursor.execute("""
            CREATE TABLE Powers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                power INTEGER UNIQUE
            )
        """)

        # Таблица цветов
        await cursor.execute("""
            CREATE TABLE Colors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE
            )
        """)

        # Таблица описаний
        await cursor.execute("""
            CREATE TABLE Descriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand INTEGER NOT NULL,
                model INTEGER NOT NULL,
                year INTEGER NOT NULL,
                description TEXT NOT NULL,
                FOREIGN KEY (brand) REFERENCES Brands(id),
                FOREIGN KEY (model) REFERENCES Models(id),
                FOREIGN KEY (year) REFERENCES Years(id)
            )
        """)

        # Основная таблица
        await cursor.execute("""
            CREATE TABLE Carplates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number TEXT UNIQUE NOT NULL,
                brand INTEGER NOT NULL,
                model INTEGER NOT NULL,
                year INTEGER NOT NULL,
                volume INTEGER,
                power INTEGER,
                color INTEGER,
                FOREIGN KEY (brand) REFERENCES Brands(id),
                FOREIGN KEY (model) REFERENCES Models(id),
                FOREIGN KEY (year) REFERENCES Years(id),
                FOREIGN KEY (volume) REFERENCES Volumes(id),
                FOREIGN KEY (power) REFERENCES Powers(id),
                FOREIGN KEY (color) REFERENCES Years(id)
            )
        """)

        await connection.commit()
    
    print("БД и таблицы успешно созданы!")


if __name__ == "__main__":
    import asyncio
    try:
        confirm = input("Пересоздать базу данных? (y/n): ").strip().lower()
        if confirm == "y":
            asyncio.run(create_tables_db())
        elif confirm == "n":
            print("Программа отменена.")
    except KeyboardInterrupt:
        print("Программа отменена.")
