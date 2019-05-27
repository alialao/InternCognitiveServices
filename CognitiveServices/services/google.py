from __future__ import division

import os
import threading
from typing import Callable

import pyaudio

from google.cloud import speech_v1p1beta1 as speech
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types
from six.moves import queue

from service_manager import ServiceManager, Service

""" Replace the GoogleSpeechToTextConfig.json in the config directory with the correct config and fix the directory"""
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:\ServicesComparisonPython\Config\GoogleSpeechToTextConfig.json"

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms


class MicrophoneStream(object):
    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk

        # Create a thread-safe buffer of audio data
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1, rate=self._rate,
            input=True, frames_per_buffer=self._chunk,
            stream_callback=self._fill_buffer,
        )

        self.closed = False

        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b''.join(data)


def get_line_per_speaker(words_info):
    res = {}
    for word in words_info:
        if word.speaker_tag not in res:
            res[word.speaker_tag] = []
        res[word.speaker_tag].append(word)

    return res


class GoogleServiceThread(threading.Thread):

    def __init__(self, callback: Callable):
        super(GoogleServiceThread, self).__init__()
        self.callback = callback
        self.done = False

    def start(self) -> None:
        self.done = False
        super(GoogleServiceThread, self).start()

    def run(self):
        def listen_print_loop(responses):
            client = language.LanguageServiceClient()
            for response in responses:

                result = response.results[-1]

                words_info = result.alternatives[0].words
                speaker_lines = get_line_per_speaker(words_info)
                res = {}
                confidence = result.alternatives[0].confidence

                for speaker in speaker_lines:
                    for word in speaker_lines[speaker]:
                        if speaker not in res:
                            res[speaker] = ""
                        res[speaker] += word.word + ' '

                        if word.word.lower() in ["exit", "quit", "close"]:
                            print('Exiting..')
                            return

                    # with open("newText.txt", "a") as f:
                    for item in res:
                        #    f.writelines([str(res[item])+"\n"])
                        content = res[item]
                        document = types.Document(
                            content=content,
                            type=enums.Document.Type.PLAIN_TEXT)
                        annotations = client.analyze_sentiment(document=document)
                        score = annotations.document_sentiment.score
                        # magnitude = annotations.document_sentiment.magnitude
                        self.callback(item, res[item], confidence, score)

                        # print("speaker{}: ‘{}’ (Sentiment:{})".format(item, res[item], score))

                    # open and read the file after the appending:
                    # with open("newText.txt", "r") as f:
                    #    print(f.read())

        print('Credentials from environ: {}'.format(
            os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')))

        # language_code = 'nl-NL'
        language_code = 'en-US'  # a BCP-47 language tag

        # Instantiates a client
        client = speech.SpeechClient()

        config = speech.types.RecognitionConfig(
            encoding=speech.enums.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=RATE,
            language_code=language_code,
            enable_speaker_diarization=True)
        # diarization_speaker_count=2)

        streaming_config = speech.types.StreamingRecognitionConfig(
            config=config,
            interim_results=True)

        with MicrophoneStream(RATE, CHUNK) as stream:
            audio_generator = stream.generator()
            requests = (speech.types.StreamingRecognizeRequest(audio_content=content)
                        for content in audio_generator)

            responses = client.streaming_recognize(streaming_config, requests)

            # Now, put the transcription responses to use.
            listen_print_loop(responses)


class GoogleService(Service):

    def __init__(self):
        self.thread = GoogleServiceThread(self.callback)
        self._callback = None

    def callback(self, speaker, data: any, confidence, score):
        if self._callback is not None:
            self._callback("google", speaker, str(data), round(confidence * 100) / 100, round(score * 100) / 100, None)

    def register_callback(self, callback: Callable):
        self._callback = callback

    def start(self):
        self.thread.start()

    def stop(self):
        self.thread.done = True


ServiceManager.register_service("google", GoogleService())
