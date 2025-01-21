from typing import Optional, TYPE_CHECKING, Union, Any

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray
    ArrayType = NDArray[np.int16]
else:
    ArrayType = Any  # Fallback type when numpy isn't available

try:
    from google.cloud import texttospeech
except ImportError:
    texttospeech = None
try:
    import sounddevice as sd
except ImportError:
    sd = None
except OSError:
    sd = None

try:
    import numpy as np
except ImportError:
    np = None

try:
    from rich import console
    console = console.Console()
except ImportError:
    console = None

from ..custom_logging import log
import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import io
import wave

import argparse
import sys

class StreamingTTS:
    """
    # Example usage
    def sample_text_stream():
        sentences = [
            "Hello, this is a test of streaming text to speech.",
            "Each sentence will be converted to audio separately.",
            "This allows for lower latency in long-form text to speech conversion."
        ]
        for sentence in sentences:
            yield sentence
            time.sleep(0.5)  # Simulate delay between text chunks

    # Initialize and run
    tts = StreamingTTS()
    tts.process_text_stream(sample_text_stream())    
    """
    def __init__(self):
        if texttospeech is None or sd is None or np is None:
            raise ImportError(f"StreamingTTS requires imports via pip install sunholo[tts] - {texttospeech=} {sd=} {np=}")
        
        log.info("Initializing StreamingTTS...")
        self.client = texttospeech.TextToSpeechClient()
        self.audio_queue = queue.Queue()
        self.is_playing = False
        self.sample_rate = 24000  # Google's default sample rate
        self.language_code = "en-GB"
        self.voice_gender = texttospeech.SsmlVoiceGender.NEUTRAL
        self.voice_name = "en-GB-Journey-D"
        # Audio processing parameters
        # Separate fade durations for playback and file saving
        self.playback_fade_duration = 0.05  # 50ms fade for real-time playback
        self.file_fade_duration = 0.01      # 10ms fade for file saving
        self.stream = None
        self._initialize_audio_device()

    def set_voice(self, voice_name: str):
        """
        Set the language for text-to-speech conversion.
        
        Args:
            language_code: Language code in BCP-47 format (e.g., 'en-US', 'es-ES', 'fr-FR')
        """
        log.info(f"Setting voice to {voice_name}")
        self.voice_name = voice_name

    def set_language(self, language_code: str):
        """
        Set the language for text-to-speech conversion.
        
        Args:
            language_code: Language code in BCP-47 format (e.g., 'en-US', 'es-ES', 'fr-FR')
        """
        log.info(f"Setting language to {language_code}")
        self.language_code = language_code
        
    def set_voice_gender(self, gender: str):
        """
        Set the voice gender for text-to-speech conversion.
        
        Args:
            gender: One of 'NEUTRAL', 'MALE', or 'FEMALE'
        """
        gender_map = {
            'NEUTRAL': texttospeech.SsmlVoiceGender.NEUTRAL,
            'MALE': texttospeech.SsmlVoiceGender.MALE,
            'FEMALE': texttospeech.SsmlVoiceGender.FEMALE
        }
        
        if gender not in gender_map:
            raise ValueError(f"Invalid gender '{gender}'. Must be one of: {', '.join(gender_map.keys())}")
        
        log.info(f"Setting voice gender to {gender}")
        self.voice_gender = gender_map[gender]

    def text_to_audio(self, text):
        """Convert text chunk to audio bytes using Google Cloud TTS."""
        log.info(f"TTS: {text=}")
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        voice = texttospeech.VoiceSelectionParams(
            language_code=self.language_code,
            ssml_gender=self.voice_gender,
            name=self.voice_name
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            sample_rate_hertz=self.sample_rate
        )
        
        response = self.client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        log.info("Got response from TTS")
        
        # Convert audio bytes to numpy array for playback
        audio_np = np.frombuffer(response.audio_content, dtype=np.int16)
        return audio_np

    def generate_audio_stream(self, text):
        """
        Generate a stream of audio data from a text chunk.
        Returns audio in WAV format for streaming.
        
        Args:
            text (str): Text to convert to speech
            
        Yields:
            bytes: WAV-formatted audio data
        """
        try:
            # Convert text to audio using existing method
            audio_chunk = self.text_to_audio(text)
            
            # Process audio chunk with fading
            processed_chunk = self._apply_fade(
                audio_chunk,
                fade_duration=self.file_fade_duration,
                fade_in=True,
                fade_out=True
            )
            
            # Convert to WAV format
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(processed_chunk.tobytes())
            
            yield wav_buffer.getvalue()
            
        except Exception as e:
            log.error(f"Error generating audio stream: {e}")
            yield b''
    
    def _initialize_audio_device(self):
        """Initialize audio device with proper settings."""
        try:
            # Set default device settings
            sd.default.samplerate = self.sample_rate
            sd.default.channels = 1
            sd.default.dtype = np.int16
            
            # Initialize persistent output stream
            self.stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.int16,
                latency='low'
            )
            self.stream.start()
            
            log.info("Audio device initialized successfully")
        except Exception as e:
            log.error(f"Error initializing audio device: {e}")
            raise

    def _make_fade(self, length: int, fade_type: str='l') -> ArrayType:
        """Generate a fade curve of specified length and type."""
        if np is None:  # Runtime check
            raise ImportError("numpy is required. Install with pip install sunholo[tts]")
    
        fade = np.arange(length, dtype=np.float32) / length
        
        if fade_type == 't':  # triangle
            pass
        elif fade_type == 'q':  # quarter of sinewave
            fade = np.sin(fade * np.pi / 2)
        elif fade_type == 'h':  # half of sinewave
            fade = (1 - np.cos(fade * np.pi)) / 2
        elif fade_type == 'l':  # logarithmic
            fade = np.power(0.1, (1 - fade) * 5)
        elif fade_type == 'p':  # inverted parabola
            fade = (1 - (1 - fade)**2)
        else:
            raise ValueError(f"Unknown fade type {fade_type!r}")
        
        return fade
    
    def _apply_fade(self, audio: ArrayType, fade_duration: float, fade_in: bool = True, fade_out: bool = True) -> ArrayType:
        """Apply fade in/out to audio with specified duration."""
        if np is None:  # Runtime check
            raise ImportError("numpy is required. Install with pip install sunholo[tts]")
    
        if audio.ndim != 1:
            raise ValueError("Audio must be 1-dimensional")
        
        fade_length = int(fade_duration * self.sample_rate)
        audio = audio.astype(np.float32)
        
        if fade_in:
            fade_in_curve = self._make_fade(fade_length, 'l')
            audio[:fade_length] *= fade_in_curve
            
        if fade_out:
            fade_out_curve = self._make_fade(fade_length, 'l')
            audio[-fade_length:] *= fade_out_curve[::-1]
        
        return audio.astype(np.int16)

    
    def _play_audio_chunk(self, audio_chunk: ArrayType, is_final_chunk: bool = False):
        """Play a single audio chunk with proper device handling."""
        if np is None:  # Runtime check
            raise ImportError("numpy is required. Install with pip install sunholo[tts]")
    
        try:
            # Add longer padding for the final chunk
            padding_duration = 0.1 if is_final_chunk else 0.02
            padding = np.zeros(int(padding_duration * self.sample_rate), dtype=np.int16)
            
            if is_final_chunk:
                # For final chunk, add extra padding and longer fade
                audio_with_padding = np.concatenate([
                    padding, 
                    audio_chunk, 
                    padding,
                    np.zeros(int(0.2 * self.sample_rate), dtype=np.int16)  # Extra tail padding
                ])
                fade_duration = self.playback_fade_duration * 2  # Longer fade for end
            else:
                audio_with_padding = np.concatenate([padding, audio_chunk, padding])
                fade_duration = self.playback_fade_duration
            
            processed_audio = self._apply_fade(
                audio_with_padding,
                fade_duration=fade_duration,
                fade_in=True,
                fade_out=True
            )
            
            if self.stream and self.stream.active:
                self.stream.write(processed_audio)
                if is_final_chunk:
                    # Write a small buffer of silence at the end
                    final_silence = np.zeros(int(0.1 * self.sample_rate), dtype=np.int16)
                    self.stream.write(final_silence)
            else:
                with sd.OutputStream(
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype=np.int16,
                    latency='low'
                ) as temp_stream:
                    temp_stream.write(processed_audio)
                    if is_final_chunk:
                        temp_stream.write(np.zeros(int(0.1 * self.sample_rate), dtype=np.int16))
            
        except Exception as e:
            log.error(f"Error during audio playback: {e}")
            raise
    
    def audio_player(self):
        """Continuously play audio chunks from the queue."""
        log.info("Audio player started")
        try:
            while self.is_playing or not self.audio_queue.empty():
                if not self.audio_queue.empty():
                    audio_chunk = self.audio_queue.get()
                    self._play_audio_chunk(audio_chunk)
                time.sleep(0.005)  # Reduced sleep time for more responsive playback
        finally:
            # Ensure stream is properly closed
            if self.stream and self.stream.active:
                self.stream.stop()
                self.stream.close()
                self.stream = None

    def __del__(self):
        """Cleanup method to ensure stream is closed."""
        if hasattr(self, 'stream') and self.stream and self.stream.active:
            # Write a small silence buffer before closing
            final_silence = np.zeros(int(0.1 * self.sample_rate), dtype=np.int16)
            try:
                self.stream.write(final_silence)
                time.sleep(0.1)  # Let the final audio finish playing
            except Exception:
                pass  # Ignore errors during cleanup
            self.stream.stop()
            self.stream.close()
    
    def process_text_stream(self, text_generator):
        """Process incoming text stream and convert to audio."""
        self.is_playing = True
        
        # Start audio playback thread
        player_thread = threading.Thread(target=self.audio_player)
        player_thread.start()
        
        try:
            # Process text chunks in parallel
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = []
                for text_chunk in text_generator:
                    future = executor.submit(self.text_to_audio, text_chunk)
                    futures.append(future)
                
                # Process results as they complete
                for future in futures:
                    audio_chunk = future.result()
                    self.audio_queue.put(audio_chunk)
        finally:
            self.is_playing = False
            player_thread.join()
    
    def save_to_file(self, text_generator, output_path):
        """Save the audio to a WAV file with minimal fading."""
        import wave
        
        all_audio = []
        for text_chunk in text_generator:
            audio_chunk = self.text_to_audio(text_chunk)
            # Use shorter fade duration for file saving
            processed_chunk = self._apply_fade(
                audio_chunk,
                fade_duration=self.file_fade_duration
            )
            all_audio.append(processed_chunk)
        
        # Add minimal silence between chunks
        silence = np.zeros(int(0.05 * self.sample_rate), dtype=np.int16)
        final_audio = silence
        
        for i, chunk in enumerate(all_audio):
            if i == len(all_audio) - 1:
                # For the last chunk, use a slightly longer fade out
                chunk = self._apply_fade(
                    chunk,
                    fade_duration=self.file_fade_duration * 2,
                    fade_in=False,
                    fade_out=True
                )
            final_audio = np.concatenate([final_audio, chunk, silence])
        
        with wave.open(output_path, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(final_audio.tobytes())

def tts_command(args):
    """
    Executes the TTS command based on parsed arguments.
    
    Args:
        args: The parsed command-line arguments.
    """
    if console is None:
        raise ImportError("Need cli tools to use TTS commands - install via `pip install sunholo[cli,tts]`")
    
    from rich.panel import Panel

    def text_generator(input_source: str, is_file: bool = False):
        """Generate text from either a file or direct input."""
        if is_file:
            try:
                with open(input_source, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:  # Skip empty lines
                            yield line
            except FileNotFoundError:
                console.print(f"Error: The input file '{input_source}' was not found.")
                sys.exit(1)
        else:
            yield input_source

    try:
        tts = StreamingTTS()
        
        # Configure TTS based on arguments
        if args.language:
            tts.set_language(args.language)
        if args.voice_gender:
            tts.set_voice_gender(args.voice_gender)
        if args.sample_rate:
            tts.sample_rate = args.sample_rate
        if args.voice_name:
            tts.set_voice(args.voice_name)

        # Process the text
        if args.action == 'speak':
            console.print(
                Panel((
                    f"Saying: {args.text}"
                    ), 
                    title="Text to Speech",
                    subtitle=f"{tts.voice_name} is talking"),
                    )
            tts.process_text_stream(
                text_generator(args.text, is_file=args.file)
            )
        elif args.action == 'save':
            if not args.output:
                console.print("Error: Output file path is required for save action")
                return
            
            tts.save_to_file(
                text_generator(args.text, is_file=args.file),
                args.output
            )
            
        console.rule("Successfully processed text-to-speech request.")
            
    except Exception as e:
        console.print(f"[bold red]Error processing text-to-speech: {str(e)}[/bold red]")
        return

def setup_tts_subparser(subparsers):
    """
    Sets up an argparse subparser for the 'tts' command.
    
    Args:
        subparsers: The subparsers object from argparse.ArgumentParser().
    """
    # TTS main parser
    tts_parser = subparsers.add_parser('tts', help='Text-to-Speech conversion utilities')
    tts_subparsers = tts_parser.add_subparsers(dest='action', help='TTS subcommands')

    # Common arguments for both speak and save commands
    common_args = argparse.ArgumentParser(add_help=False)
    common_args.add_argument('text', help='Text to convert to speech (or file path if --file is used)')
    common_args.add_argument('--file', action='store_true', 
                            help='Treat the text argument as a file path')
    common_args.add_argument('--language', default='en-GB',
                            help='Language code (e.g., en-US, es-ES)')
    common_args.add_argument('--voice-gender', choices=['NEUTRAL', 'MALE', 'FEMALE'],
                            default='NEUTRAL', help='Voice gender to use')
    common_args.add_argument('--sample-rate', type=int, default=24000,
                            help='Audio sample rate in Hz')
    common_args.add_argument('--voice_name', default='en-GB-Journey-D', help='A voice name from supported list at https://cloud.google.com/text-to-speech/docs/voices')

    # Speak command - converts text to speech and plays it
    speak_parser = tts_subparsers.add_parser('speak', 
                                            help='Convert text to speech and play it',
                                            parents=[common_args])
    speak_parser.set_defaults(func=tts_command)

    # Save command - converts text to speech and saves to file
    save_parser = tts_subparsers.add_parser('save',
                                           help='Convert text to speech and save to file',
                                           parents=[common_args])
    save_parser.add_argument('--output', default='audio.wav',
                            help='Output audio file path (.wav)')
    save_parser.set_defaults(func=tts_command)

    # Set the default function for the TTS parser
    tts_parser.set_defaults(func=lambda args: tts_parser.print_help())
    

