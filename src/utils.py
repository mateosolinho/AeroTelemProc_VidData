import numpy as np
import pytesseract
import re

def cleanup(im):
    """Limpia una imagen restando su valor mediano de píxeles y luego escalándola."""
    arr = np.array(im, dtype=float)
    if arr.mean(axis=-1).max() < 200:
        arr[:] = 0  # si no hay texto, devuelve imagen en negro
    else:
        arr -= np.median(arr) + 5
        arrmax = arr.max(axis=(0, 1))
        if all(arrmax != 0):
            arr *= 255 / arrmax
        arr = arr.clip(0, 255)
    return arr.astype(np.uint8)

def extract_text(image_region):
    """Extrae texto de la región de imagen proporcionada."""
    custom_config = r'--oem 3 --psm 7'
    return pytesseract.image_to_string(image_region, config=custom_config)

def time_to_ms(time_text):
    """Convierte el tiempo en formato MM:SS a milisegundos."""
    parts = time_text.split(':')
    if len(parts) == 2 and all(part.isdigit() for part in parts):
        minutes, seconds = map(int, parts)
        totalsecs = minutes * 60 + seconds
        return totalsecs * 1000
    return 0

def time_to_seconds(time_text):
    """Convierte el tiempo en formato HH:MM:SS a segundos."""
    parts = time_text.split(':')
    if len(parts) == 3 and all(part.isdigit() for part in parts):
        hours, minutes, seconds = map(int, parts)
        return hours * 3600 + minutes * 60 + seconds
    return 0  # Si no está en el formato correcto, devolver 0

def moving_average(data, window_size):
    """Calcula el promedio móvil de una lista de números."""
    if len(data) < window_size:
        return np.mean(data) if data else 0
    return np.mean(data[-window_size:])
