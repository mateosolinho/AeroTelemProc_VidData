import numpy as np
import pytesseract
import re

def cleanup(im):
    """Cleans up an image by subtracting its median pixel value and then scaling it."""
    arr = np.array(im, dtype=float)
    if arr.mean(axis=-1).max() < 200:
        arr[:] = 0  # if there is no text, return black image
    else:
        arr -= np.median(arr) + 5
        arrmax = arr.max(axis=(0, 1))
        if all(arrmax != 0):
            arr *= 255 / arrmax
        arr = arr.clip(0, 255)
    return arr.astype(np.uint8)

def extract_text(image_region):
    """Extract text from the provided image region."""
    custom_config = r'--oem 3 --psm 7'
    return pytesseract.image_to_string(image_region, config=custom_config)

def time_to_ms(time_text):
    """Converts time in HH:MM:SS format to milliseconds."""
    parts = time_text.split(':')
    if len(parts) == 3 and all(part.isdigit() for part in parts):
        hours, minutes, seconds = map(int, parts)
        total_secs = hours * 3600 + minutes * 60 + seconds
        print(total_secs*1000)
        return total_secs * 1000
    return 0

def time_to_seconds(time_text):
    """Converts time in HH:MM:SS format to seconds."""
    parts = time_text.split(':')
    if len(parts) == 3 and all(part.isdigit() for part in parts):
        hours, minutes, seconds = map(int, parts)
        return hours * 3600 + minutes * 60 + seconds
    return 0  # If not in the correct format, return 0

def moving_average(data, window_size):
    """Calculates the moving average of a list of numbers."""
    if len(data) < window_size:
        return np.mean(data) if data else 0
    return np.mean(data[-window_size:])
