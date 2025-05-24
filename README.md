
# OCR y Resumen de PDF con FastAPI y Google Gemini

-----

## Descripción del Proyecto

Este proyecto es una API web construida con **FastAPI** que permite a los usuarios subir documentos PDF. La aplicación procesa estos PDFs para extraer su texto, utilizando **OCR (Optical Character Recognition)** para documentos escaneados o basados en imágenes. Una vez extraído el texto, este es enviado a la API de **Google Gemini** para generar un resumen conciso de los puntos clave del documento. La interfaz web, implementada con **Jinja2**, proporciona una manera sencilla de interactuar con la API, mostrando los resúmenes directamente en el navegador.

### Características Principales:

  * **Subida de PDF:** Interfaz web sencilla para cargar archivos PDF.
  * **Extracción de Texto (OCR):** Capacidad para extraer texto de PDFs seleccionables y aplicar OCR a PDFs escaneados o basados en imágenes (usando PyTesseract y Poppler).
  * **Resumen Inteligente:** Envía el texto extraído a Google Gemini para generar un resumen de lo más importante, comportándose como un experto analista de textos.
  * **Validaciones Robustas:** Incluye validación de tipo de archivo (solo PDF) y límite de tamaño (500 KB) para asegurar un uso eficiente.
  * **API Pura:** Mantiene un endpoint de API RESTful puro para integración con otras aplicaciones.

-----

## Requisitos del Sistema

Para que este proyecto funcione correctamente, necesitas tener instalados los siguientes componentes en tu sistema:

1.  **Python 3.8+**
2.  **Tesseract OCR:** Motor de OCR.
      * **Windows:** Descarga el instalador desde [Tesseract-OCR GitHub](https://tesseract-ocr.github.io/tessdoc/Installation.html). Asegúrate de añadirlo a tu `PATH`.
      * **Linux (Ubuntu/Debian):** `sudo apt-get install tesseract-ocr`
3.  **Poppler:** Librería para el procesamiento de PDFs (necesaria para `pdf2image`).
      * **Windows:** Descarga los binarios (ej. de [este repositorio](https://github.com/oschwartz10612/poppler-windows/releases)) y añade la ruta de la carpeta `bin` a tus variables de entorno del sistema (`PATH`).
      * **Linux (Ubuntu/Debian):** `sudo apt-get install poppler-utils`

-----

## Configuración del Entorno

Sigue estos pasos para configurar y ejecutar el proyecto:

### 1\. Clona el Repositorio

```bash
git clone <URL_DE_TU_REPOSITORIO>
cd <nombre_de_tu_repositorio>
```

### 2\. Crea y Activa un Entorno Virtual (Recomendado)

```bash
python -m venv venv
# En Windows
.\venv\Scripts\activate
# En Linux/macOS
source venv/bin/activate
```

### 3\. Instala las Dependencias de Python

```bash
pip install "fastapi[all]" python-dotenv google-generativeai pypdf pytesseract "pdf2image" jinja2
```

### 4\. Configura tus Claves API

Obtén una clave API de Google Gemini desde [Google AI Studio](https://aistudio.google.com/app/apikey).

Crea un archivo llamado `.env` en la raíz de tu proyecto (junto a `main.py`) y añade tus claves:

```env
GEMINI_API_KEY='TU_CLAVE_API_DE_GEMINI_AQUI'
IA_GENERATIVE_MODEL='gemini-pro' # Puedes usar 'gemini-1.5-pro-latest' si tienes acceso
```

**Asegúrate de no compartir tu archivo `.env` en sistemas de control de versiones como GitHub.**

### 5\. Configuración de Tesseract (Opcional)

Si Tesseract no está en tu `PATH` del sistema, puedes especificar su ubicación en `main.py` descomentando y modificando la siguiente línea:

```python
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe' # Ejemplo para Windows
```

### 6\. Estructura de Archivos

Asegúrate de que la estructura de tu proyecto sea la siguiente:

```
.
├── main.py
├── .env
└── templates/
    └── index.html
```

-----

## Uso de la Aplicación

### Iniciar la Aplicación

Para iniciar el servidor FastAPI, ejecuta el siguiente comando desde la raíz de tu proyecto:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

El flag `--reload` es útil para el desarrollo, ya que el servidor se reiniciará automáticamente con los cambios en el código.

### Acceder a la Interfaz Web

Una vez que la aplicación esté en funcionamiento, abre tu navegador web y navega a:

[http://127.0.0.1:8000/](https://www.google.com/search?q=http://127.0.0.1:8000/)

Aquí encontrarás un formulario sencillo donde podrás subir un archivo PDF (máximo 500 KB) y ver el resumen generado por Gemini directamente en la página.

### Uso de la API Pura (Opcional)

Si deseas interactuar con la API directamente (sin la interfaz web), puedes enviar solicitudes POST al siguiente endpoint:

**Endpoint:** `/api/resumen_pdf/`
**Método:** `POST`
**Content-Type:** `multipart/form-data`

Puedes probarla a través de la documentación interactiva de FastAPI en:

[http://127.0.0.1:8000/docs](https://www.google.com/search?q=http://127.0.0.1:8000/docs)

El endpoint `POST /api/resumen_pdf/` te permitirá subir un archivo y recibir una respuesta JSON con el resumen.

-----

## Errores Comunes y Solución de Problemas

  * **`TesseractNotFoundError`:** Asegúrate de que Tesseract OCR esté instalado y su ejecutable (`tesseract.exe` en Windows) esté en tu `PATH` del sistema, o especifica la ruta manualmente en `main.py`.
  * **Errores de `pdf2image` (Poppler):** Confirma que Poppler esté instalado y sus binarios accesibles desde el `PATH`.
  * **`GEMINI_API_KEY` no configurada:** Verifica que tu archivo `.env` exista, esté en la raíz del proyecto y contenga la clave `GEMINI_API_KEY` correctamente definida.
  * **Problemas con el tamaño del archivo:** Asegúrate de que los PDFs no excedan los 500 KB.

-----

## Contribución

Si deseas contribuir a este proyecto, no dudes en abrir *issues* o enviar *pull requests*.

-----

## Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo `LICENSE` para más detalles.

-----
