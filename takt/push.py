from takt.midi import MidiReceiver

USER_MODE_CMD = b'\xf0G\x7f\x15b\x00\x01\x00\xf7'


def convert_midi_to_pad_position(note):
    base = note - 36
    step = base % 8
    row = base // 8
    return row, step


def convert_pad_position_to_midi(row, step):
    return row * 8 + step + 36


class PushInterface(MidiReceiver):

    """
    implements an interface to the ableton push 1 controller
    """

    def __init__(self, server):
        super().__init__(server)
        # set push to user mode
        server.sysexout(USER_MODE_CMD)

    def note_on(self, note, velocity):
        if 36 <= note <= 99:
            row, step = convert_midi_to_pad_position(note)
            self.pad_down(row, step)

    def note_off(self, note, velocity):
        if 36 <= note <= 99:
            row, step = convert_midi_to_pad_position(note)
            self.pad_release(row, step)

    def control_change(self, data1: int, data2: int):
        if data2 < 64:
            change = data2
        else:
            change = data2 - 128
        self.dial_change(data1, change)

    def pad_down(self, row: int, step: int):
        """
        called when a pad is pushed down
        :param row: row number
        :param step: column position
        """

    def pad_release(self, row: int, step: int):
        """
        called when a pad is released
        :param row: row number
        :param step: column position
        """

    def dial_change(self, dial_id: int, value: float):
        """
        called for rotary knob changes
        :param dial_id: number of dial changed
        :param value: value change
        """

    def button_down(self, button_id: int):
        """
        called when a button is pressed
        :param button_id: button id
        """

    def button_release(self, button_id: int):
        """
        called when a button is released
        :param button_id: button id
        """

    def set_pad_color(self, row: int, step: int, value: int):
        note = convert_pad_position_to_midi(row, step)
        self.server.noteout(note, value)

    def clear_display_line(self, line: int):
        """
        clear a line on the display
        """
        data = bytes([240, 71, 127, 21, 28 + line, 0, 0, 247])
        self.server.sysexout(data)

    def write_display_text(self, line: int, offset: int, text: str):
        """
        write a text to the push display
        :param line: line number (0-3)
        :param offset:
        :param text: text to write
        """
        data = bytes(
            [240, 71, 127, 21, 24 + line, 0, len(text) + 1, offset] + [ord(x) for x in text] + [247]
        )
        self.server.sysexout(data)


