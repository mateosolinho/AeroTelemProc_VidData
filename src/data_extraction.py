from concurrent.futures import ThreadPoolExecutor
import cv2
import csv
from openpyxl import Workbook
from collections import deque
from src.angle_detection import detectar_angulo_nave
from src.engine_detection import analizar_motores
from src.propelent_detection import PropellantAnalyzer
from src.utils import cleanup, extract_text, time_to_ms
import re

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
            'time_rect_height': 45,
            "line_coordinates_lox": (270, 1042, 500, 1042),
            "line_coordinates_ch4": (270, 1006, 500, 1006)
        },
        'StarShip': {
            'rect_start_x': int(0.8 * 1750),
            'rect_start_y': int(0.8 * 1135),
            'rect_width': 230,
            'rect_height': 35,
            'time_rect_start_x': 905,
            'time_rect_start_y': 950,
            'time_rect_width': 155,
            'time_rect_height': 45,
            "line_coordinates_lox": (1460, 1040, 1690, 1040),
            "line_coordinates_ch4": (1460, 1050, 1690, 1050)
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
    print(current_profile['line_coordinates_lox'])
    
    rect_start_x = current_profile['rect_start_x']
    rect_start_y = current_profile['rect_start_y']
    rect_width = current_profile['rect_width']
    rect_height = current_profile['rect_height']
    time_rect_start_x = current_profile['time_rect_start_x']
    time_rect_start_y = current_profile['time_rect_start_y']
    time_rect_width = current_profile['time_rect_width']
    time_rect_height = current_profile['time_rect_height']
    line_coordinates_lox = current_profile['line_coordinates_lox']
    line_coordinates_ch4 = current_profile['line_coordinates_ch4']

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

    analyzer = PropellantAnalyzer()

    # Crear un archivo CSV para almacenar los datos
    with open('C:/Users/mateo/Desktop/AeroTelemProc_VidData/data/telemetry_data.csv', mode='w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['Time', 'Speed', 'Altitude', 'Angle', 'SuperHeavy_Engines', 'Starship_Engines', 'LOX', 'CH4'])

        # Crear un archivo .xlsx para almacenar los datos
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(['Time', 'Speed', 'Altitude', 'Angle', 'SuperHeavy_Engines', 'Starship_Engines', 'LOX', 'CH4'])

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Me aseguro de que las coordenadas de la región de interés no excedan el tamaño del cuadro
            height, width, _ = frame.shape
            if (rect_start_y + rect_height) > height or (rect_start_x + rect_width) > width:
                print("La región de velocidad excede el tamaño del cuadro.")
                continue  # O realizo algún otro manejo de errores aquí

            # Extrae las regiones donde se encuentran SPEED, ALTITUDE, y el contador de tiempo
            speed_region = frame[rect_start_y:rect_start_y + rect_height, rect_start_x:rect_start_x + rect_width]
            altitude_region = frame[altitude_rect_start_y:altitude_rect_start_y + rect_height, altitude_rect_start_x:altitude_rect_start_x + rect_width]
            time_region = frame[time_rect_start_y:time_rect_start_y + time_rect_height, time_rect_start_x:time_rect_start_x + time_rect_width]

            # Dibuja rectángulos sobre las regiones de interés
            cv2.rectangle(frame, (rect_start_x, rect_start_y), (rect_start_x + rect_width, rect_start_y + rect_height), (0, 255, 0), 2)
            cv2.rectangle(frame, (altitude_rect_start_x, altitude_rect_start_y), (altitude_rect_start_x + rect_width, altitude_rect_start_y + rect_height), (255, 0, 0), 2)
            cv2.rectangle(frame, (time_rect_start_x, time_rect_start_y), (time_rect_start_x + time_rect_width, time_rect_start_y + time_rect_height), (0, 0, 255), 2)
                        
            if frame_counter % 5 == 0:

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
                
                if ret:
                    fuel_data_lox = analyzer.analyze_propellant_bar(frame, line_coordinates_lox)
                    
                    print("LOX:",fuel_data_lox)
                        
                    fuel_data_ch4 = analyzer.analyze_propellant_bar(frame, line_coordinates_ch4)
                    
                    print("CH4:",fuel_data_ch4)

                # Obtener valores detectados
                if speed_numbers:
                    speed_value = int(speed_numbers[0])  # Convertir a entero para el promedio
                    speed_buffer.append(speed_value)  # Añadir al buffer
                else:
                    speed_value = "No speed detected"
                    
                angle, roi_with_lines = detectar_angulo_nave(frame, deque(maxlen=5))
                if angle is None:    
                    angle = "No angle detected"
                    
                resultados = analizar_motores(frame)
                Starship_engine = resultados['starship']
                SuperHeavy_engine = resultados['booster']

                if altitude_numbers:
                    last_altitude_value = float(altitude_numbers[0])  # Convertir a float
                    altitude_buffer.append(last_altitude_value)  # Añadir al buffer
                else:
                    last_altitude_value = "No altitude detected"
                
                # Guardar los datos en el CSV y en el archivo Excel
                csv_writer.writerow([time_text, speed_value, last_altitude_value, angle, SuperHeavy_engine, Starship_engine, fuel_data_lox, fuel_data_ch4])
                sheet.append([time_text, speed_value, last_altitude_value, angle, SuperHeavy_engine, Starship_engine, fuel_data_lox, fuel_data_ch4])

                # Muestra los valores detectados en el frame original
                cv2.putText(frame, f"LOX", (line_coordinates_lox[0], line_coordinates_lox[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                cv2.putText(frame, f"CH4", (line_coordinates_ch4[0], line_coordinates_ch4[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
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
    workbook.save('C:/Users/mateo/Desktop/AeroTelemProc_VidData/data/telemetry_data.xlsx')