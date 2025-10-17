import os
import re
import fitz
import requests
from dotenv import load_dotenv

load_dotenv()
AZURE_OCR_ENDPOINT = os.getenv("AZURE_OCR_ENDPOINT")
AZURE_OCR_KEY = os.getenv("AZURE_OCR_KEY")

def log_event(text):
    with open("bitacora.txt", "a", encoding="utf-8") as f:
        f.write(text + "\n")

def pdf_to_images(pdf_path):
    doc = fitz.open(pdf_path)
    images = []
    for page_num, page in enumerate(doc):
        pix = page.get_pixmap(dpi=300)
        img_bytes = pix.tobytes("png")
        images.append(img_bytes)
        log_event(f"[INFO] Página {page_num + 1} convertida a imagen")
    return images

def extract_text_from_ocr(image_bytes):
    ocr_url = f"{AZURE_OCR_ENDPOINT}/vision/v3.2/read/analyze"
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_OCR_KEY,
        "Content-Type": "application/octet-stream"
    }
    response = requests.post(ocr_url, headers=headers, data=image_bytes)
    response.raise_for_status()
    result_url = response.headers["Operation-Location"]

    import time
    while True:
        result = requests.get(result_url, headers={"Ocp-Apim-Subscription-Key": AZURE_OCR_KEY})
        result_json = result.json()
        if result_json["status"] in ["succeeded", "failed"]:
            break
        time.sleep(1)

    text = ""
    if result_json["status"] == "succeeded":
        for read_result in result_json["analyzeResult"]["readResults"]:
            for line in read_result["lines"]:
                text += line["text"] + "\n"

    log_event("[OCR] Texto extraído OCR:")
    log_event(text)
    return text

def validar_datos(texto):
    resultados = []
    match_numero_bono = re.search(r"N[°º]\s*(\d{9})", texto)
    if match_numero_bono:
        resultados.append({
            "dato": "NUMERO BONO",
            "encontrada": True,
            "valor": match_numero_bono.group(1)
        })
    # datos fijas
    datos = [
        "FONDO NACIONAL DE SALUD",
        "BONO DE ATENCION DE SALUD",
        "77125557-4 SALUD DIGITAL SB S.A."
    ]
    for dato in datos:
        resultados.append({
            "dato": dato,
            "encontrada": dato in texto
        })

    # Campos a extraer
    match_rut = re.search(r"RUT BENEFICIARIO\s*:?\s*([0-9\-]+)", texto)
    if match_rut:
        resultados.append({
            "dato": "RUT BENEFICIARIO",
            "encontrada": True,
            "valor": match_rut.group(1)
        })

    match_nombre = re.search(r"NOMBRE REGISTRAL\s*:\s*(.+)", texto)
    if match_nombre:
        resultados.append({
            "dato": "NOMBRE REGISTRAL",
            "encontrada": True,
            "valor": match_nombre.group(1).strip()
        })

    match_codigo = re.search(r"\b(\d{7})\b", texto)
    if match_codigo:
        resultados.append({
            "dato": "CÓDIGO PRESTACIÓN",
            "encontrada": True,
            "valor": match_codigo.group(1)
        })

    match_descripcion = re.search(r"\b(\d{7})\b\s*\n([A-ZÁÉÍÓÚÑ ]{5,})", texto)
    if match_descripcion:
        resultados.append({
            "dato": "DESCRIPCIÓN PRESTACIÓN",
            "encontrada": True,
            "valor": match_descripcion.group(2).strip()
        })

    return resultados
