import threading
from typing import Callable

import azure.cognitiveservices.speech as speechsdk
import time

from azure.cognitiveservices.speech import SpeechRecognitionEventArgs

from service_manager import Service, ServiceManager

from azure.cognitiveservices.language.textanalytics import TextAnalyticsClient
from msrest.authentication import CognitiveServicesCredentials


""" Place Keys"""
text_analytics_key = "*********************"
speech_key, service_region = "*********************", "westeurope"


def text_analysis(text):
    credentials = CognitiveServicesCredentials(text_analytics_key)

    # Creates a text analytics with the given settings
    text_analytics_url = "https://westeurope.api.cognitive.microsoft.com/"
    text_analytics = TextAnalyticsClient(endpoint=text_analytics_url, credentials=credentials)
    docs = [
        {
            "id": "1",
            "language": "en",
            "text": text
        }
    ]
    response = text_analytics.sentiment(documents=docs)
    for document in response.documents:
        return "{:.2f}".format(document.score)


class MicrosoftServiceThread(threading.Thread):

    def __init__(self, callback: Callable):
        super(MicrosoftServiceThread, self).__init__()
        self.callback = callback
        self.done = False

    def start(self) -> None:
        self.done = True
        super(MicrosoftServiceThread, self).start()

    def run(self) -> None:
        # Creates an instance of a speech config with specified subscription key and service region.
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)

        # Creates a recognizer with the given settings.
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)

        def stop_cb(evt):
            """callback that stops continuous recognition upon receiving an event `evt`"""
            print('CLOSING on {}'.format(evt))
            speech_recognizer.stop_continuous_recognition()
            self.done = True

        def callback(data):
            res = data.result.text.strip()
            sentiment = text_analysis(res)
            self.callback(data, sentiment)

        # Connect callbacks to the events fired by the speech recognizer.
        # speech_recognizer.recognizing.connect(self.callback)
        speech_recognizer.recognized.connect(callback)
        speech_recognizer.session_started.connect(callback)
        speech_recognizer.session_stopped.connect(callback)
        speech_recognizer.canceled.connect(callback)

        # Stop continuous recognition on either session stopped or canceled events.
        speech_recognizer.session_stopped.connect(stop_cb)
        speech_recognizer.canceled.connect(stop_cb)

        # Start continuous speech recognition.
        speech_recognizer.start_continuous_recognition()

        while not self.done:
            time.sleep(.5)


class MicrosoftService(Service):

    def __init__(self):
        self.thread = MicrosoftServiceThread(self.callback)
        self._callback = None

    def callback(self, data: any, sentiment):
        if self._callback is not None:
            if isinstance(data, SpeechRecognitionEventArgs):
                res = data.result.text.strip()
                if not res: return
                self._callback("microsoft", -1, res, -1, sentiment, None)

    def register_callback(self, callback: Callable):
        self._callback = callback

    def start(self):
        self.thread.start()

    def stop(self):
        self.thread.done = False


ServiceManager.register_service("microsoft", MicrosoftService())
