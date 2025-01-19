import cv2
import numpy as np

def check_circles(circles, roi, engines_on):
    """Check the detected circles and count the engines that are on."""
    
    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")

        for (x, y, r) in circles:
            if y >= roi.shape[0] or x >= roi.shape[1]:
                continue
              
            motor_color = roi[y, x]
                
            if np.mean(motor_color) > 200:
                engines_on += 1
                
            cv2.circle(roi, (x, y), r, (0, 255, 0), 2)
            
    return engines_on

def analyze_engines(frame):
    """Analyze the engines in the given frame."""
    
    results = {
        "starship": 0,
        "booster": 0
    }
    
    # Define the region of interest for Starship
    x1, y1, x2, y2 = 1700, 900, 1920, 1080
    roi = frame[y1:y2, x1:x2]
    
    # Convert ROI to grayscale and apply blur for better detection
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blurred = cv2.medianBlur(gray, 5)
    
    # Detect circles in ROI
    circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1.2, minDist=5, param1=50, param2=30, minRadius=10, maxRadius=30)
    results["starship"] = check_circles(circles, roi, results["starship"])
    
    # Define the region of interest for the Booster
    x1, y1, x2, y2 = 20, 900, 180, 1080
    roi = frame[y1:y2, x1:x2]
    
    # Again convert the ROI to grayscale and apply blur
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blurred = cv2.medianBlur(gray, 5)
    
    # Detect circles in ROI
    circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=3, param2=20, minRadius=3, maxRadius=10)
    results["booster"] = check_circles(circles, roi, results["booster"])
    
    return results