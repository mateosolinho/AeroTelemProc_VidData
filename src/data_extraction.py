from concurrent.futures import ThreadPoolExecutor
import cv2
import csv
from openpyxl import Workbook
from collections import deque
from src.angle_detection import detect_ship_angle
from src.engine_detection import analyze_engines
from src.propellant_detection import PropellantAnalyzer
from src.utils import cleanup, extract_text, time_to_ms
import re

def read_speed_and_altitude_from_video(video_path, profile, initTime, finishTime):
    """Reads the speed and altitude from a video file and saves the data to a CSV and Excel file."""
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
        raise ValueError("Invalid profile. Choose from: SuperHeavy, StarShip, Falcon 9")
    
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

    # Separate altitude coordinates if Falcon 9
    if profile == 'Falcon9':
        altitude_rect_start_x = current_profile['altitude_rect_x']
        altitude_rect_start_y = current_profile['altitude_rect_y']
    else:
        altitude_rect_start_x = rect_start_x
        altitude_rect_start_y = rect_start_y + rect_height
        
    speed_buffer = deque(maxlen=5)  # Keeps the last 5 values
    altitude_buffer = deque(maxlen=5)  # Keeps the last 5 values

    frame_counter = 0  # Frame counter

    analyzer = PropellantAnalyzer()

    # Create a CSV file to store the data
    with open('C:/Users/your_username/Desktop/AeroTelemProc_VidData/data/telemetry_data.csv', mode='w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['Time', 'Speed', 'Altitude', 'Angle', 'SuperHeavy_Engines', 'Starship_Engines', 'LOX', 'CH4'])

        # Create a .xlsx file to store the data
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(['Time', 'Speed', 'Altitude', 'Angle', 'SuperHeavy_Engines', 'Starship_Engines', 'LOX', 'CH4'])

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # I make sure that the coordinates of the region of interest do not exceed the size of the box
            height, width, _ = frame.shape
            if (rect_start_y + rect_height) > height or (rect_start_x + rect_width) > width:
                print("The velocity region exceeds the frame size.")
                continue

            # Extract the regions where SPEED, ALTITUDE, and the time counter are located
            speed_region = frame[rect_start_y:rect_start_y + rect_height, rect_start_x:rect_start_x + rect_width]
            altitude_region = frame[altitude_rect_start_y:altitude_rect_start_y + rect_height, altitude_rect_start_x:altitude_rect_start_x + rect_width]
            time_region = frame[time_rect_start_y:time_rect_start_y + time_rect_height, time_rect_start_x:time_rect_start_x + time_rect_width]

            # Draw rectangles over the regions of interest
            cv2.rectangle(frame, (rect_start_x, rect_start_y), (rect_start_x + rect_width, rect_start_y + rect_height), (0, 255, 0), 2)
            cv2.rectangle(frame, (altitude_rect_start_x, altitude_rect_start_y), (altitude_rect_start_x + rect_width, altitude_rect_start_y + rect_height), (255, 0, 0), 2)
            cv2.rectangle(frame, (time_rect_start_x, time_rect_start_y), (time_rect_start_x + time_rect_width, time_rect_start_y + time_rect_height), (0, 0, 255), 2)
                        
            if frame_counter % 5 == 0:

                # Clean images before extracting text
                cleaned_speed_region = cleanup(speed_region)
                cleaned_altitude_region = cleanup(altitude_region)
                cleaned_time_region = cleanup(time_region)

                # Perform text extraction in parallel
                with ThreadPoolExecutor() as executor:
                    speed_future = executor.submit(extract_text, cleaned_speed_region)
                    altitude_future = executor.submit(extract_text, cleaned_altitude_region)
                    time_future = executor.submit(extract_text, cleaned_time_region)

                    speed_text = speed_future.result()
                    altitude_text = altitude_future.result()
                    time_text = time_future.result()

                # Clean the detected text and extract only the numbers
                speed_numbers = re.findall(r'\d+', speed_text.replace('"', '').replace("'", '').strip())
                altitude_numbers = re.findall(r'\d+\.?\d*', altitude_text.replace('"', '').replace("'", '').strip())
                time_text = re.sub(r'[^0-9:]', '', time_text)
                
                if ret:
                    fuel_data_lox = analyzer.analyze_propellant_bar(frame, line_coordinates_lox)
                    
                    print("LOX:",fuel_data_lox)
                        
                    fuel_data_ch4 = analyzer.analyze_propellant_bar(frame, line_coordinates_ch4)
                    
                    print("CH4:",fuel_data_ch4)

                # Get detected values
                if speed_numbers:
                    speed_value = int(speed_numbers[0])
                    speed_buffer.append(speed_value)  
                else:
                    speed_value = "No speed detected"
                    
                angle, roi_with_lines = detect_ship_angle(frame, deque(maxlen=5))
                if angle is None:    
                    angle = "No angle detected"
                    
                results = analyze_engines(frame)
                Starship_engine = results['starship']
                SuperHeavy_engine = results['booster']

                if altitude_numbers:
                    last_altitude_value = float(altitude_numbers[0]) 
                    altitude_buffer.append(last_altitude_value)
                else:
                    last_altitude_value = "No altitude detected"
                
                # Save data to CSV and Excel file
                csv_writer.writerow([time_text, speed_value, last_altitude_value, angle, SuperHeavy_engine, Starship_engine, fuel_data_lox, fuel_data_ch4])
                sheet.append([time_text, speed_value, last_altitude_value, angle, SuperHeavy_engine, Starship_engine, fuel_data_lox, fuel_data_ch4])

                # Displays the values ​​detected in the original frame
                cv2.putText(frame, f"LOX", (line_coordinates_lox[0], line_coordinates_lox[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                cv2.putText(frame, f"CH4", (line_coordinates_ch4[0], line_coordinates_ch4[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                cv2.putText(frame, f"Speed: {speed_value}", (rect_start_x, rect_start_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                cv2.putText(frame, f"Altitude: {last_altitude_value}", (altitude_rect_start_x, altitude_rect_start_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                cv2.putText(frame, f"Time: {time_text} seconds", (time_rect_start_x, time_rect_start_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            # Show the original frame with the detection
            cv2.imshow('Original Frame', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # Check to end the program
            if time_text == finishTime:
                print(f"Time reached: {time_text}. Stopping the program.")
                break  # Exit the loop
            frame_counter += 1  # Increments the frame counter

    cap.release()
    cv2.destroyAllWindows()

    # Save the .xlsx file
    workbook.save('C:/Users/your_username/Desktop/AeroTelemProc_VidData/data/telemetry_data.xlsx')