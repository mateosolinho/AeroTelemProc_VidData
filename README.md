# 🚀 Rocket Telemetry Data Extraction

Bienvenido al emocionante mundo de la extracción de datos de telemetría de lanzamientos de cohetes. Este proyecto es una herramienta diseñada para los entusiastas de la aviación, la ingeniería espacial y la programación, que busca capturar y analizar datos clave de lanzamientos de cohetes a través de videos.

## 📊 ¿Qué es esto?

Imagina poder extraer datos de velocidad y otras métricas directamente de un video de lanzamiento. Este programa utiliza **OpenCV** para la manipulación de imágenes y **Tesseract OCR** para convertir imágenes de texto en datos que puedes analizar. ¡Todo en tiempo real!

## 🔧 ¿Cómo Funciona?

1. **Carga de Video**: Selecciona el video del lanzamiento que deseas analizar.
2. **Procesamiento**: El programa escanea el video, enfocado en la región donde se espera que aparezcan los datos de telemetría.
3. **Extracción de Datos**: Utiliza Tesseract para leer la información y la muestra en tiempo real mientras el video se reproduce.

## 🌟 Características Clave

- **Extracción en Tiempo Real**: Captura y muestra datos de velocidad al instante.
- **Fácil de Usar**: Con una simple modificación de la ruta del video, puedes comenzar a analizar.
- **Visualización Intuitiva**: Ve el video con los datos superpuestos, haciendo que el análisis sea mucho más atractivo.

## 🚀 ¿Cómo Empezar?

### Requisitos

- Python 3.12.5
- Dependencias:
  - OpenCV
  - Pytesseract
  - NumPy
  - Openpyxl

### Instalación

Para comenzar, clona el repositorio y configura tu entorno:

```bash
git clone https://github.com/tu_usuario/rocket-telemetry-extraction.git
cd rocket-telemetry-extraction
pip install -r requirements.txt
```

No olvides instalar Tesseract OCR [desde aquí](https://github.com/tesseract-ocr/tesseract) y ajustar la ruta en el código si es necesario.

## Ejecución

Ejecuta el programa de la siguiente manera:

```bash
python main.py
```

Asegúrate de que la ruta del video esté correctamente especificada en el código, además de colocar bien el tiempo de comienzo y final que desees en tu análisis

## 🔍 Estructura del Proyecto

Aquí tienes un vistazo a cómo está organizado el código:

```plaintext
aerotelemproc_viddata/
├── README.md                   # Documentación del proyecto
├── requirements.txt            # Archivo que lista todas las dependencias del proyecto
├── main.py                     # Código principal
│
├── src/                        # Módulos del proyecto
│   ├── __init__.py                 # Archivo de inicialización del paquete
│   ├── telemetry_extractor.py      # Módulo para la extracción de datos de telemetría
│   └── utils.py                    # Módulo de utilidades
│ 
├── data/                       # Carpeta que contiene los datos utilizados en el proyecto
│   ├── telemetry_data.csv          # Archivo CSV con datos de telemetría
│   ├── telemetry_data.xlsx         # Archivo Excel con datos de telemetría
│   └── media/                      # Carpeta para archivos multimedia
│       └── files.mp4                   # Archivo de vídeo que contiene las grabaciones de lanzamiento
│ 
└── tests/                      # Carpeta que contiene las pruebas del proyecto
    ├── __init__.py                 # Archivo de inicialización del paquete de pruebas
    ├── test_utils.py               # Archivo de pruebas para el módulo de utilidades
    ├── test_angle_detection.py     # Archivo de pruebas para la detección de ángulos
    └── test_data_extraction.py     # Archivo de pruebas para la extracción de datos
```

## 🙌 Contribuciones

Las contribuciones son bienvenidas. Si tienes una idea o mejora, ¡no dudes en contribuir! Simplemente sigue estos pasos:

    1. Haz un fork del repositorio.
    2. Crea tu rama (git checkout -b feature/nueva-caracteristica).
    3. Realiza tus cambios.
    4. Envía un pull request.