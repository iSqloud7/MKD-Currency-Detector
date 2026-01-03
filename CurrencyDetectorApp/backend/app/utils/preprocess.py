import cv2
import numpy as np
from PIL import Image


def preprocess_image(image: Image.Image, target_size: int = 640):
    img = np.array(image)

    if len(img.shape) == 3 and img.shape[2] == 3:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    h, w = img.shape[:2]
    scale = target_size / max(h, w)
    new_w, new_h = int(w * scale), int(h * scale)

    img_resized = cv2.resize(img, (new_w, new_h))

    pad_w = (target_size - new_w) // 2
    pad_h = (target_size - new_h) // 2

    img_padded = cv2.copyMakeBorder(
        img_resized, pad_h, target_size - new_h - pad_h,
        pad_w, target_size - new_w - pad_w,
        cv2.BORDER_CONSTANT, value=(114, 114, 114)
    )

    return img_padded
