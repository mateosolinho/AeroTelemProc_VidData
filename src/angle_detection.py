import cv2
import numpy as np
from collections import deque

def detect_ship_angle(frame, angles_buffer):
    """Detects the angle of the Starship in the given frame."""
    
    # Define ROI coordinates for angle detection
    x1, y1, x2, y2 = 1170, 900, 1320, 1080  # Example coordinates for a specific Starship ROI
    roi = frame[y1:y2, x1:x2]

    # Smooth the image to reduce noise
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Detect edges with Canny
    canny = cv2.Canny(blurred, 50, 150, apertureSize=3)

    # Line detection with HoughLines
    lines = cv2.HoughLines(canny, 1, np.pi / 180, 60, np.array([]))

    if lines is not None:
        angles = []
        for rho, theta in lines[:, 0]:
            # Convert from polar to Cartesian coordinates for the line
            a = np.cos(theta)
            b = np.sin(theta)
            x0 = a * rho
            y0 = b * rho
            x1_line = int(x0 + 1000 * (-b))
            y1_line = int(y0 + 1000 * (a))
            x2_line = int(x0 - 1000 * (-b))
            y2_line = int(y0 - 1000 * (a))

            # Calculate the angle in degrees
            angle = np.degrees(np.arctan2((y2_line - y1_line), (x2_line - x1_line)))
            angles.append(angle)

            # Draw the line in the ROI for visualization
            cv2.line(roi, (x1_line, y1_line), (x2_line, y2_line), (0, 0, 255), 2)

        # Average the detected angles
        angle_mean = np.mean(angles)

        # Add the detected angle to the buffer
        angles_buffer.append(angle_mean)

        # Calculate the moving average of the last angles
        if len(angles_buffer) >= 5:
            smooth_angle = np.mean(angles_buffer)
        else:
            smooth_angle = angle_mean

        # Threshold to ignore minor variations
        if abs(smooth_angle - angles_buffer[-1]) < 2:  # 2 degree threshold
            smooth_angle = angles_buffer[-1]

        return smooth_angle, roi
    else:
        return None, roi
