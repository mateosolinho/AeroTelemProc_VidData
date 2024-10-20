# 🚀 Rocket Telemetry Data Extraction

Welcome to the exciting world of extracting telemetry data from rocket launches. This project is a tool designed for aviation enthusiasts, space engineering fans, and programmers, aiming to capture and analyze key data from rocket launches through videos.

## 📊 What Is This?

Imagine being able to extract speed data and other metrics directly from a launch video. This program uses **OpenCV** for image manipulation and **Tesseract OCR** to convert images of text into data that you can analyze—all in real-time!

## 🔧 How It Works?

1. **Load Video**: Select the launch video you want to analyze.
2. **Processing**: The program scans the video, focusing on the region where telemetry data is expected to appear.
3. **Data Extraction**: It uses Tesseract to read the information and displays it in real-time as the video plays.

## 🌟 Key Features

- **Real-Time Extraction**: Captures and displays speed data instantly.
- **User-Friendly**: With a simple modification of the video path, you can start analyzing.
- **Intuitive Visualization**: Watch the video with overlaid data, making the analysis much more engaging.

## 🚀 Getting Started

### Requirements

- Python 3.12.5
- Dependencies:
  - OpenCV
  - Pytesseract
  - NumPy
  - Openpyxl

### Installation

To get started, clone the repository and set up your environment:

```bash
git clone https://github.com/tu_usuario/rocket-telemetry-extraction.git
cd rocket-telemetry-extraction
pip install -r requirements.txt
```

Don't forget to install Tesseract OCR [from here](https://github.com/tesseract-ocr/tesseract) and adjust the path in the code if necessary.

## Execution

Run the program as follows:

```bash
python main.py
```

Make sure the video path is correctly specified in the code, and also set the start and end times you want for your analysis.

## 🔍 Project Structure

Here’s a glimpse of how the code is organized:

```plaintext
aerotelemproc_viddata/
├── README.md                   # Project documentation
├── requirements.txt            # File that lists all project dependencies
├── main.py                     # Main code
│
├── src/                        # Project modules
│   ├── __init__.py                 # Package initialization file
│   ├── telemetry_extractor.py      # Module for telemetry data extraction
│   └── utils.py                    # Utilities module
│ 
├── data/                       # Folder containing data used in the project
│   ├── telemetry_data.csv          # CSV file with telemetry data
│   ├── telemetry_data.xlsx         # Excel file with telemetry data
│   └── media/                      # Folder for media files
│       └── files.mp4                   # Video file containing launch recordings
│ 
└── tests/                      # Folder containing project tests
    ├── __init__.py                 # Initialization file for the test package
    ├── test_utils.py               # Test file for the utilities module
    ├── test_angle_detection.py     # Test file for angle detection
    └── test_data_extraction.py     # Test file for data extraction
```

## 🙌 Contributions

Contributions are welcome! If you have an idea or improvement, feel free to contribute! Just follow these steps:

    1. Fork the repository.
    2. Create your branch (git checkout -b feature/new-feature).
    3. Make your changes.
    4. Submit a pull request.