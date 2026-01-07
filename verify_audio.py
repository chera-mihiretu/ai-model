import pyaudio
import numpy as np
import time

def test_audio():
    print("Testing Audio Output...")
    p = pyaudio.PyAudio()
    
    # List devices
    print(f"Default Output Device Info: {p.get_default_output_device_info()}")
    
    # Generate a simple beep (sine wave)
    sample_rate = 24000
    duration = 1.0 # seconds
    frequency = 440.0 # Hz (A4)
    
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    # Generate float32 audio
    audio = np.sin(frequency * t * 2 * np.pi).astype(np.float32)
    
    try:
        stream = p.open(format=pyaudio.paFloat32,
                        channels=1,
                        rate=sample_rate,
                        output=True)

        print("Playing 1 second beep...")
        stream.write(audio.tobytes())
        print("Playback finished.")
        
        stream.stop_stream()
        stream.close()
    except Exception as e:
        print(f"Failed to play audio: {e}")
        
    p.terminate()

if __name__ == "__main__":
    test_audio()
