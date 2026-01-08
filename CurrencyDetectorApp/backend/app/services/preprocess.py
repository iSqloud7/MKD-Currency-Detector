import cv2
import numpy as np


def preprocess_image(image: np.ndarray, target_size: int = 640):
    original_h, original_w = image.shape[:2]

    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)

    image = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)

    image = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)

    scale = target_size / max(original_h, original_w)
    new_w = int(original_w * scale)
    new_h = int(original_h * scale)

    image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

    return image, scale
