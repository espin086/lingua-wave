# Audio Translation Tool

This tool transcribes English audio to text, translates it to Spanish, and converts it back to speech.

## Requirements

- Python 3.8 or higher
- FFmpeg (required for audio processing)

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Install FFmpeg:
- On macOS:
```bash
brew install ffmpeg
```

## Usage

1. Place your audio file in the same directory as the script
2. Run the script:
```bash
python audio_translator.py
```

The script will:
1. Transcribe the audio using OpenAI's Whisper model
2. Translate the text to Spanish using Google Translate
3. Convert the translated text to speech using Google Text-to-Speech
4. Save the output as `translated_audio.mp3` in the same directory

## Output

The translated audio will be saved as `translated_audio.mp3` in the same directory as the script.

## Notes

- The script uses high-quality models for both transcription and text-to-speech
- The translation is done using Google Translate
- The output audio will be in Spanish with natural-sounding speech 