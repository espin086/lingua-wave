import os
from pathlib import Path
import whisper
from deep_translator import GoogleTranslator
from gtts import gTTS
import logging
import sys
import time
import argparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe audio file to text using Whisper model.
    
    Args:
        audio_path (str): Path to the audio file
        
    Returns:
        str: Transcribed text
    """
    try:
        logger.info("Loading Whisper model...")
        model = whisper.load_model("base")
        logger.info("Transcribing audio...")
        result = model.transcribe(audio_path)
        return result["text"]
    except Exception as e:
        logger.error(f"Error during transcription: {str(e)}")
        raise

def translate_text(text: str, target_language: str = 'es') -> str:
    """
    Translate text to target language using Google Translate.
    
    Args:
        text (str): Text to translate
        target_language (str): Target language code (default: 'es' for Spanish)
        
    Returns:
        str: Translated text
    """
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

def text_to_speech(text: str, output_path: str, language: str = 'es'):
    """
    Convert text to speech using Google Text-to-Speech.
    
    Args:
        text (str): Text to convert to speech
        output_path (str): Path to save the output audio file
        language (str): Language code (default: 'es' for Spanish)
    """
    try:
        logger.info("Converting text to speech...")
        # Split text into chunks to handle large texts
        max_chunk_size = 5000
        chunks = [text[i:i+max_chunk_size] for i in range(0, len(text), max_chunk_size)]
        
        # Create temporary files for each chunk
        temp_files = []
        for i, chunk in enumerate(chunks):
            temp_file = f"temp_{i}.mp3"
            tts = gTTS(text=chunk, lang=language, slow=False)
            tts.save(temp_file)
            temp_files.append(temp_file)
            logger.info(f"Created audio chunk {i+1}/{len(chunks)}")
        
        # Combine all temporary files
        if len(temp_files) > 1:
            # Use ffmpeg to concatenate audio files
            concat_file = "concat_list.txt"
            with open(concat_file, "w") as f:
                for temp_file in temp_files:
                    f.write(f"file '{temp_file}'\n")
            
            os.system(f"ffmpeg -f concat -safe 0 -i {concat_file} -c copy {output_path}")
            
            # Clean up temporary files
            for temp_file in temp_files:
                os.remove(temp_file)
            os.remove(concat_file)
        else:
            # If only one chunk, just rename the file
            os.rename(temp_files[0], output_path)
            
        logger.info(f"Audio saved to {output_path}")
    except Exception as e:
        logger.error(f"Error during text-to-speech conversion: {str(e)}")
        raise

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Translate audio files from English to Spanish',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        'input_file',
        type=str,
        help='Path to the input audio file'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='translated_audio.mp3',
        help='Path to save the output audio file'
    )
    
    parser.add_argument(
        '-l', '--language',
        type=str,
        default='es',
        help='Target language code (default: es for Spanish)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Get the current directory
        current_dir = Path.cwd()
        
        # Convert input file to absolute path
        input_path = Path(args.input_file)
        if not input_path.is_absolute():
            input_path = current_dir / input_path
        
        # Convert output file to absolute path
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = current_dir / output_path
        
        # Verify input file exists
        if not input_path.exists():
            logger.error(f"Input file not found: {input_path}")
            sys.exit(1)
            
        # Step 1: Transcribe audio
        logger.info("Starting transcription process...")
        transcribed_text = transcribe_audio(str(input_path))
        logger.info("Transcription completed successfully")
        
        # Step 2: Translate text
        translated_text = translate_text(transcribed_text, args.language)
        logger.info("Translation completed successfully")
        
        # Step 3: Convert to speech
        text_to_speech(translated_text, str(output_path), args.language)
        logger.info("Text-to-speech conversion completed successfully")
        
        logger.info(f"Process completed. Output saved to: {output_path}")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 