from __future__ import print_function
import threading
from typing import Callable
import pyaudio
from ibm_watson import SpeechToTextV1
from ibm_watson.websocket import RecognizeCallback, AudioSource

from service_manager import Service, ServiceManager

try:
    from Queue import Queue, Full
except ImportError:
    from queue import Queue, Full

# Initialize queue to store the recordings
CHUNK = 1024
BUF_MAX_SIZE = CHUNK * 10
# Variables for recording the speech
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

""" Place Key and URL """
text_tone_analysis_apikey = '*********************'
text_tone_analysis_url = '*********************'

speech_to_text_apikey = '*********************'
speech_to_text_url = '*********************'

from ibm_watson import ToneAnalyzerV3


def text_tone_analysis(text):
    tone_analyzer = ToneAnalyzerV3(
        version='2017-09-21',
        iam_apikey=text_tone_analysis_apikey,
        url=text_tone_analysis_url
    )

    tone_analysis = tone_analyzer.tone(
        tone_input=text
    ).get_result()

    res = {}
    for tone_category in tone_analysis["document_tone"]["tones"]:
        res[tone_category["score"]] = tone_category

    if res:
        return res[max(res.keys())]
    else:
        raise Exception


# define callback for the speech to text service
class IBMRecognizeCallback(RecognizeCallback):
    def __init__(self, callback: Callable):
        RecognizeCallback.__init__(self)
        self.callback = callback

    def on_transcription(self, transcript):
        self.callback(transcript)

    def on_connected(self):
        print('Connection was successful')

    def on_error(self, error):
        print('Error received: {}'.format(error))

    def on_inactivity_timeout(self, error):
        print('Inactivity timeout: {}'.format(error))

    def on_listening(self):
        print('Service is listening')

    def on_hypothesis(self, hypothesis):
        # self.callback(hypothesis)
        pass

    def on_data(self, data):
        # self.callback(data)
        pass

    def on_close(self):
        print("Connection closed")


class IBMServiceThread(threading.Thread):

    def __init__(self, callback: Callable):
        super(IBMServiceThread, self).__init__()
        self.callback = callback
        self.done = False
        self.stream = None

    def start(self) -> None:
        self.done = True
        super(IBMServiceThread, self).start()

    def stop(self):
        self.stream.stop_stream()

    def run(self) -> None:
        # Buffer to store audio
        q = Queue(maxsize=int(round(BUF_MAX_SIZE / CHUNK)))

        # Create an instance of AudioSource
        audio_source = AudioSource(q, True, True)

        # initialize speech to text service
        speech_to_text = SpeechToTextV1(
            iam_apikey=speech_to_text_apikey,
            url=speech_to_text_url
        )

        # define callback for pyaudio to store the recording in queue
        def pyaudio_callback(in_data, frame_count, time_info, status):
            try:
                q.put(in_data)
            except Full:
                pass  # discard
            return None, pyaudio.paContinue

        # instantiate pyaudio
        audio = pyaudio.PyAudio()

        # open stream using callback
        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
            stream_callback=pyaudio_callback,
            start=False
        )
        self.stream = stream
        stream.start_stream()
        mycallback = IBMRecognizeCallback(self.callback)
        speech_to_text.recognize_using_websocket(audio=audio_source,
                                                 content_type='audio/l16; rate=44100',
                                                 recognize_callback=mycallback,
                                                 interim_results=True)

        audio.terminate()


class IBMService(Service):

    def __init__(self):
        self.thread = IBMServiceThread(self.callback)
        self._callback = None

    def callback(self, data: any):
        if self._callback is not None:
            emotion = text_tone_analysis(data[0]["transcript"])

            self._callback("ibm", -1, data[0]["transcript"], data[0]["confidence"], -1, emotion)

    def register_callback(self, callback: Callable):
        self._callback = callback

    def start(self):
        self.thread.start()

    def stop(self):
        self.thread.stop()


ServiceManager.register_service("ibm", IBMService())
