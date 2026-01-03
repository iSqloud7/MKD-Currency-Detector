import os
import torch

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "app", "models")

BINARY_MODEL = os.path.join(MODEL_DIR, "binary_model.torchscript")
BANKNOTE_MODEL = os.path.join(MODEL_DIR, "banknote_model.torchscript")
COIN_MODEL = os.path.join(MODEL_DIR, "coin_model.torchscript")

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
IMAGE_SIZE = 640
