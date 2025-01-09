# Credits: This code is based on the work of the authors named @LaunchLabsLive, i have permission to use and modify the code.

import cv2
import logging

class PropellantAnalyzer:
    def __init__(self):
        pass

    def analyze_propellant_bar(self, frame, line_coordinates):
        if not isinstance(line_coordinates, tuple) or len(line_coordinates) != 4:
            logging.error("Invalid line coordinates provided")
            return "N/A"

        x1, y1, x2, y2 = line_coordinates

        if y1 != y2:
            logging.error("The provided line is not horizontal")
            return "N/A"

        roi = frame[y1:y1 + 1, x1:x2]
        if roi.size == 0:
            logging.error("Empty ROI extracted")
            return "N/A"

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        pixel_values = gray.flatten().astype(float)  # Convert to float for arithmetic operations

        # Normalize the pixel values between 0 and 255
        normalized_pixel_values = cv2.normalize(pixel_values, None, 0, 255, cv2.NORM_MINMAX).flatten()

        # Detect the increase in grayscale values from the end of the line
        increase_threshold = 50  # Define a threshold for detecting a significant increase
        previous_value = normalized_pixel_values[-1]
        increase_index = None
        increase_position = None

        for i in range(len(normalized_pixel_values) - 2, -1, -1):
            if normalized_pixel_values[i] > previous_value + increase_threshold:
                increase_index = i
                # Linear interpolation for sub-pixel accuracy
                lower_value = normalized_pixel_values[i]
                upper_value = previous_value
                if upper_value != lower_value:
                    position_within_pixel = (previous_value + increase_threshold - lower_value) / (upper_value - lower_value)
                else:
                    position_within_pixel = 0  # Avoid division by zero
                increase_position = i + position_within_pixel
                break
            previous_value = normalized_pixel_values[i]

        if increase_position is None:
            #logging.error("No significant increase detected in grayscale values")
            return "N/A"

        # Calculate the percentage of the bar filled with sub-pixel resolution
        percent_filled = (increase_position / len(normalized_pixel_values)) * 100

        return percent_filled