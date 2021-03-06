import argparse
import time
import pyo
import sys

from takt.push import PushInterface
from takt.sampler import Sampler


COLOR_OFF = 0
COLOR_RUNNING = 5
COLOR_ON = 13


class PushUI(PushInterface):

    def __init__(self, server):
        super().__init__(server)
        self.parameter_modified = {}
        self.sampler = Sampler(steps=8, no_samples=8, callback=self.step)

    def step(self):
        """increase time-step by one"""
        pos = self.sampler.pos
        previous_pos = pos - 1
        if previous_pos < 0:
            previous_pos = 7
        for i in range(8):
            self.draw(i, previous_pos)
            self.draw(i, pos)

        for pos in range(4):
            self.clear_display_line(pos)
        self.write_display_text(0, 0, 'velocity')
        self.write_display_text(0, 11, 'speed')
        self.write_display_text(0, 18, 'timing')

    def draw(self, row, step):
        if step == self.sampler.pos:
            self.set_pad_color(row, step, COLOR_RUNNING)
        else:
            if self.sampler.is_on(row, step):
                self.set_pad_color(row, step, COLOR_ON)
            else:
                self.set_pad_color(row, step, COLOR_OFF)

    def pad_down(self, row: int, step: int):
        self.parameter_modified[(row, step)] = False

    def pad_release(self, row: int, step: int):
        if not self.parameter_modified[(row, step)]:
            self.sampler.toggle(row, step)
            self.draw(row, step)
        del self.parameter_modified[(row, step)]

    def dial_change(self, dial_id: int, value: float):
        change = value / 30
        for row, step in self.parameter_modified:
            if dial_id == 71:
                self.sampler.change_velocity(row, step, by=change)
            elif dial_id == 72:
                self.sampler.change_speed(row, step, by=change)
            elif dial_id == 73:
                self.sampler.change_timing(row, step, by=change*100)
            self.parameter_modified[(row, step)] = True


def main():
    parser = argparse.ArgumentParser(description="runs a sampler that can be controlled with push 1.")
    parser.add_argument('--midi_in', default=0, type=int, help='MIDI IN port of push interface')
    parser.add_argument('--midi_out', default=2, type=int, help='MIDI OUT port of push interface')
    parser.add_argument('--list_devices', action='store_true')
    parser.add_argument('--audio_out_device', default=0, type=int, help='audio output device (start with option '
                                                                     '--list_devices too see available devices)')

    args = parser.parse_args()

    if args.list_devices:
        pyo.pa_list_devices()
        pyo.pm_list_devices()
        sys.exit()

    server = pyo.Server()
    server.setOutputDevice(args.audio_out_device)
    server.setMidiInputDevice(args.midi_in)
    server.setMidiOutputDevice(args.midi_out)
    server.boot()
    server.start()
    push = PushInterface(server)
    ui = PushUI(server)
    ui.sampler.load_sample('samples/BD-short.wav', 0)
    ui.sampler.load_sample('samples/SD-short.wav', 1)
    ui.sampler.load_sample('samples/LT-short.wav', 2)
    ui.sampler.load_sample('samples/MT-short.wav', 3)
    ui.sampler.load_sample('samples/HT-short.wav', 4)
    ui.sampler.load_sample('samples/RS-short.wav', 5)
    ui.sampler.load_sample('samples/CH-short.wav', 6)
    ui.sampler.load_sample('samples/OH-short.wav', 7)
    ui.sampler.start()
    while 1:
        time.sleep(1)


if __name__ == '__main__':
    main()
