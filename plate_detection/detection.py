import os
import asyncio
from ultralytics import YOLO
from PIL import Image
import logging
logging.getLogger("ultralytics").setLevel(logging.ERROR)


async def crop_img(image_path, box_xyxy: list, result_name) -> str:
    # Обрезаем изображение и сохраняем
    folder_save = r"images/result_images/"
    os.makedirs(folder_save, exist_ok=True)
    def crop_and_save():
        image = Image.open(image_path)
        cropped_image = image.crop(box_xyxy)
        save_path = f"{folder_save}/{result_name}"
        cropped_image.save(save_path)
        return save_path

    return await asyncio.to_thread(crop_and_save)


def find_max_box(result) -> list:
    # Находим самую большую площадь объекта
    boxes_xywh = result.boxes.xywh.tolist()
    boxes_square = [box[2] * box[3] for box in boxes_xywh]
    max_box_index = boxes_square.index(max(boxes_square))
    max_box = result.boxes.xyxy.tolist()[max_box_index]
    return max_box


async def detect_car(image_path, user_id) -> str:
    model = YOLO("plate_detection/models/yolo11n.pt")
    def run_model():
        return model(image_path, classes=2, conf=0.7)
    result = await asyncio.to_thread(run_model)
    result = result[0]
    if len(result) == 0:
        return ""
    box = find_max_box(result)
    crop_car = await crop_img(image_path, box, f"result_crop_car_{user_id}.jpg")
    return crop_car


async def detect_number(image_path, user_id) -> str:
    model = YOLO("plate_detection/models/model_det_num_e300.pt")
    def run_model():
        return model(image_path, conf=0.65)
    result = await asyncio.to_thread(run_model)
    result = result[0]
    if len(result) == 0:
        return ""
    box = find_max_box(result)
    crop_number = await crop_img(image_path, box, f"result_crop_number_{user_id}.jpg")
    return crop_number


async def detect(image_path: str, user_id: str) -> str:
    number_crop = await detect_number(image_path=image_path, user_id=user_id)
    # Пробуем найти номер
    if number_crop:
        return number_crop
    else:
        # Пробуем найти машину
        car_crop = await detect_car(image_path=image_path, user_id=user_id)
        if car_crop:
            number_crop = await detect_number(image_path=car_crop, user_id=user_id)
            # Пробуем найти номер на машине
            if number_crop:
                # Найдена машина, затем номер.
                return number_crop
            else:
                # Машина есть, номера нет
                return ""
        else:
            # Не нашли ни номера, ни машины
            return ""


if __name__ == "__main__":
    result = asyncio.run(detect_number(r"photo_2025-01-10_18-26-27.jpg", 1))
    print(result)
