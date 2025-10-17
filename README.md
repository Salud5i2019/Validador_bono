# 🏥 Validador de Bonos Médicos con Azure OCR

Este proyecto es una API en **Python + Flask** que permite validar Bonos de Atención Médica (FONASA / ISAPRE) extrayendo información clave desde documentos PDF o imágenes utilizando **Azure OCR (Azure Cognitive Services)**.  
El sistema detecta información como:

- Número de bono
- RUN del paciente
- Prestador
- Fecha de atención
- Diagnóstico
- Código de sucursal
- Monto total

---

## ✅ Instalación rápida

### 1. Requisitos previos

| Requisito | Versión recomendada |
|------------|--------------------|
| Python     | 3.11 |
| Cuenta Azure | Requerida |
| Azure Cognitive Services | Endpoint + API Key habilitados |

---

### 2. Crear entorno virtual

```bash
py -3.11 -m venv venv
3. Activar entorno virtual (Windows)
bash
Copiar código
venv\Scripts\activate
4. Instalar dependencias
bash
Copiar código
pip install --upgrade pip
pip install -r requirements.txt
5. Configurar variables de entorno
Crear un archivo .env en la raíz del proyecto con:

ini
Copiar código
AZURE_OCR_ENDPOINT=https://<tu-endpoint>.cognitiveservices.azure.com/
AZURE_OCR_KEY=tu_api_key_de_azure
JWT_SECRET_KEY=clave_segura
🚀 Ejecutar el servicio
bash
Copiar código
python app.py
La API quedará disponible en:

arduino
Copiar código
http://localhost:5000# Validador_bono
Programa que utiliza el ocr de azure para validar informacion de bonos y texto.
