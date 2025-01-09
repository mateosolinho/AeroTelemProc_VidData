from src.data_extraction import read_speed_and_altitude_from_video

# Insertar path del video
video_path = 'C:/Users/mateo/Desktop/AeroTelemProc_VidData/data/media/ift6.mp4'
# El orden de los parametros es: (video_path, profile, initTime, finishTime)
read_speed_and_altitude_from_video(video_path, "SuperHeavy", "00:02:58", "00:06:55")