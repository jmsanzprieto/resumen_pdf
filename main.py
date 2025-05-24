import os
import io
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from PIL import Image
import pytesseract
from pypdf import PdfReader
from dotenv import load_dotenv
import google.generativeai as genai
# No se usa directamente en este contexto, pero se mantiene si es necesario para otros fines
from datetime import datetime
import sys

# Importar convert_from_bytes para el procesamiento de PDF a imagen
try:
    from pdf2image import convert_from_bytes
except ImportError:
    print("Error: La librería 'pdf2image' no está instalada. Por favor, instálala con: pip install pdf2image")
    print("Además, asegúrate de tener Poppler instalado en tu sistema y su ruta añadida a las variables de entorno.")
    sys.exit(1)


# --- Cargar variables de entorno ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
IA_GENERATIVE_MODEL = os.getenv("IA_GENERATIVE_MODEL")


# --- Configuración de la API de Gemini ---
if not GEMINI_API_KEY:
    print("Error: La variable de entorno GEMINI_API_KEY no está configurada.")
    print("Por favor, asegúrate de tener un archivo .env con GEMINI_API_KEY='TU_API_KEY'.")
    sys.exit(1)
genai.configure(api_key=GEMINI_API_KEY)


# --- Configuración del motor Tesseract OCR (si no está en el PATH) ---
# Si Tesseract está en una ubicación no estándar, descomenta y actualiza la siguiente línea
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe' # Ejemplo para Windows

app = FastAPI(
    title="OCR API con FastAPI y Resumen con Gemini",
    description="API para subir documentos PDF, extraer su texto mediante OCR y generar un resumen con Google Gemini.",
    version="1.0.0",
)

# --- Configuración de Jinja2Templates ---
templates = Jinja2Templates(directory="templates")

# --- Modelo de Gemini a utilizar ---
# Usamos la variable de entorno para el modelo
GEMINI_MODEL = IA_GENERATIVE_MODEL if IA_GENERATIVE_MODEL else "gemini-pro" # Fallback por si no se define en .env

# --- Límites de tamaño del archivo ---
MAX_FILE_SIZE_BYTES = 500 * 1024  # 500 KB

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Muestra la página principal con el formulario de subida de PDF.
    """
    return templates.TemplateResponse("index.html", {"request": request, "summary": None, "error_message": None})


@app.post("/resumen_pdf/", response_class=HTMLResponse)
async def resumen_pdf_web(request: Request, file: UploadFile = File(...)):
    """
    Sube un documento PDF, realiza validaciones, extrae su texto, y genera un resumen con Gemini.
    Luego, renderiza la misma página con el resumen o un mensaje de error.
    """
    error_message = None
    summary = None

    # --- 1. Validación de Tipo de Archivo ---
    if file.content_type != "application/pdf":
        error_message = "El archivo debe ser un PDF."
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "summary": summary, "error_message": error_message}
        )

    # --- 2. Validación de Tamaño de Archivo ---
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        error_message = f"El tamaño del archivo excede el límite de {MAX_FILE_SIZE_BYTES / 1024:.0f} KB."
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "summary": summary, "error_message": error_message}
        )

    # Rebobinar el stream después de leerlo para que las funciones lo puedan leer de nuevo
    file_stream = io.BytesIO(file_bytes)

    try:
        reader = PdfReader(file_stream)
        extracted_text = ""
        is_scanned_pdf = False

        # Intentar extraer texto directamente primero
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            page_text = page.extract_text()
            if page_text:
                extracted_text += f"--- Página {page_num + 1} (Texto Seleccionable) ---\n"
                extracted_text += page_text + "\n\n"
            else:
                is_scanned_pdf = True # Si alguna página no tiene texto, asumimos que es un PDF escaneado

        # Si el PDF es escaneado o tiene páginas sin texto, aplicar OCR
        if is_scanned_pdf or not extracted_text.strip():
            # Si ya se extrajo texto seleccionable, lo mantenemos y solo aplicamos OCR a las páginas sin texto.
            # Si todo el PDF es escaneado o no tenía texto, reiniciamos.
            if not extracted_text.strip():
                extracted_text = ""

            # Convertir cada página del PDF en una imagen
            # Es importante pasar file_bytes (bytes originales) a convert_from_bytes
            images = convert_from_bytes(file_bytes, dpi=300)

            for i, image in enumerate(images):
                try:
                    text_from_image = pytesseract.image_to_string(image, lang='spa+eng')
                    extracted_text += f"--- Página {i+1} (OCR) ---\n"
                    extracted_text += text_from_image + "\n\n"
                except Exception as e:
                    print(f"Error al procesar la página {i+1} con OCR: {e}")
                    extracted_text += f"--- Error al procesar la página {i+1} ---\n\n"

        if not extracted_text.strip():
            error_message = "No se pudo extraer texto del documento."
            return templates.TemplateResponse(
                "index.html",
                {"request": request, "summary": summary, "error_message": error_message}
            )

        # --- Enviar el texto a Gemini para generar el resumen ---
        try:
            model = genai.GenerativeModel(GEMINI_MODEL)
            prompt = (
                "Eres un experto analista de textos con una capacidad excepcional para identificar la información más relevante. "
                "Tu tarea es leer el siguiente documento y proporcionar un resumen conciso y claro de los puntos clave y lo más importante. "
                "Asegúrate de que el resumen capture la esencia del contenido, eliminando redundancias y centrándote en los datos cruciales. "
                "Aquí está el texto del documento:\n\n"
                f"{extracted_text}\n\n"
                "Por favor, genera el resumen:"
            )
            response = await model.generate_content_async(prompt)
            summary = response.text

            return templates.TemplateResponse(
                "index.html",
                {"request": request, "summary": summary, "error_message": None}
            )

        except Exception as e:
            error_message = f"Error al comunicarse con la API de Gemini: {str(e)}"
            return templates.TemplateResponse(
                "index.html",
                {"request": request, "summary": summary, "error_message": error_message}
            )

    except pytesseract.TesseractNotFoundError:
        error_message = "El motor Tesseract OCR no está instalado o no se encontró en el PATH. Por favor, instálalo."
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "summary": summary, "error_message": error_message}
        )
    except Exception as e:
        error_message = f"Error interno del servidor al procesar el PDF: {str(e)}"
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "summary": summary, "error_message": error_message}
        )

# Este es el endpoint API puro que tenías, modificado para usar las nuevas variables
@app.post("/api/resumen_pdf/", response_class=JSONResponse)
async def resumen_pdf_api(file: UploadFile = File(...)):
    """
    (Endpoint API puro) Sube un documento PDF, extrae su texto usando OCR y envía el texto a Google Gemini
    para generar un resumen de lo más importante.
    La IA se comporta como un experto en analizar textos.
    Incluye validación de tipo y tamaño de archivo.
    """
    # --- 1. Validación de Tipo de Archivo ---
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="El archivo debe ser un PDF.")

    # --- 2. Validación de Tamaño de Archivo ---
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail=f"El tamaño del archivo excede el límite de {MAX_FILE_SIZE_BYTES / 1024:.0f} KB.")

    # Rebobinar el stream después de leerlo para la validación de tamaño
    pdf_stream = io.BytesIO(file_bytes)

    try:
        reader = PdfReader(pdf_stream)
        extracted_text = ""
        is_scanned_pdf = False

        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            page_text = page.extract_text()
            if page_text:
                extracted_text += f"--- Página {page_num + 1} (Texto Seleccionable) ---\n"
                extracted_text += page_text + "\n\n"
            else:
                is_scanned_pdf = True

        if is_scanned_pdf or not extracted_text.strip():
            if not extracted_text.strip():
                extracted_text = ""
            images = convert_from_bytes(file_bytes, dpi=300) # Usar file_bytes original
            for i, image in enumerate(images):
                try:
                    text_from_image = pytesseract.image_to_string(image, lang='spa+eng')
                    extracted_text += f"--- Página {i+1} (OCR) ---\n"
                    extracted_text += text_from_image + "\n\n"
                except Exception as e:
                    print(f"Error al procesar la página {i+1} con OCR: {e}")
                    extracted_text += f"--- Error al procesar la página {i+1} ---\n\n"

        if not extracted_text.strip():
            raise HTTPException(status_code=500, detail="No se pudo extraer texto del documento.")

        try:
            model = genai.GenerativeModel(GEMINI_MODEL)
            prompt = (
                "Eres un experto analista de textos con una capacidad excepcional para identificar la información más relevante. "
                "Tu tarea es leer el siguiente documento y proporcionar un resumen conciso y claro de los puntos clave y lo más importante. "
                "Asegúrate de que el resumen capture la esencia del contenido, eliminando redundancias y centrándote en los datos cruciales. "
                "Aquí está el texto del documento:\n\n"
                f"{extracted_text}\n\n"
                "Por favor, genera el resumen:"
            )
            response = await model.generate_content_async(prompt)
            summary = response.text

            return JSONResponse(
                status_code=200,
                content={
                    "filename": file.filename,
                    "extracted_text_length": len(extracted_text),
                    "summary": summary
                }
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al comunicarse con la API de Gemini: {str(e)}")

    except pytesseract.TesseractNotFoundError:
        raise HTTPException(status_code=500, detail="El motor Tesseract OCR no está instalado o no se encontró en el PATH. Por favor, instálalo.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)