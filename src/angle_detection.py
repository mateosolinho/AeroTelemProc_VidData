import cv2
import numpy as np
from collections import deque

def detectar_angulo_nave(frame, angulos_buffer):
    # Definir las coordenadas de la ROI para la detección de ángulos
    x1, y1, x2, y2 = 1170, 900, 1320, 1080  # Ejemplo de coordenadas para una ROI específica de Starship
    roi = frame[y1:y2, x1:x2]

    # Suavizar la imagen para reducir el ruido
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Detectar bordes con Canny
    canny = cv2.Canny(blurred, 50, 150, apertureSize=3)

    # Detección de líneas con HoughLines
    lines = cv2.HoughLines(canny, 1, np.pi / 180, 60, np.array([]))

    if lines is not None:
        angles = []
        for rho, theta in lines[:, 0]:
            # Convertir de coordenadas polares a cartesianas para la línea
            a = np.cos(theta)
            b = np.sin(theta)
            x0 = a * rho
            y0 = b * rho
            x1_line = int(x0 + 1000 * (-b))
            y1_line = int(y0 + 1000 * (a))
            x2_line = int(x0 - 1000 * (-b))
            y2_line = int(y0 - 1000 * (a))

            # Calcular el ángulo en grados
            angle = np.degrees(np.arctan2((y2_line - y1_line), (x2_line - x1_line)))
            angles.append(angle)

            # Dibujar la línea en la ROI para visualización
            cv2.line(roi, (x1_line, y1_line), (x2_line, y2_line), (0, 0, 255), 2)

        # Promediar los ángulos detectados
        angle_mean = np.mean(angles)

        # Agregar el ángulo detectado al buffer
        angulos_buffer.append(angle_mean)

        # Calcular el promedio móvil de los últimos ángulos
        if len(angulos_buffer) >= 5:
            smooth_angle = np.mean(angulos_buffer)
        else:
            smooth_angle = angle_mean

        # Umbral para ignorar variaciones menores
        if abs(smooth_angle - angulos_buffer[-1]) < 2:  # Umbral de 2 grados
            smooth_angle = angulos_buffer[-1]

        return smooth_angle, roi
    else:
        return None, roi
