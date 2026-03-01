"""
Voice-Native Ambient Assistant - Backend
Handles Twilio voice calls, SMS, and web API requests via Gemini.
Includes Function Calling (Tools) for live data fetching.
"""

from flask import Flask, request, Response, jsonify
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.twiml.messaging_response import MessagingResponse
from google import genai
from google.genai import types
import os
import logging
import requests

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize Gemini client
# Ensure your environment variable is set as GEMINI_API_KEY
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

SYSTEM_PROMPT = """You are a helpful voice assistant designed for elderly users and people with limited digital literacy. 

CRITICAL RULES:
- Keep responses SHORT (2-3 sentences max for voice, 1-2 sentences for SMS).
- Speak in plain, simple, warm language. No jargon.
- Be conversational, like a kind neighbor helping out.
- You have access to tools to check the weather and bus schedules. USE THEM when asked.
- Never mention APIs, AI, tools, prompts, or technical terms.
- Always end with briefly offering to help with something else."""

# ─── AGENTIC TOOLS (FUNCTION CALLING) ──────────────────────────────────────────

def get_live_weather(location: str) -> str:
    """Gets the current real-time weather and temperature for a given city or location."""
    logger.info(f"Tool called: get_live_weather for {location}")
    try:
        # wttr.in is a free weather API that requires no authentication
        r = requests.get(f"https://wttr.in/{location}?format=%C+%t")
        if r.status_code == 200:
            return f"The current weather in {location} is {r.text.strip()}."
        return "Weather data is currently unavailable."
    except Exception as e:
        logger.error(f"Weather tool error: {e}")
        return "Weather service is down."

def get_next_bus(bus_stop_name: str) -> str:
    """Gets the arrival time of the next bus for a specific bus stop."""
    logger.info(f"Tool called: get_next_bus for {bus_stop_name}")
    # In a production app, this would query a real municipal transit API.
    # For the prototype, we return a realistic mock string.
    return f"The next bus arriving at {bus_stop_name} is the number 42. It will arrive in approximately 8 minutes."

# ─── GEMINI INTEGRATION ────────────────────────────────────────────────────────

def ask_gemini(user_text: str) -> str:
    """Send text to Gemini and allow it to use tools to formulate a response."""
    try:
        # We use the generate_content method with our python functions passed as tools
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_text,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=300,
                temperature=0.3,
                tools=[get_live_weather, get_next_bus]
            )
        )
        return response.text
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return "I'm sorry, I had a little trouble figuring that out. Could you please ask again?"

# ─── TWILIO VOICE ENDPOINTS ────────────────────────────────────────────────────

@app.route("/voice/incoming", methods=["POST"])
def voice_incoming():
    """Handle incoming phone call - greet and start listening."""
    response = VoiceResponse()
    gather = Gather(
        input="speech",
        action="/voice/respond",
        method="POST",
        timeout=5,
        speech_timeout="auto",
        language="en-US"
    )
    gather.say(
        "Hello! I'm your voice assistant. How can I help you today?",
        voice="Polly.Joanna",
        language="en-US"
    )
    response.append(gather)
    # If the user stays silent, loop back to the start
    response.redirect("/voice/incoming")
    return Response(str(response), mimetype="text/xml")


@app.route("/voice/respond", methods=["POST"])
def voice_respond():
    """Process transcribed speech input and respond via Text-to-Speech."""
    speech_result = request.form.get("SpeechResult", "")
    logger.info(f"Voice input from user: {speech_result}")

    response = VoiceResponse()

    if speech_result:
        # Send the transcribed text to Gemini
        ai_response = ask_gemini(speech_result)
        logger.info(f"Gemini response: {ai_response}")

        # Speak the answer and start listening again
        gather = Gather(
            input="speech",
            action="/voice/respond",
            method="POST",
            timeout=5,
            speech_timeout="auto"
        )
        gather.say(ai_response, voice="Polly.Joanna", language="en-US")
        response.append(gather)
        
        # Keep conversation going if they don't respond to the prompt
        response.redirect("/voice/incoming")
    else:
        response.say("I didn't quite catch that. Please try again.", voice="Polly.Joanna")
        response.redirect("/voice/incoming")

    return Response(str(response), mimetype="text/xml")


# ─── TWILIO SMS ENDPOINT ───────────────────────────────────────────────────────

@app.route("/sms/incoming", methods=["POST"])
def sms_incoming():
    """Handle incoming SMS message."""
    body = request.form.get("Body", "").strip()
    from_number = request.form.get("From", "")
    logger.info(f"SMS from {from_number}: {body}")

    response = MessagingResponse()

    if body:
        ai_response = ask_gemini(body)
        response.message(ai_response)
    else:
        response.message("Hi! Text me any question and I'll help you out.")

    return Response(str(response), mimetype="text/xml")


# ─── WEB API (For the frontend simulator) ──────────────────────────────────────

@app.route("/api/chat", methods=["POST"])
def api_chat():
    """REST API endpoint for the web simulator interface."""
    data = request.get_json()
    user_text = data.get("message", "").strip()

    if not user_text:
        return jsonify({"error": "No message provided"}), 400

    logger.info(f"Web API request: {user_text}")
    ai_response = ask_gemini(user_text)
    logger.info(f"Web API response: {ai_response}")

    return jsonify({"response": ai_response})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "Voice-Native Ambient Assistant"})

@app.route("/", methods=["GET"])
def index():
    """Serve the web simulator UI when someone visits the main link."""
    try:
        with open("simulator.html", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error loading simulator: {e}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # Run securely on 0.0.0.0 for cloud deployment
    app.run(host="0.0.0.0", port=port, debug=False)