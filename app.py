import os
import json
import base64
import traceback
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from sarvamai import SarvamAI

from flask_cors import CORS






# -----------------------------------
# Load ENV
# -----------------------------------
load_dotenv()

app = Flask(__name__)
CORS(
    app,
    origins=[
        "http://localhost:3000",
        "https://pfanewfrontend-abhhaegyfrdvfdd2.centralindia-01.azurewebsites.net",
        "https://nwrwhatsapp-ekhmbrcqhfdgd0cv.centralindia-01.azurewebsites.net"
        
    ]
)

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")

if not SARVAM_API_KEY:
    print("❌ SARVAM_API_KEY missing")



@app.route("/", methods=["GET"])
def send_response():
    return "Connection Successful",200





#get-chatbot-response
def get_ai_response(query, thread_id="default", page_name="pfa"):
    url = f"https://backendnwr.azurewebsites.net/api/get-final-result"
    params = {"pageName": page_name}
    payload = {
        "query": query,
    }
    if thread_id and thread_id != "default":
        payload["threadId"] = thread_id
        
    return requests.post(url, params=params, json=payload)


# -----------------------------------
# Batch Transcription Function (REST)
# -----------------------------------
def transcribe_audio_batch(audio_base64: str):

    url = "https://api.sarvam.ai/speech-to-text"

    headers = {
        "api-subscription-key": SARVAM_API_KEY
    }

    # Convert base64 back to binary
    audio_bytes = base64.b64decode(audio_base64)

    files = {
        "file": ("audio.ogg", audio_bytes, "audio/ogg")
    }

    data = {
        "model": "saaras:v3",
        "language_code": "en-IN"
    }

    response = requests.post(
        url,
        headers=headers,
        files=files,
        data=data
    )

    print("Sarvam response:", response.text)

    if response.status_code != 200:
        raise Exception(response.text)

    result = response.json()

    return result.get("transcript", "")

#text to speech conversion
def text_to_speech_sarvam(text: str) -> str:
    client = SarvamAI(
        api_subscription_key=SARVAM_API_KEY,
    )

    response = client.text_to_speech.convert(
        text=text,
        target_language_code="hi-IN",
        speaker="shubh",
        pace=1.1,
        speech_sample_rate=22050,
        enable_preprocessing=True,
        model="bulbul:v3"
    )

    # Extract base64 audio from response
    if not response.audios:
        raise Exception("No audio returned from Sarvam")

    return response.audios[0]   # Already base64



@app.route("/whatsapp", methods=["POST"])
def whatsapp_transcribe():
    print("request received")

    try:
        data = request.get_json()
        # print("data:",data)

        if not data or "audio_base64" not in data:
            return jsonify({"error": "Missing 'audio_base64' field"}), 400

        audio_base64file = data["audio_base64"]
        print("preview:", audio_base64file[:10])
        request_source=data["request_source"] or "whatsapp"

        # Validate base64
        base64.b64decode(audio_base64file, validate=True)

        transcript = transcribe_audio_batch(audio_base64file)

        print("transcript:", transcript)
        # if "create task" in transcript.lower():
        #     return jsonify({
        #         "status": "success",
        #         "transcript": transcript
        #     })
        # chat_response=get_ai_response(transcript)
        # response_json=chat_response.json()
        # saar_response=response_json["data"]["reply"]
        # print("chat_response:", saar_response)

        # if request_source == "portal":
        #     audio_bytes = text_to_speech_sarvam(saar_response)
            # audio_json = json.loads(audio_bytes)
            # print("audio_bytes:", audio_json["audios"])

            #audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
            # print("audio_base64:", audio_bytes[:10])
            # return jsonify({
            #     "status": "success",
            #     "transcript": saar_response,
            #     "audio_base64": audio_bytes
            # })


        return jsonify({
            "status": "success",
            "transcript": transcript
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500



# -----------------------------------
# API Endpoint
# -----------------------------------
@app.route("/transcribe", methods=["POST"])
def transcribe():
    print("request received")

    try:
        data = request.get_json()
        # print("data:",data)

        if not data or "audio_base64" not in data:
            return jsonify({"error": "Missing 'audio_base64' field"}), 400

        audio_base64file = data["audio_base64"]
        print("preview:", audio_base64file[:10])
        request_source=data["request_source"] or "whatsapp"

        # Validate base64
        base64.b64decode(audio_base64file, validate=True)

        transcript = transcribe_audio_batch(audio_base64file)

        print("transcript:", transcript)
        if "create task" in transcript.lower():
            return jsonify({
                "status": "success",
                "transcript": transcript
            })
        chat_response=get_ai_response(transcript)
        response_json=chat_response.json()
        saar_response=response_json["data"]["reply"]
        print("chat_response:", saar_response)

        if request_source == "portal":
            audio_bytes = text_to_speech_sarvam(saar_response)
            # audio_json = json.loads(audio_bytes)
            # print("audio_bytes:", audio_json["audios"])

            #audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
            print("audio_base64:", audio_bytes[:10])
            return jsonify({
                "status": "success",
                "transcript": saar_response,
                "audio_base64": audio_bytes
            })


        return jsonify({
            "status": "success",
            "transcript": saar_response
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/health")
def health():
    return jsonify({"status": "running"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
