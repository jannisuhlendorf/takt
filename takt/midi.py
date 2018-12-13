import logging
import pyo

NOTE_ON = 144
NOTE_OFF = 128
AFTERTOUCH = 160
CC = 176
# TODO: this is only for channel 1 need to add midi codes for other channels

logger = logging.getLogger(__name__)


class MidiReceiver:

    """
    base class for a midi controller

    different methods are called for note_on, note_off, aftertouch and control
    change messages, that should be implemented by subclasses
    """

    def __init__(self, server):

        self.__handlers__ = {
            NOTE_ON: self.note_on,
            NOTE_OFF: self.note_off,
            AFTERTOUCH: self.aftertouch,
            CC: self.control_change
        }

        self.server = server
        self.a = pyo.RawMidi(self._midi_event)

    def _midi_event(self, status, data1, data2):
        if status in self.__handlers__:
            self.__handlers__[status](data1, data2)
        else:
            logger.warning(f'undefined midi input: status: {status} data1: {data1} data2: {data2}')

    def note_on(self, note: int, velocity: int):
        pass

    def note_off(self, note: int, vecolity: int):
        pass

    def aftertouch(self, note: int, pressure: int):
        pass

    def control_change(self, data1: int, data2: int):
        pass
