from ultralytics import YOLO
import asyncio
import re
import logging

logging.getLogger("ultralytics").setLevel(logging.ERROR)

regions = [
    '01', '02', '102', '702', '03', '103', '04', '05', '06', '07', '08', '09', '10', '11', '111', '12', '13', '113', '14', '116', '716', '17', '18', '118', '19', '21', '121', '22', '122', '23', '93', '123', '193', '24', '84', '88', '124', '25', '125', '725', '26', '126', '27', '28', '29', '30', '130', '31', '32', '33', '34', '134', '35', '36', '136', '37', '38', '85', '138', '39', '40', '41', '82', '42', '142', '43', '44', '45', '46', '47', '147', '48', '49', '50', '90', '150', '190', '750', '790', '51', '52', '152', '252', '53', '54', '154', '754', '55', '155', '56', '156', '57', '58', '158', '59', '81', '159', '60', '61', '161', '761', '62', '63', '163', '763', '64', '164', '65', '66', '96', '166', '196', '67', '68', '69', '70', '71', '72', '172', '73', '173', '74', '174', '774', '75', '80', '76', '77', '97', '99', '177', '197', '199', '777', '797', '799', '78', '98', '178', '198', '79', '80', '180', '81', '181', '82', '83', '84', '184', '85', '185', '86', '186', '87', '89', '92', '94', '95'
]

letters = {
    "A": "А", "B": "В", "C": "С", "E": "Е", "H": "Н", "K": "К", "M": "М", "O": "О", "P": "Р", "T": "Т", "X": "Х", "Y": "У"
}

async def sort_letters(data: list) -> list:
    # Проверка на квадратный номер
    for i, y1 in enumerate(data):
        # Если сработает условие y1(верхняя линия) > y2(нижняя линия), то начнется сортировка
        if any(y1[1] > y2[3] for j, y2 in enumerate(data) if i != j):
            y_up = min(i[3] for i in data) # y верхней линии
            y_down = [i[1] for i in data if i[1] > y_up] # y нижней линии
            letters_down = [sublist for sublist in data if sublist[1] in y_down] # символы нижней линии
            letters_down = sorted(letters_down, key=lambda x: x[0]) # сортивка по x
            letters_up = [sublist for sublist in data if sublist not in letters_down] # символы верхней линии
            letters_up = sorted(letters_up, key=lambda x: x[0]) # сортивка по x
            sorted_data = letters_up + letters_down
            return sorted_data
    sorted_data = sorted(data, key=lambda x: x[0])
    return sorted_data


async def process_and_validate_carplate(data: list, class_names: dict) -> str:
    """
    Формирует строку номера и проверяет его на соответствие шаблону и регионам.
    Возвращает номер, если он валиден, иначе пустую строку.
    """
    number = ""
    for item in data:
        num_class = item[-1]
        number += class_names[num_class]
    carplate = "".join([letters.get(letter, letter) for letter in number])  # Замена англ букв на рус

    # Проверка на валидность
    pattern = r"^[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}$"
    if re.fullmatch(pattern, carplate):
        if (carplate[-3:] in regions and len(carplate) == 9) or (carplate[-2:] in regions and len(carplate) == 8):
            return carplate

    return ""


async def read_number(image_path: str) -> str:
    model = YOLO("plate_detection/models/model_rd_num_e500_v1.pt")
    confs = [0.1, 0.6, 0.75]
    for conf in confs:
        def run_model(conf):
            return model(image_path, conf=conf)
        result = await asyncio.to_thread(run_model, conf)
        result = result[0]
        class_names = result.names
        data = result.boxes.data.tolist()
        sorted_data = sorted(data, key=lambda x: x[0])
        carplate = await process_and_validate_carplate(sorted_data, class_names)
        if carplate:
            return carplate

        # Сортировка для квадратного номера
        sorted_data = await sort_letters(data)
        carplate = await process_and_validate_carplate(sorted_data, class_names)
        if carplate:
            return carplate
        
    return ""
    

if __name__ == "__main__":
    print(asyncio.run(read_number(r"plate_detection\Screenshot_2.jpg")))