import time
import requests
import sounddevice as sd
from scipy.io.wavfile import write
import speech_recognition as sr
import webbrowser

# Settings
SAMPLE_RATE = 44100
RECORD_SECONDS = 4
TEMP_AUDIO = "live_audio.wav"

def get_location():
    """Fetches real-time GPS coordinates via free IP-API."""
    try:
        res = requests.get("http://ip-api.com/json/", timeout=5).json()
        if res.get("status") == "success":
            return res.get("lat"), res.get("lon"), res.get("city"), res.get("regionName")
    except Exception as err:
        print(f"Error fetching IP location: {err}")
    # Default fallback coordinates
    return 13.0827, 80.2707, "Chennai", "Tamil Nadu"

def find_nearest_police_station(lat, lon):
    """Searches OpenStreetMap Overpass for the closest police station within 10 km."""
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json];
    node["amenity"="police"](around:10000,{lat},{lon});
    out 1;
    """
    try:
        response = requests.post(overpass_url, data={"data": query}, timeout=8)
        data = response.json()
        if data.get("elements"):
            police = data["elements"][0]
            tags = police.get("tags", {})
            name = tags.get("name", "Nearest Police Station")
            phone = tags.get("phone", tags.get("contact:phone", "112 / 100"))
            return name, phone, police.get("lat"), police.get("lon")
    except Exception as err:
        print(f"Overpass API error: {err}")
    return "Local Police Station", "112", lat, lon

def trigger_emergency_protocol(lat, lon, city, station_name, station_phone):
    """Executes the alert protocol: opens map and displays alert details."""
    print("\n" + "="*50)
    print("🚨 EMERGENCY ALERT TRIGGERED! 🚨")
    print(f"📍 Location: {city} ({lat}, {lon})")
    print(f"👮 Target Station: {station_name}")
    print(f"📞 Contact Line: {station_phone}")
    print("="*50 + "\n")
    
    # Opens direct directions to the police station in the default web browser
    maps_url = f"https://www.google.com/maps/dir/?api=1&destination={station_name}+{city}"
    print(f"Opening navigation to station: {maps_url}")
    webbrowser.open(maps_url)

def record_audio_chunk():
    """Records audio using sounddevice (no PyAudio needed)."""
    recording = sd.rec(int(RECORD_SECONDS * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='int16')
    sd.wait()
    write(TEMP_AUDIO, SAMPLE_RATE, recording)

def main():
    recognizer = sr.Recognizer()
    print("="*50)
    print("🟢 Emergency Monitor Active.")
    print("Say: 'emergency', 'help me', 'danger', or 'police'")
    print("Press Ctrl + C in terminal to stop.")
    print("="*50)

    trigger_keywords = ["emergency", "help", "danger", "police", "save me"]

    while True:
        try:
            print("\nListening...", end="", flush=True)
            record_audio_chunk()

            with sr.AudioFile(TEMP_AUDIO) as source:
                audio = recognizer.record(source)

            try:
                text = recognizer.recognize_google(audio).lower()
                print(f" Heard: '{text}'")

                if any(word in text for word in trigger_keywords):
                    print("⚠️ Emergency keyword recognized!")
                    lat, lon, city, region = get_location()
                    station_name, phone, p_lat, p_lon = find_nearest_police_station(lat, lon)
                    trigger_emergency_protocol(lat, lon, city, station_name, phone)
                    break
            except sr.UnknownValueError:
                print(" [No clear speech]")
            except sr.RequestError as e:
                print(f" Recognition error: {e}")

        except KeyboardInterrupt:
            print("\nMonitoring stopped by user.")
            break

if __name__ == "__main__":
    main()