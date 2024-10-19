import cv2
import pytesseract
import re
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from collections import deque
import csv
from openpyxl import Workbook

# Funciones
def time_to_ms(time_text):
    parts = time_text.split(':')
    if len(parts) == 2 and all(part.isdigit() for part in parts):
        minutes, seconds = map(int, parts)
        totalsecs = minutes * 60 + seconds
        return totalsecs * 1000
    return 0

def cleanup(im):
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
    custom_config = r'--oem 3 --psm 6'
    return pytesseract.image_to_string(image_region, config=custom_config)

def moving_average(data, window_size):
    if len(data) < window_size:
        return np.mean(data) if data else 0
    return np.mean(data[-window_size:])

# Función principal con soporte de perfiles
def read_speed_and_altitude_from_video(video_path, profile, init, finalTime=-1):
    cap = cv2.VideoCapture(video_path)
    
    cap.set(cv2.CAP_PROP_POS_MSEC, time_to_ms(init))
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    wait_time = int(1000 / fps)

    
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

    altitude_buffer = deque(maxlen=5)
    frame_counter = 0

    last_speed_value = "No speed detected"
    last_altitude_value = "No altitude detected"
    last_time_text = "00:00:00"

    with open('telemetry_data.csv', mode='w', newline='') as csvfile:        
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['Time', 'Speed', 'Altitude'])

        workbook = Workbook()
        sheet = workbook.active
        sheet.append(['Time (seconds)', 'Speed', 'Altitude'])

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            height, width, _ = frame.shape
            if (rect_start_y + rect_height) > height or (rect_start_x + rect_width) > width:
                print("La región de velocidad excede el tamaño del cuadro.")
                continue

            if frame_counter % 5 == 0:
                print(frame_counter)
                speed_region = frame[rect_start_y:rect_start_y + rect_height, rect_start_x:rect_start_x + rect_width]
                altitude_region = frame[altitude_rect_start_y:altitude_rect_start_y + rect_height, altitude_rect_start_x:altitude_rect_start_x + rect_width]
                time_region = frame[time_rect_start_y:time_rect_start_y + time_rect_height, time_rect_start_x:time_rect_start_x + time_rect_width]

                cleaned_speed_region = cleanup(speed_region)
                cleaned_altitude_region = cleanup(altitude_region)
                cleaned_time_region = cleanup(time_region)

                with ThreadPoolExecutor() as executor:
                    speed_future = executor.submit(extract_text, cleaned_speed_region)
                    altitude_future = executor.submit(extract_text, cleaned_altitude_region)
                    time_future = executor.submit(extract_text, cleaned_time_region)

                    speed_text = speed_future.result()
                    altitude_text = altitude_future.result()
                    time_text = time_future.result()

                speed_numbers = re.findall(r'\d+', speed_text.replace('"', '').replace("'", '').strip())
                altitude_numbers = re.findall(r'\d+\.?\d*', altitude_text.replace('"', '').replace("'", '').strip())
                time_text = re.sub(r'[^0-9:]', '', time_text)
                
                print(f"Texto detectado en la región de tiempo: {time_text.strip()}")

                if speed_numbers:
                    last_speed_value = int(speed_numbers[0])

                if altitude_numbers:
                    last_altitude_value = float(altitude_numbers[0])
                    altitude_buffer.append(last_altitude_value)
                    
                last_time_text = time_text if time_text else last_time_text

                csv_writer.writerow([last_time_text, last_speed_value, last_altitude_value])
                sheet.append([last_time_text, last_speed_value, last_altitude_value])

                # Dibuja los cuadros y el texto en cada cuadro
                cv2.rectangle(frame, (rect_start_x, rect_start_y), (rect_start_x + rect_width, rect_start_y + rect_height), (0, 255, 0), 2)
                cv2.rectangle(frame, (altitude_rect_start_x, altitude_rect_start_y), (altitude_rect_start_x + rect_width, altitude_rect_start_y + rect_height), (255, 0, 0), 2)
                cv2.rectangle(frame, (time_rect_start_x, time_rect_start_y), (time_rect_start_x + time_rect_width, time_rect_start_y + time_rect_height), (0, 0, 255), 2)

                cv2.putText(frame, f"Speed: {last_speed_value}", (rect_start_x, rect_start_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                cv2.putText(frame, f"Altitude: {last_altitude_value}", (altitude_rect_start_x, altitude_rect_start_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                cv2.putText(frame, f"Time: {last_time_text}", (time_rect_start_x, time_rect_start_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            cv2.imshow('Original Frame', frame)

            frame_counter += 1
            if cv2.waitKey(wait_time) & 0xFF == ord('q'):
                break

            if last_time_text == finalTime:
                print(f"Tiempo alcanzado: {finalTime}. Deteniendo el programa.")
                break

    cap.release()
    cv2.destroyAllWindows()
    workbook.save('telemetry_data.xlsx')

# Uso del programa
video_path = 'C:/Users/mateo/Desktop/python/projects/rocket_telemetry/s.mp4'
 
read_speed_and_altitude_from_video(video_path, 'Falcon9', "00:10", "00:08:22")

