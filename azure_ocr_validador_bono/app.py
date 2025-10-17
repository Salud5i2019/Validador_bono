import os
import jwt
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from utils import pdf_to_images, extract_text_from_ocr, validar_datos, log_event
from io import BytesIO
import fitz
import datetime
from dotenv import dotenv_values
import base64
import binascii

load_dotenv()
config = dotenv_values()
os.environ.update(config) 
app = Flask(__name__)
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
API_USER = os.getenv("API_USER")
API_PASSWORD = os.getenv("API_PASSWORD")

@app.route("/token", methods=["POST"])
def generar_token():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if username != API_USER or password != API_PASSWORD:
        return jsonify({"error": "Credenciales inválidas"}), 401

    # Token válido por 1 día
    expiration = datetime.datetime.utcnow() + datetime.timedelta(days=1)
    payload = {
        "user": username,
        "exp": expiration
    }

    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")
    return jsonify({"token": token}), 200

@app.route("/validar-bono", methods=["POST"])
def validar_bono():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    try:
        jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        return jsonify({"error": "Token inválido o no enviado"}), 403

    if "file" not in request.files:
        return jsonify({"error": "Archivo no enviado"}), 400

    file = request.files["file"]
    filename = file.filename.lower()
    file_bytes = file.read()
    log_event(f"[INFO] Archivo recibido: {filename}")

    imagenes = []

    # Procesar PDF o imagen en memoria
    if filename.endswith(".pdf"):
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        for page_num, page in enumerate(doc):
            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes("png")
            imagenes.append(img_bytes)
            log_event(f"[INFO] Página {page_num + 1} convertida a imagen (en memoria)")
    elif filename.endswith((".png", ".jpg", ".jpeg")):
        imagenes = [file_bytes]
        log_event("[INFO] Imagen cargada directamente en memoria")
    else:
        return jsonify({"error": "Formato de archivo no soportado"}), 400

    # OCR y extracción de líneas
    lineas_totales = []
    for imagen in imagenes:
        texto_extraido = extract_text_from_ocr(imagen)
        lineas_totales.extend(texto_extraido.splitlines())

    texto_concatenado = "\n".join(lineas_totales)
    frases_validadas = validar_datos(texto_concatenado)

    respuesta = {
        # "mensaje": "lectura bono completa",
        "texto_extraido": lineas_totales,
        "data_encontrada": frases_validadas
    }

    log_event("[FIN] Respuesta enviada al cliente")
    return jsonify(respuesta), 200

@app.route("/validar-bono-base64", methods=["POST"])
def validar_bono_base64():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    try:
        jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        return jsonify({"error": "Token inválido o no enviado"}), 403

    data = request.get_json()
    base64_file = data.get("archivo_base64")

    if not base64_file:
        return jsonify({"error": "Falta el archivo base64"}), 400

    try:
        if base64_file.startswith("data:"):
            base64_file = base64_file.split(",")[1]
        file_bytes = base64.b64decode(base64_file)
    except binascii.Error:
        return jsonify({"error": "Base64 inválido. No se pudo decodificar."}), 400

    # Detectar tipo por firma mágica
    if file_bytes.startswith(b"%PDF"):
        tipo = "pdf"
    elif file_bytes.startswith(b"\x89PNG"):
        tipo = "png"
    elif file_bytes.startswith(b"\xff\xd8"):
        tipo = "jpg"
    else:
        return jsonify({"error": "Tipo de archivo no reconocido o no soportado"}), 400

    imagenes = []

    # Procesamiento según tipo
    if tipo == "pdf":
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            for page_num, page in enumerate(doc):
                pix = page.get_pixmap(dpi=300)
                img_bytes = pix.tobytes("png")
                imagenes.append(img_bytes)
                log_event(f"[INFO] Página {page_num + 1} convertida desde PDF base64")
        except Exception as e:
            return jsonify({"error": f"No se pudo procesar el PDF: {str(e)}"}), 400
    else:
        imagenes = [file_bytes]
        log_event("[INFO] Imagen base64 procesada directamente")

    # OCR + Validación
    lineas_totales = []
    for imagen in imagenes:
        texto_extraido = extract_text_from_ocr(imagen)
        lineas_totales.extend(texto_extraido.splitlines())

    texto_concatenado = "\n".join(lineas_totales)
    frases_validadas = validar_datos(texto_concatenado)

    return jsonify({
        "texto_extraido": lineas_totales,
        "data_encontrada": frases_validadas
    }), 200


if __name__ == "__main__":
    app.run(debug=True)
