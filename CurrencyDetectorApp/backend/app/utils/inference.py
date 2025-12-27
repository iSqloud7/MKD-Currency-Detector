import cv2
import numpy as np
import os
from ultralytics import YOLO

MODEL_DIR = os.path.join(os.path.dirname(__file__), '../models')
model_path = os.path.join(MODEL_DIR, 'best.pt')
model = YOLO(model_path)

def is_coin_or_note(class_name):
    if 'coin' in class_name.lower():
        return 'coin'
    elif 'note' in class_name.lower():
        return 'note'
    return 'unknown'

def remove_background_circular(image, bbox):
    x1, y1, x2, y2 = map(int, bbox)
    cropped = image[y1:y2, x1:x2].copy()
    if cropped.size == 0: return np.zeros((1,1,4), dtype=np.uint8)

    gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5,5),0)
    circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=50,
                               param1=50, param2=30,
                               minRadius=int(min(cropped.shape[:2])*0.3),
                               maxRadius=int(max(cropped.shape[:2])*0.6))
    mask = np.zeros(cropped.shape[:2], dtype=np.uint8)
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for circle in circles[0,:1]:
            center = (circle[0], circle[1])
            radius = circle[2]
            cv2.circle(mask, center, radius, 255, -1)
    else:
        h,w = cropped.shape[:2]
        center = (w//2,h//2)
        axes = (int(w*0.45), int(h*0.45))
        cv2.ellipse(mask, center, axes, 0,0,360,255,-1)

    kernel = np.ones((5,5),np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.GaussianBlur(mask,(5,5),0)
    result = cropped.copy()
    bgra = cv2.cvtColor(result, cv2.COLOR_BGR2BGRA)
    bgra[:,:,3] = mask
    return bgra

def process_image(image_path, bg_removal_method='circular'):
    img = cv2.imread(image_path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = model(img)

    coins_with_bg_removed = []
    notes = []

    remove_bg_func = remove_background_circular

    for result in results:
        boxes = result.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            class_id = int(box.cls[0])
            class_name = result.names[class_id]
            confidence = float(box.conf[0])

            currency_type = is_coin_or_note(class_name)
            if currency_type == 'coin':
                coin_no_bg = remove_bg_func(img, [x1, y1, x2, y2])
                coins_with_bg_removed.append({'class':class_name,'confidence':confidence,'image':coin_no_bg,'bbox':[x1,y1,x2,y2]})
            elif currency_type == 'note':
                note_cropped = img[int(y1):int(y2), int(x1):int(x2)]
                notes.append({'class':class_name,'confidence':confidence,'image':note_cropped,'bbox':[x1,y1,x2,y2]})
    return img_rgb, coins_with_bg_removed, notes, results
