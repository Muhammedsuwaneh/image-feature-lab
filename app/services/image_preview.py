"""Encode MNIST uint8 images for the Qt Quick image source property."""

import base64

import cv2
import numpy as np


def digit_image_url(image: np.ndarray) -> str:
    pixels = np.rint(np.clip(np.asarray(image), 0, 255)).astype(np.uint8)
    preview = cv2.resize(pixels, (256, 256), interpolation=cv2.INTER_NEAREST)
    encoded, png_data = cv2.imencode(".png", preview)

    if not encoded:
        raise ValueError("Could not encode the processed image preview.")

    return "data:image/png;base64," + base64.b64encode(png_data).decode("ascii")
