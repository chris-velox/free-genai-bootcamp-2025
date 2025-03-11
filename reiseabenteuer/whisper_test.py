import sounddevice as sd
from whisper import load_model, transcribe
import numpy as np

# Load the Whisper model
model = load_model("tiny")

# Start transcribing
print('Ready for transcription')

while True:
    # Record audio from the microphone
    duration = 5  # seconds
    fs = 16000  # sample rate
    print("Recording...")
    myrecording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float32')
    sd.wait()  # Wait until recording is finished
    print("Finished recording")

    # Transcribe the audio data using Whisper, specifying German language
    myrecording = np.squeeze(myrecording)
    text = transcribe(model, myrecording, fp16=False, language="de")

    # Print the transcription
    print(text)
