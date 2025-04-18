# riskOldPersonDetector# 🔍 Real-Time Visual Risk Detection with GPT-4o

A lightweight AI-powered surveillance prototype that uses OpenAI's GPT-4o to semantically analyze camera snapshots for risky or dangerous situations. Ideal for elderly care, home security, and proactive monitoring.

---

## 🚀 What It Does

- 📸 Receives a static image (replaced externally every 10 minutes)
- 🧠 Uses GPT-4o to interpret visual context (e.g., fall, smoke, strange behavior)
- ⚠️ Sends risk summaries to Telegram
- 🛠️ Easily configurable via `.env` file

---

## 💡 Use Case

**Elderly monitoring:** Detect if an elderly person has fallen, remains inactive for a long period, or if something unusual is happening in the room (e.g., another person enters, visible injury, abnormal posture).

---

## 🧠 Why GPT-4o?

Unlike traditional object detection models, GPT-4o understands *context* and *semantics*. It can reason about what it sees, which allows it to:
- Identify dangerous situations
- Understand behaviors, not just objects
- Provide human-like explanations in plain text

---

## ⚙️ Setup

### 1. Clone repo and create virtual env

```bash
python3 -m venv analizador_env
source analizador_env/bin/activate
pip install -r requirements.txt
