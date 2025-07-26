import os
import tempfile
import logging
from pathlib import Path
from typing import Optional
import asyncio
import aiofiles
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
import whisper
from deep_translator import GoogleTranslator
from gtts import gTTS
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="LinguaWave API",
    description="A powerful API for translating audio files using AI models",
    version="1.0.0"
)

# Global Whisper model (loaded once at startup)
whisper_model = None

# Pydantic models
class TranslationResponse(BaseModel):
    original_text: str
    translated_text: str
    target_language: str
    message: str

class HealthResponse(BaseModel):
    status: str
    message: str

@app.on_event("startup")
async def startup_event():
    """Load Whisper model on startup"""
    global whisper_model
    logger.info("Loading Whisper model...")
    whisper_model = whisper.load_model("base")
    logger.info("Whisper model loaded successfully")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="healthy", message="LinguaWave API is running")

@app.post("/translate-audio", response_model=TranslationResponse)
async def translate_audio_endpoint(
    file: UploadFile = File(..., description="Audio file to translate"),
    target_language: str = Form(default="es", description="Target language code")
):
    """
    Translate audio file to target language.
    
    Returns the transcribed and translated text.
    """
    # Validate file type (more permissive validation)
    logger.info(f"Received file: {file.filename}, content_type: {file.content_type}")
    allowed_extensions = ['.wav', '.mp3', '.aiff', '.flac', '.ogg', '.m4a', '.mp4']
    file_extension = Path(file.filename).suffix.lower()
    if not file.content_type or (not file.content_type.startswith('audio/') and file_extension not in allowed_extensions):
        raise HTTPException(status_code=400, detail=f"File must be an audio file. Received: {file.content_type}, Extension: {file_extension}")
    
    # Create temporary file for uploaded audio
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_audio:
        try:
            # Save uploaded file
            contents = await file.read()
            temp_audio.write(contents)
            temp_audio.flush()
            
            # Transcribe audio
            logger.info(f"Transcribing audio file: {file.filename}")
            transcribed_text = await transcribe_audio_async(temp_audio.name)
            
            # Translate text
            logger.info(f"Translating to language: {target_language}")
            translated_text = await translate_text_async(transcribed_text, target_language)
            
            return TranslationResponse(
                original_text=transcribed_text,
                translated_text=translated_text,
                target_language=target_language,
                message="Translation completed successfully"
            )
            
        except Exception as e:
            logger.error(f"Error processing audio: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_audio.name):
                os.unlink(temp_audio.name)

@app.post("/translate-and-synthesize")
async def translate_and_synthesize_endpoint(
    file: UploadFile = File(..., description="Audio file to translate"),
    target_language: str = Form(default="es", description="Target language code")
):
    """
    Translate audio file and return translated audio.
    
    Returns the translated audio file.
    """
    # Validate file type (more permissive validation)
    logger.info(f"Received file: {file.filename}, content_type: {file.content_type}")
    allowed_extensions = ['.wav', '.mp3', '.aiff', '.flac', '.ogg', '.m4a', '.mp4']
    file_extension = Path(file.filename).suffix.lower()
    if not file.content_type or (not file.content_type.startswith('audio/') and file_extension not in allowed_extensions):
        raise HTTPException(status_code=400, detail=f"File must be an audio file. Received: {file.content_type}, Extension: {file_extension}")
    
    temp_audio_path = None
    temp_output_path = None
    
    try:
        # Create temporary file for uploaded audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_audio:
            contents = await file.read()
            temp_audio.write(contents)
            temp_audio_path = temp_audio.name
        
        # Transcribe audio
        logger.info(f"Transcribing audio file: {file.filename}")
        transcribed_text = await transcribe_audio_async(temp_audio_path)
        
        # Translate text
        logger.info(f"Translating to language: {target_language}")
        translated_text = await translate_text_async(transcribed_text, target_language)
        
        # Convert to speech
        temp_output_path = tempfile.mktemp(suffix=".mp3")
        logger.info("Converting translated text to speech")
        await text_to_speech_async(translated_text, temp_output_path, target_language)
        
        # Return the audio file
        return FileResponse(
            temp_output_path,
            media_type="audio/mpeg",
            filename=f"translated_{file.filename}.mp3"
        )
        
    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")
    
    finally:
        # Clean up temporary files
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.unlink(temp_audio_path)
        # Note: temp_output_path will be cleaned up by FastAPI after response

async def transcribe_audio_async(audio_path: str) -> str:
    """
    Transcribe audio file to text using Whisper model (async wrapper).
    """
    def _transcribe():
        try:
            logger.info("Transcribing audio...")
            result = whisper_model.transcribe(audio_path)
            return result["text"]
        except Exception as e:
            logger.error(f"Error during transcription: {str(e)}")
            raise
    
    # Run CPU-bound operation in thread pool
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _transcribe)

async def translate_text_async(text: str, target_language: str = 'es') -> str:
    """
    Translate text to target language using Google Translate (async wrapper).
    """
    def _translate():
        try:
            logger.info("Translating text...")
            # Split text into smaller chunks (sentences)
            sentences = text.split('. ')
            translated_sentences = []
            
            for sentence in sentences:
                if not sentence.strip():
                    continue
                    
                try:
                    # Add a small delay to avoid rate limiting
                    time.sleep(0.5)
                    translator = GoogleTranslator(source='auto', target=target_language)
                    translated = translator.translate(sentence)
                    translated_sentences.append(translated)
                    logger.info(f"Translated: {sentence[:50]}...")
                except Exception as e:
                    logger.warning(f"Failed to translate sentence: {str(e)}")
                    # Keep the original sentence if translation fails
                    translated_sentences.append(sentence)
            
            return '. '.join(translated_sentences)
        except Exception as e:
            logger.error(f"Error during translation: {str(e)}")
            raise
    
    # Run I/O-bound operation in thread pool
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _translate)

async def text_to_speech_async(text: str, output_path: str, language: str = 'es'):
    """
    Convert text to speech using Google Text-to-Speech (async wrapper).
    """
    def _text_to_speech():
        try:
            logger.info("Converting text to speech...")
            # Split text into chunks to handle large texts
            max_chunk_size = 5000
            chunks = [text[i:i+max_chunk_size] for i in range(0, len(text), max_chunk_size)]
            
            # Create temporary files for each chunk
            temp_files = []
            for i, chunk in enumerate(chunks):
                temp_file = f"temp_{i}_{os.getpid()}.mp3"
                tts = gTTS(text=chunk, lang=language, slow=False)
                tts.save(temp_file)
                temp_files.append(temp_file)
                logger.info(f"Created audio chunk {i+1}/{len(chunks)}")
            
            # Combine all temporary files
            if len(temp_files) > 1:
                # Use ffmpeg to concatenate audio files
                concat_file = f"concat_list_{os.getpid()}.txt"
                with open(concat_file, "w") as f:
                    for temp_file in temp_files:
                        f.write(f"file '{temp_file}'\n")
                
                os.system(f"ffmpeg -f concat -safe 0 -i {concat_file} -c copy {output_path}")
                
                # Clean up temporary files
                for temp_file in temp_files:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                if os.path.exists(concat_file):
                    os.remove(concat_file)
            else:
                # If only one chunk, just rename the file
                os.rename(temp_files[0], output_path)
                
            logger.info(f"Audio saved to {output_path}")
        except Exception as e:
            logger.error(f"Error during text-to-speech conversion: {str(e)}")
            raise
    
    # Run I/O-bound operation in thread pool
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _text_to_speech)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 