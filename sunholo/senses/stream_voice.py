try:
    from google.cloud import texttospeech
except ImportError:
    texttospeech = None
try:
    import sounddevice as sd
except ImportError:
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

import argparse
import json
from typing import Optional
from pathlib import Path
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
        self.fade_duration = 0.1  # 10ms fade in/out
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
    
    def _initialize_audio_device(self):
        """Initialize audio device with proper settings."""
        try:
            # Set default device settings
            sd.default.samplerate = self.sample_rate
            sd.default.channels = 1
            sd.default.dtype = np.int16
            
            # Start and stop the stream once to "warm up" the audio device
            dummy_audio = np.zeros(int(self.sample_rate * 1), dtype=np.int16)
            with sd.OutputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.int16,
                latency='low'
            ) as stream:
                stream.write(dummy_audio)
            
            log.info("Audio device initialized successfully")
        except Exception as e:
            log.error(f"Error initializing audio device: {e}")
            raise

    def _make_fade(x, in_length, out_length=None, type='l', copy=True):
        """Apply fade in/out to a signal.

        If `x` is two-dimenstional, this works along the columns (= first
        axis).

        This is based on the *fade* effect of SoX, see:
        http://sox.sourceforge.net/sox.html

        The C implementation can be found here:
        http://sourceforge.net/p/sox/code/ci/master/tree/src/fade.c

        Parameters
        ----------
        x : array_like
            Input signal.
        in_length : int
            Length of fade-in in samples (contrary to SoX, where this is
            specified in seconds).
        out_length : int, optional
            Length of fade-out in samples.  If not specified, `fade_in` is
            used also for the fade-out.
        type : {'t', 'q', 'h', 'l', 'p'}, optional
            Select the shape of the fade curve: 'q' for quarter of a sine
            wave, 'h' for half a sine wave, 't' for linear ("triangular")
            slope, 'l' for logarithmic, and 'p' for inverted parabola.
            The default is logarithmic.
        copy : bool, optional
            If `False`, the fade is applied in-place and a reference to
            `x` is returned.

        """
        x = np.array(x, copy=copy)

        if out_length is None:
            out_length = in_length

        def make_fade(length, type):
            fade = np.arange(length) / length
            if type == 't':  # triangle
                pass
            elif type == 'q':  # quarter of sinewave
                fade = np.sin(fade * np.pi / 2)
            elif type == 'h':  # half of sinewave... eh cosine wave
                fade = (1 - np.cos(fade * np.pi)) / 2
            elif type == 'l':  # logarithmic
                fade = np.power(0.1, (1 - fade) * 5)  # 5 means 100 db attenuation
            elif type == 'p':  # inverted parabola
                fade = (1 - (1 - fade)**2)
            else:
                raise ValueError("Unknown fade type {0!r}".format(type))
            return fade

        # Using .T w/o [:] causes error: https://github.com/numpy/numpy/issues/2667
        x[:in_length].T[:] *= make_fade(in_length, type)
        x[len(x) - out_length:].T[:] *= make_fade(out_length, type)[::-1]
        return x
    
    def _apply_fade(self, audio: np.ndarray, fade_in: bool = True, fade_out: bool = True) -> np.ndarray:
        """Apply fade in/out to audio to prevent clicks."""
        fade_length = int(self.fade_duration * self.sample_rate)
        audio = audio.astype(np.float32)  # Convert to float for fade calculation
        
        if fade_in:
            fade_in_curve = np.linspace(0, 1, fade_length)
            audio[:fade_length] *= fade_in_curve
            
        if fade_out:
            fade_out_curve = np.linspace(1, 0, fade_length)
            audio[-fade_length:] *= fade_out_curve
        
        return audio.astype(np.int16)  # Convert back to int16
    
    def _play_audio_chunk(self, audio_chunk: np.ndarray):
        """Play a single audio chunk with proper device handling."""
        try:
            # Add small silence padding and apply fades
            padding = np.zeros(int(1 * self.sample_rate), dtype=np.int16)
            audio_with_padding = np.concatenate([padding, audio_chunk, padding])
            processed_audio = self._apply_fade(audio_with_padding)
            
            # Use context manager for proper stream handling
            with sd.OutputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.int16,
                latency='low'
            ) as stream:
                stream.write(processed_audio)
                stream.write(np.zeros(int(0.1 * self.sample_rate), dtype=np.int16))  
            
        except Exception as e:
            log.error(f"Error during audio playback: {e}")
            raise
    
    def audio_player(self):
        """Continuously play audio chunks from the queue."""
        log.info("Audio player started")
        while self.is_playing or not self.audio_queue.empty():
            if not self.audio_queue.empty():
                audio_chunk = self.audio_queue.get()
                self._play_audio_chunk(audio_chunk)
            time.sleep(0.1) 
    
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
        """Save the audio to a WAV file instead of playing it."""
        import wave
        
        all_audio = []
        for text_chunk in text_generator:
            audio_chunk = self.text_to_audio(text_chunk)
            processed_chunk = self._apply_fade(audio_chunk)
            all_audio.append(processed_chunk)
        
        # Add small silence between chunks and at ends
        silence = np.zeros(int(0.1 * self.sample_rate), dtype=np.int16)
        final_audio = silence
        for chunk in all_audio:
            final_audio = np.concatenate([final_audio, chunk, silence])
        
        with wave.open(output_path, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # 16-bit audio
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
                    title=f"Text to Speech",
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
    

