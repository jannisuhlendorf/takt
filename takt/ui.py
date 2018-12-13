import argparse
import time
import pyo

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

    args = parser.parse_args()

    server = pyo.Server()
    server.boot()
    server.start()
    server.setMidiInputDevice(args.midi_in)
    server.setMidiOutputDevice(args.midi_out)
    push = PushInterface(server)
    ui = PushUI(server)
    ui.sampler.load_sample('samples/waot_kick_01.wav', 0)
    ui.sampler.load_sample('samples/waot_snare_01.wav', 1)
    ui.sampler.start()
    while 1:
        time.sleep(1)


if __name__ == '__main__':
    main()
