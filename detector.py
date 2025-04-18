import os
import time
import openai
import requests
from dotenv import load_dotenv
from PIL import Image
import io
import base64

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL_SECONDS", "600"))  # Default: 10 min
IMAGE_PATH = os.getenv("IMAGE_PATH", "images/frame.jpg")

def encode_image(path):
    with Image.open(path) as img:
        buffer = io.BytesIO()
        img.convert("RGB").save(buffer, format="JPEG")
        return base64.b64encode(buffer.getvalue()).decode()

def analyze_image_with_gpt4o(encoded_image):
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a visual safety monitoring system. Analyze the image and summarize any risky situations, "
                        "such as falls, fights, intruders, unusual posture, or suspicious behavior. Respond concisely without listing examples."
                    )
                },
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
    except Exception as e:
        return f"[❌ Error during analysis: {e}]"

def send_to_telegram(image_path, message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(image_path, 'rb') as photo:
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "caption": message
        }
        files = {"photo": photo}
        response = requests.post(url, data=data, files=files)
    return response.ok

def monitoring_loop():
    print(f"🔁 Starting monitoring of '{IMAGE_PATH}' every {CHECK_INTERVAL} seconds...\n")
    while True:
        if os.path.exists(IMAGE_PATH):
            try:
                encoded = encode_image(IMAGE_PATH)
                result = analyze_image_with_gpt4o(encoded)
                print(f"🧠 [{time.ctime()}] Result:\n{result}\n")

                # Basic trigger keywords
                if any(keyword in result.lower() for keyword in [
                    "fall", "intruder", "fight", "unusual", "risk", "suspicious"
                ]):
                    success = send_to_telegram(IMAGE_PATH, result)
                    print("📤 Alert sent to Telegram." if success else "⚠️ Failed to send alert.")
            except Exception as e:
                print(f"❌ Error processing image: {e}")
        else:
            print("❗ Image not found.")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    monitoring_loop()
