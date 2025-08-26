from flask import Blueprint, jsonify, request
from .analysis.fft import analyze_fft

api = Blueprint("api", __name__)

@api.get("/health")
def health():
    return jsonify(status="ok")

@api.post("/analyze/fft")
def analyze():
    payload = request.get_json(force=True)
    signal = payload.get("signal", [])
    fs = payload.get("fs", 250)
    result = analyze_fft(signal, fs)
    return jsonify(result)
