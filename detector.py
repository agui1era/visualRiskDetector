import os
import time
import openai
import requests
from dotenv import load_dotenv
import cv2
import datetime
import base64

# Cargar variables de entorno
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL_SECONDS", "10"))
PROMPT_SYSTEM = os.getenv("PROMPT_SYSTEM")
TRIGGER_KEYWORDS = [kw.strip().lower() for kw in os.getenv("TRIGGER_KEYWORDS", "").split(",")]
ACTIVE_HOURS_START = int(os.getenv("ACTIVE_HOURS_START", "0"))
ACTIVE_HOURS_END = int(os.getenv("ACTIVE_HOURS_END", "23"))
DIFF_THRESHOLD = float(os.getenv("DIFF_THRESHOLD", "0.03"))

last_frame = None

def is_within_active_hours():
    now = datetime.datetime.now().hour
    if ACTIVE_HOURS_START < ACTIVE_HOURS_END:
        return ACTIVE_HOURS_START <= now < ACTIVE_HOURS_END
    else:
        return now >= ACTIVE_HOURS_START or now < ACTIVE_HOURS_END

def has_significant_change(frame1, frame2, threshold=DIFF_THRESHOLD):
    if frame1 is None or frame2 is None:
        return True
    resized1 = cv2.resize(frame1, (320, 240))
    resized2 = cv2.resize(frame2, (320, 240))
    diff = cv2.absdiff(resized1, resized2)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    non_zero = cv2.countNonZero(gray)
    total_pixels = 320 * 240
    return (non_zero / total_pixels) > threshold

def encode_image_cv2(frame):
    _, buffer = cv2.imencode('.jpg', frame)
    return base64.b64encode(buffer.tobytes()).decode()

def analyze_image_with_gpt4o(encoded_image):
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": PROMPT_SYSTEM},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{encoded_image}"
                        }
                    }
                ]
            }
        ],
        max_tokens=300
    )
    return response.choices[0].message.content.strip()

def send_to_telegram(image_bytes, message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    files = {
        "photo": ("frame.jpg", image_bytes, "image/jpeg")
    }
    data = {"chat_id": TELEGRAM_CHAT_ID, "caption": message}
    response = requests.post(url, files=files, data=data)
    return response.ok

def save_last_detected_frame(frame, path="frames_detected/last_frame.jpg"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cv2.imwrite(path, frame)
    print(f"💾 Último frame con cambio guardado en: {path}")

def monitoring_loop():
    global last_frame
    print(f"📸 Monitoreando webcam cada {CHECK_INTERVAL}s (umbral: {DIFF_THRESHOLD*100:.1f}%)...\n")
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("❌ No se pudo acceder a la cámara.")
        return

    while True:
        if not is_within_active_hours():
            print(f"⏰ Fuera de horario activo ({ACTIVE_HOURS_START}:00–{ACTIVE_HOURS_END}:00). Esperando...")
            time.sleep(CHECK_INTERVAL)
            continue

        ret, frame = cap.read()
        if not ret:
            print("⚠️ No se pudo capturar imagen.")
            time.sleep(CHECK_INTERVAL)
            continue

        if has_significant_change(last_frame, frame):
            save_last_detected_frame(frame)  # Guardar última con cambio
            try:
                encoded = encode_image_cv2(frame)
                result = analyze_image_with_gpt4o(encoded)
                print(f"🧠 [{time.ctime()}] Resultado:\n{result}\n")

                if any(k in result.lower() for k in TRIGGER_KEYWORDS):
                    _, jpeg_buffer = cv2.imencode('.jpg', frame)
                    success = send_to_telegram(jpeg_buffer.tobytes(), result)
                    print("📤 Alerta enviada." if success else "⚠️ Fallo al enviar a Telegram.")
            except Exception as e:
                print(f"❌ Error de análisis: {e}")
        else:
            print("🔍 Sin cambios significativos. No se envía.")

        last_frame = frame.copy()
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    monitoring_loop()
