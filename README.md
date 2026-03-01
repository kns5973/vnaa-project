# Voice-Native Ambient Assistant (VNAA)
**AMD Slingshot Hackathon 2026 Submission**

VNAA is a radical accessibility tool designed to bridge the digital divide for the 2.7 billion people currently offline. It provides a "GUI-less" AI interface that functions entirely through standard cellular voice calls and SMS.

## 🚀 Key Features
- **Voice-Native Interaction**: High-fidelity STT/TTS via Twilio for natural spoken dialogue.
- **Agentic Intelligence**: Uses Google Gemini 2.5 Flash to orchestrate real-time tools (Weather, Transit).
- **Extreme Accessibility**: Zero data plan or smartphone required; works on any 2G/landline phone.
- **Hybrid Backend**: Secure Python Flask orchestration hosted on Railway.

## 🛠️ Tech Stack
- **LLM**: Google Gemini 2.5 Flash
- **Telephony**: Twilio Programmable Voice & SMS
- **Backend**: Python (Flask, Gunicorn)
- **Deployment**: Railway (Backend), Vercel (Web Simulator)

## 📖 How it Works
1. **Input**: User speaks or texts a standard phone number.
2. **Routing**: Twilio forwards the payload to our Flask webhook.
3. **Reasoning**: Gemini analyzes intent and triggers Python functions (Tools) for live data.
4. **Output**: Assistant responds with low-latency synthesized speech or SMS.