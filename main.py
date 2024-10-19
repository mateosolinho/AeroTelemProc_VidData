from src.data_extraction import read_speed_and_altitude_from_video

video_path = 'C:/Users/mateo/Desktop/AeroTelemProc_VidData/data/media/ift5.mp4'
read_speed_and_altitude_from_video(video_path, "StarShip", "00:00", "01:05:50")