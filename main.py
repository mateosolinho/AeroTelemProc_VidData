from src.data_extraction import read_speed_and_altitude_from_video

# Insert video path
video_path = 'C:/Users/your_username/Desktop/AeroTelemProc_VidData/data/media/ift6.mp4'

# The order of the parameters is: (video_path, profile, initTime, finishTime)
read_speed_and_altitude_from_video(video_path, "SuperHeavy", "00:02:58", "00:06:55")