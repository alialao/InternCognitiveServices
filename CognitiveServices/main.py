import json
import os
import threading
from glob import glob
from queue import Queue

from flask import Flask, render_template
import time
from websocket_server import WebsocketServer

from service_manager import ServiceManager
import importlib

for file in glob("services/*.py"): importlib.import_module(file.replace(os.sep, ".")[:-3])

server = WebsocketServer(8765, host='127.0.0.1')
q = Queue()
last = {}


class WebsocketTread(threading.Thread):
    def run(self):
        global server
        global last
        global q
        q = q  # type:Queue
        while True:
            item = q.get()
            last = item
            server.send_message_to_all(item)


class WebsocketThread(threading.Thread):
    def run(self):
        server.run_forever()


def new_client(client, server: WebsocketServer):
    global last
    while last is None:
        time.sleep(0.1)
    data = json.dumps(last)
    server.send_message(client, data)


server.set_fn_new_client(new_client)

WebsocketThread().start()
WebsocketTread().start()

app = Flask(__name__)  # create the application instance :)


def add_result_from_stt_service(service_name: str, speaker, result: any, confidence, score, emotion):
    q.put(json.dumps({
        "service": service_name,
        "speaker": speaker,
        "result": result,
        "confidence": confidence,
        "score": score,
        "emotion": emotion
    }))


@app.route('/', methods=['GET'])
def route_home():
    return render_template("index.html")


def voice_callback(service: str, speaker, data, confidence, score, emotion):
    add_result_from_stt_service(service, speaker, data, confidence, score, emotion)
    print(service, speaker, data, confidence, score, emotion)


service_manager = ServiceManager()
service_manager.register_callback(voice_callback)
service_manager.start()

app.run(debug=True)
