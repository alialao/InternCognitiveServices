from typing import Callable, Dict


class Service:
    def register_callback(self, callback: Callable): pass

    def start(self): pass

    def stop(self): pass


class ServiceManager:
    SERVICES = {}  # type: Dict[str, Service]

    def __init__(self):
        self._callback = None

    @staticmethod
    def register_service(name: str, service: Service):
        """
        Will register a service to be managed by the manager.

        :param name: Name of the service.
        :param service: Service object.
        """

        ServiceManager.SERVICES[name] = service

    def register_callback(self, callback: Callable):
        """
        Register the callback that will be called when a service received new data.

        :param callback: The callback that should be called.
        """
        self._callback = callback

    def callback(self, source: str, speaker, data: any, confidence, score, emotion):
        """
        Will be called from each service when a new result was received.

        :param data: Result
        """
        if self._callback is not None:
            self._callback(source, speaker, data, confidence, score, emotion)

    def start(self, name: str = None):
        for key in ServiceManager.SERVICES:
            if name is None or name == key:
                ServiceManager.SERVICES[key].register_callback(self.callback)
                ServiceManager.SERVICES[key].start()

    def stop(self, name: str = None):
        for key in ServiceManager.SERVICES:
            if name is None or name == key:
                ServiceManager.SERVICES[key].stop()
