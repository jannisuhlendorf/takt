from functools import partial
import os
from typing import Callable
import pyo

from takt.exceptions import NotFoundException


class Beat:
    """
    implements a simple beat that can trigger a number of callback functions
    at certain beat positions. In addition it is possible to change the timing
    of single beat steps.
    """

    def __init__(self, no_patterns: int, steps: int, bpm: float):
        """
        :param no_patterns: number of patterns (number of samples to trigger)
        :param steps: number of steps
        :param bpm: beats per minute
        """
        self.time_per_step = 1. / bpm * 60 / 4
        self.duration = steps * self.time_per_step
        self.offsets = [[0.] * steps for _ in range(no_patterns + 1)]
        self.pattern = [[False] * steps for _ in range(no_patterns + 1)]
        self.pattern_tables = [
            pyo.NewTable(self.duration) for _ in range(no_patterns + 1)
        ]
        self.trigger_tables = [
            pyo.TableRead(table, freq=1./self.duration, interp=1, loop=1)
            for table in self.pattern_tables
        ]
        self.trigger_functions = [
            pyo.TrigFunc(trigger, lambda: None)
            for trigger in self.trigger_tables
        ]
        self.sampling_rate = self.trigger_tables[0].getSamplingRate()

        # the last pattern is always on to implement a callback at each step
        for step in range(steps):
            self.activate(no_patterns, step)

    def register_callback(self, pattern: int, func: Callable):
        """
        register a callback function that is called each time the corresponding
        pattern is triggered
        """
        self.trigger_functions[pattern].setFunction(func)

    def register_step_callback(self, func: Callable):
        """
        register a callback function that is called each step
        """
        pos_all_on_pattern = len(self.pattern_tables) - 1
        self.register_callback(pos_all_on_pattern, func)

    def play(self):
        """
        start the beat
        """
        [t.play() for t in self.trigger_tables]

    def stop(self):
        """
        stop the beat
        """
        [t.stop() for t in self.trigger_tables]

    def toggle(self, pattern: int, step: int):
        """
        toggle a pattern step
        (switch in on if it was off before and vice versa)
        """
        if not self.is_on(pattern, step):
            self.activate(pattern, step)
        else:
            self.deactivate(pattern, step)

    def activate(self, pattern: int, step: int):
        """
        activate the trigger of a pattern at a certain step
        """
        beat_time = (self.time_per_step * step) + self.offsets[pattern][step]
        index = int(self.sampling_rate * beat_time)
        self.pattern_tables[pattern].put(1., pos=index)
        self.pattern[pattern][step] = True

    def deactivate(self, pattern, step):
        """
        deactivate the trigger of a pattern at a certain step
        """
        beat_time = (self.time_per_step * step) + self.offsets[pattern][step]
        index = int(self.sampling_rate * beat_time)
        self.pattern_tables[pattern].put(0., pos=index)
        self.pattern[pattern][step] = False

    def change_timing(self, pattern: int, step: int, by: float):
        """
        change the precise timing of a certain step in miliseconds
        """
        self.deactivate(pattern, step)
        self.offsets[pattern][step] += by / 1000
        self.activate(pattern, step)

    def is_on(self, pattern: int, step: int) -> bool:
        """
        get the state of a pattern position (on or off)
        """
        return self.pattern[pattern][step]


class Sampler:
    """
    implements a simple sampler, that can load samples and play them at
    certain beat position
    """

    def __init__(self, steps=16, no_samples=8, bpm=125, callback=None):
        """
        :param steps: number of steps in the pattern
        :param no_samples: number of samples
        :param bpm: beats per minute (assuming a 4-bar-pattern)
        :param callback: callback function that is called each step
        """
        self.steps = steps
        self.samples = [None] * no_samples
        self.callback = callback
        self.pos = 0
        self.velocity = self._create_parameter_matrix()
        self.speed = self._create_parameter_matrix()
        self.beat = Beat(no_patterns=no_samples, steps=steps, bpm=bpm)
        self.beat.register_step_callback(self._step)
        for pos in range(no_samples):
            func = partial(self.trigger, sample_pos=pos)
            self.beat.register_callback(pos, func)

    def _create_parameter_matrix(self, value=1.):
        return [[value] * self.steps for _ in self.samples]

    def load_sample(self, path: str, sample_pos: int):
        """
        load a sample to a certain position
        :param path: path to sample file
        :param sample_pos: position in sampler to load sample to
        """
        if not os.path.isfile(path):
            raise NotFoundException(f'Sample {path} not found.')
        self.samples[sample_pos] = pyo.SfPlayer(path, speed=1, loop=False)

    def start(self):
        """
        start the sampler
        """
        self.beat.play()

    def stop(self):
        """
        stop the sampler
        """
        self.beat.stop()

    def _step(self):
        """
        method that is called at each step
        """
        self.pos = (self.pos + 1) % self.steps
        if self.callback is not None:
            self.callback()

    def trigger(self, sample_pos: int):
        """
        trigger a sample
        :param sample_pos: position of sample
        """
        sample = self.samples[sample_pos]
        if sample is not None:
            sample.setMul(self.velocity[sample_pos][self.pos])
            sample.setSpeed(self.speed[sample_pos][self.pos])
            sample.out()

    def toggle(self, sample_pos: int, step: int):
        """
        toggle a pattern step
        (switch in on if it was off before and vice versa)
        """
        self.beat.toggle(sample_pos, step)

    def is_on(self, sample_pos: int, step: int) -> bool:
        """
        get the state of a pattern position (on or off)
        """
        return self.beat.is_on(sample_pos, step)

    def change_velocity(self, sample_pos: int, step: int, by: float):
        """
        alter the velocity of a sample at a specific step
        :param sample_pos: sample position
        :param step: position in beat
        :param by: float to alter velocity by
        :return: new velocity value
        """
        self.velocity[sample_pos][step] += by
        return self.velocity[sample_pos][step]

    def change_speed(self, sample_pos: int, step: int, by: float):
        """
        alter the playback speed of a sample at a specific step
        :param sample_pos: sample position
        :param step: position in beat
        :param by: float to alter velocity by
        :return: new playback speed
        """
        self.speed[sample_pos][step] += by
        return self.speed[sample_pos][step]

    def change_parameter(self, parameter: str, sample_pos: int, step: int, by: float):
        """
        change the value of a parameter for a sample at a certain beat position
        :param parameter: parameter name
        :param sample_pos: sample position
        :param step: position in beat
        :param by: float to alter parameter by
        :return: new parameter value
        """
        matrix = getattr(self, parameter)
        matrix[sample_pos][step] += by
        return matrix[sample_pos][step]

    def get_parameter_value(self, parameter: str, sample_pos: int, step: int):
        """
        get the value of a parameter for a sample at a certain beat position
        :param parameter: parameter name
        :param sample_pos: sample position
        :param step: position in beat
        :return: parameter value
        """
        matrix = getattr(self, parameter)
        return matrix[sample_pos][step]
