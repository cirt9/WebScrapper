import functools
from inspect import signature


def connect(subject, event_signal, observer):
    subject.add_event_observer(event_signal, observer)


def disconnect(subject, event_signal, observer):
    subject.remove_event_observer(event_signal, observer)


def signal(event_signal):
    @functools.wraps(event_signal)
    def wrapper(*args, **kwargs):
        subject = args[0]
        signal_args = args[1:]
        event_signal_method = subject.__getattribute__(event_signal.__name__)

        subject.notify(event_signal_method, signal_args, kwargs)

    return wrapper


class Subject:

    def __init__(self):
        self.events = []

    def remove_event(self, event_signal):
        self.events[:] = [event for event in self.events if not event.signal == event_signal]

    def add_event_observer(self, event_signal, observer):
        event_exists = self.append_observer_to_event(event_signal, observer)

        if not event_exists:
            self.add_new_event(event_signal, observer)

    def append_observer_to_event(self, event_signal, observer):
        for event in self.events:
            if event.signal == event_signal:
                event.add_observer(observer)
                return True

        return False

    def add_new_event(self, event_signal, observer):
        event = Event(event_signal)
        event.add_observer(observer)
        self.events.append(event)

    def remove_event_observer(self, event_signal, observer):
        for event in self.events:
            if event.signal == event_signal:
                event.remove_observer(observer)
                break

    def notify(self, event_signal, signal_args, signal_kwargs):
        self.clean_events()

        for event in self.events:
            if event.signal == event_signal:
                event.clean_observers()
                event.execute(signal_args, signal_kwargs)

    def clean_events(self):
        self.events[:] = [event for event in self.events if event.signal is not None]


class Event:

    def __init__(self, event_signal=None):
        self.signal = event_signal
        self.observers = []

    def add_observer(self, observer):
        if observer in self.observers:
            raise DuplicateObserver(f'Duplicate observer "{observer.__name__}" of signal "{self.signal.__name__}"')
        else:
            self.observers.append(observer)

    def remove_observer(self, observer):
        self.observers.remove(observer)

    def execute(self, signal_args, signal_kwargs):
        for observer in self.observers:
            observer_signature = signature(observer)
            number_of_non_kw_parameters = len(observer_signature.parameters) - len(signal_kwargs)

            if number_of_non_kw_parameters < 0:
                raise MoreKwargsThanAccepted(f'Observer: "{observer.__name__}')

            if len(signal_args) < number_of_non_kw_parameters:
                raise TooMuchParametersInObserver(f'Observer: "{observer.__name__}')

            observer(*signal_args[0:number_of_non_kw_parameters], **signal_kwargs)

    def clean_observers(self):
        self.observers[:] = [observer for observer in self.observers if observer is not None]


class DuplicateObserver(Exception):
    pass


class TooMuchParametersInObserver(Exception):
    pass


class MoreKwargsThanAccepted(Exception):
    pass
