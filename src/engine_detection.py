import cv2
import numpy as np

# Función para verificar los círculos detectados y contar los motores encendidos
def verificar_circulos(circles, roi, motores_encendidos):
    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")

        for (x, y, r) in circles:
            if y >= roi.shape[0] or x >= roi.shape[1]:
                continue
              
            motor_color = roi[y, x]
                
            if np.mean(motor_color) > 200:
                motores_encendidos += 1
                
            cv2.circle(roi, (x, y), r, (0, 255, 0), 2)
            
    return motores_encendidos

# Función para analizar los motores en el frame dado
def analizar_motores(frame):
    resultados = {
        "starship": 0,
        "booster": 0
    }
    
    # Definir la región de interés para Satrship
    x1, y1, x2, y2 = 1700, 900, 1920, 1080
    roi = frame[y1:y2, x1:x2]
    
    # Convertir la ROI a escala de grises y aplicar desenfoque para una mejor detección
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blurred = cv2.medianBlur(gray, 5)
    
    # Detectar círculos en la ROI 
    circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1.2, minDist=5, param1=50, param2=30, minRadius=10, maxRadius=30)
    resultados["starship"] = verificar_circulos(circles, roi, resultados["starship"])
    
    # Definir la región de interés para el Booster
    x1, y1, x2, y2 = 20, 900, 180, 1080
    roi = frame[y1:y2, x1:x2]
    
    # De nuevo convertir la ROI a escala de grises y aplicar desenfoque
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blurred = cv2.medianBlur(gray, 5)
    
    # Detectar círculos en la ROI
    circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=3, param2=20, minRadius=3, maxRadius=10)
    resultados["booster"] = verificar_circulos(circles, roi, resultados["booster"])
    
    return resultados