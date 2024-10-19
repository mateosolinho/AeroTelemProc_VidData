import cv2
import pytesseract
import re
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from collections import deque
import csv
from openpyxl import Workbook

def detectar_angulo_nave(frame, angulos_buffer):
    # Definir las coordenadas de la ROI (ajústalas según tus necesidades)
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

def time_to_ms(time_text):
    parts = time_text.split(':')
    if len(parts) == 2 and all(part.isdigit() for part in parts):
        minutes, seconds = map(int, parts)
        totalsecs = minutes * 60 + seconds
        return totalsecs * 1000
    return 0

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

def moving_average(data, window_size):
    """Calcula el promedio móvil de una lista de números."""
    if len(data) < window_size:
        return np.mean(data) if data else 0
    return np.mean(data[-window_size:])

def time_to_seconds(time_text):
    """Convierte el tiempo en formato XX:XX:XX a segundos."""
    parts = time_text.split(':')
    
    # Hay 3 partes y que ninguna está vacía
    if len(parts) == 3 and all(part.isdigit() for part in parts):
        hours, minutes, seconds = map(int, parts)
        return hours * 3600 + minutes * 60 + seconds
    return 0  # Si no está en el formato correcto, devolver 0

def read_speed_and_altitude_from_video(video_path, profile, initTime, finishTime):
    cap = cv2.VideoCapture(video_path)

    cap.set(cv2.CAP_PROP_POS_MSEC, time_to_ms(initTime))
    
    profiles = {
        'SuperHeavy': {
            'rect_start_x': int(0.8 * 270),
            'rect_start_y': int(0.8 * 1135),
            'rect_width': 230,
            'rect_height': 35,
            'time_rect_start_x': 905,
            'time_rect_start_y': 950,
            'time_rect_width': 155,
            'time_rect_height': 45
        },
        'StarShip': {
            'rect_start_x': int(0.8 * 1750),
            'rect_start_y': int(0.8 * 1135),
            'rect_width': 230,
            'rect_height': 35,
            'time_rect_start_x': 905,
            'time_rect_start_y': 950,
            'time_rect_width': 155,
            'time_rect_height': 45
        },
        'Falcon9': {
            'rect_start_x': int(0.8 * 145),
            'rect_start_y': int(0.8 * 1205),
            'rect_width': 100,
            'rect_height': 40,
            'altitude_rect_x': int(0.8 * 345),
            'altitude_rect_y': int(0.8 * 1205),
            'time_rect_start_x': 890,
            'time_rect_start_y': 970,
            'time_rect_width': 200,
            'time_rect_height': 60
        }
    }
    
    if profile not in profiles:
        raise ValueError("Perfil no válido. Escoge entre: SuperHeavy, StarShip, Falcon9")
    
    current_profile = profiles[profile]
    
    rect_start_x = current_profile['rect_start_x']
    rect_start_y = current_profile['rect_start_y']
    rect_width = current_profile['rect_width']
    rect_height = current_profile['rect_height']
    time_rect_start_x = current_profile['time_rect_start_x']
    time_rect_start_y = current_profile['time_rect_start_y']
    time_rect_width = current_profile['time_rect_width']
    time_rect_height = current_profile['time_rect_height']

    # Coordenadas de altitud separadas si es Falcon 9
    if profile == 'Falcon9':
        altitude_rect_start_x = current_profile['altitude_rect_x']
        altitude_rect_start_y = current_profile['altitude_rect_y']
    else:
        altitude_rect_start_x = rect_start_x
        altitude_rect_start_y = rect_start_y + rect_height
        
    speed_buffer = deque(maxlen=5)  # Mantiene los últimos 5 valores
    altitude_buffer = deque(maxlen=5)  # Mantiene los últimos 5 valores

    frame_counter = 0  # Contador de fotogramas


    # Crear un archivo CSV para almacenar los datos
    with open('telemetry_data.csv', mode='w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['Time', 'Speed', 'Altitude'])

        # Crear un archivo .xlsx para almacenar los datos
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(['Time (seconds)', 'Speed', 'Altitude'])

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Asegúrate de que las coordenadas están dentro de los límites del cuadro
            height, width, _ = frame.shape
            if (rect_start_y + rect_height) > height or (rect_start_x + rect_width) > width:
                print("La región de velocidad excede el tamaño del cuadro.")
                continue  # O realiza algún otro manejo de errores aquí

            if frame_counter % 5 == 0:
                # Extrae las regiones donde se encuentran SPEED, ALTITUDE, y el contador de tiempo
                speed_region = frame[rect_start_y:rect_start_y + rect_height, rect_start_x:rect_start_x + rect_width]
                altitude_region = frame[altitude_rect_start_y:altitude_rect_start_y + rect_height, altitude_rect_start_x:altitude_rect_start_x + rect_width]
                time_region = frame[time_rect_start_y:time_rect_start_y + time_rect_height, time_rect_start_x:time_rect_start_x + time_rect_width]

                # Dibuja rectángulos sobre las regiones de interés
                cv2.rectangle(frame, (rect_start_x, rect_start_y), (rect_start_x + rect_width, rect_start_y + rect_height), (0, 255, 0), 2)
                cv2.rectangle(frame, (altitude_rect_start_x, altitude_rect_start_y), (altitude_rect_start_x + rect_width, altitude_rect_start_y + rect_height), (255, 0, 0), 2)
                cv2.rectangle(frame, (time_rect_start_x, time_rect_start_y), (time_rect_start_x + time_rect_width, time_rect_start_y + time_rect_height), (0, 0, 255), 2)

                # Limpia las imágenes antes de extraer texto
                cleaned_speed_region = cleanup(speed_region)
                cleaned_altitude_region = cleanup(altitude_region)
                cleaned_time_region = cleanup(time_region)

                # Realiza la extracción de texto en paralelo
                with ThreadPoolExecutor() as executor:
                    speed_future = executor.submit(extract_text, cleaned_speed_region)
                    altitude_future = executor.submit(extract_text, cleaned_altitude_region)
                    time_future = executor.submit(extract_text, cleaned_time_region)

                    speed_text = speed_future.result()
                    altitude_text = altitude_future.result()
                    time_text = time_future.result()

                # Limpia el texto detectado y extrae solo los números
                speed_numbers = re.findall(r'\d+', speed_text.replace('"', '').replace("'", '').strip())
                altitude_numbers = re.findall(r'\d+\.?\d*', altitude_text.replace('"', '').replace("'", '').strip())
                time_text = re.sub(r'[^0-9:]', '', time_text)

                # print(f"Texto detectado en la región de tiempo: {time_text.strip()}")

                # Obtener valores detectados
                if speed_numbers:
                    speed_value = int(speed_numbers[0])  # Convertir a entero para el promedio
                    speed_buffer.append(speed_value)  # Añadir al buffer
                else:
                    speed_value = "No speed detected"
                    
                angle, roi_with_lines = detectar_angulo_nave(frame, deque(maxlen=5))
                if angle is not None:    
                    print(f"Ángulo de la nave detectado: {angle:.2f} grados")
                else:
                    print(f"Ángulo de la nave no detectado")
                    

                if altitude_numbers:
                    last_altitude_value = float(altitude_numbers[0])  # Convertir a float
                    altitude_buffer.append(last_altitude_value)  # Añadir al buffer
                else:
                    last_altitude_value = "No altitude detected"
                
                # Guardar los datos en el CSV y en el archivo Excel
                csv_writer.writerow([time_text, speed_value, last_altitude_value])
                sheet.append([time_text, speed_value, last_altitude_value])

                # Muestra los valores detectados en el frame original
                cv2.putText(frame, f"Speed: {speed_value}", (rect_start_x, rect_start_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                cv2.putText(frame, f"Altitude: {last_altitude_value}", (altitude_rect_start_x, altitude_rect_start_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                cv2.putText(frame, f"Time: {time_text} seconds", (time_rect_start_x, time_rect_start_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            # Muestra el frame original con la detección
            cv2.imshow('Original Frame', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # Comprobación para finalizar el programa 
            if time_text == finishTime:
                print(f"Tiempo alcanzado: {time_text}. Deteniendo el programa.")
                break  # Salir del bucle
            frame_counter += 1  # Incrementa el contador de fotogramas

    cap.release()
    cv2.destroyAllWindows()

    # Guarda el archivo .xlsx
    workbook.save('telemetry_data.xlsx')

# Uso del programa
video_path = 'C:/Users/mateo/Desktop/AeroTelemProc_VidData/ift5.mp4'
read_speed_and_altitude_from_video(video_path, "StarShip", "25:15", "01:05:50")
