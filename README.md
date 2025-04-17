# LinguaWave

A powerful command-line tool for translating audio files from English to other languages using state-of-the-art AI models. Perfect for content creators, educators, and anyone needing high-quality audio translations.

## Features

- 🎙️ High-quality speech-to-text using OpenAI's Whisper model
- 🌐 Accurate translation using Google Translate
- 🔊 Natural-sounding text-to-speech in multiple languages
- 📝 Handles large audio files with intelligent chunking
- 🔄 Preserves audio quality throughout the translation process
- 📊 Detailed logging for monitoring progress
- 🛠️ Flexible command-line interface

## Requirements

- Python 3.8 or higher
- FFmpeg (required for audio processing)

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Install FFmpeg:
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows (using Chocolatey)
choco install ffmpeg
```

## Usage

Basic usage:
```bash
python audio_translator.py input.wav
```

### Command-line Options

- `input_file`: Path to the input audio file (required)
- `-o, --output`: Output file path (default: 'translated_audio.mp3')
- `-l, --language`: Target language code (default: 'es' for Spanish)
- `-v, --verbose`: Enable verbose logging

### Examples

1. Basic translation to Spanish:
```bash
python audio_translator.py input.wav
```

2. Specify output file:
```bash
python audio_translator.py input.wav -o output.mp3
```

3. Translate to French:
```bash
python audio_translator.py input.wav -l fr
```

4. Enable verbose logging:
```bash
python audio_translator.py input.wav -v
```

5. Combine options:
```bash
python audio_translator.py input.wav -o output.mp3 -l es -v
```

### Supported Languages

The tool supports all languages available in Google Translate. Some common language codes:
- Spanish: `es`
- French: `fr`
- German: `de`
- Italian: `it`
- Portuguese: `pt`
- Japanese: `ja`
- Korean: `ko`
- Chinese (Simplified): `zh-CN`
- Russian: `ru`

## How It Works

1. **Transcription**: Uses OpenAI's Whisper model to convert speech to text
2. **Translation**: Translates the text using Google Translate
3. **Speech Synthesis**: Converts the translated text back to speech using Google Text-to-Speech

## Error Handling

- The tool provides detailed error messages if the input file doesn't exist
- Failed translations are logged but don't stop the process
- Temporary files are automatically cleaned up
- Progress is logged at each step

## License

MIT License - Free for personal and commercial use 