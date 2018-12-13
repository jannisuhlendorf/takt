import os
import pyo

from takt.exceptions import NotFoundException


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
        self.patterns = []
        self.trigs = []
        self.velocity = self._create_parameter_matrix()
        self.speed = self._create_parameter_matrix()
        self._initialize_patterns()

        w1 = [100] * (no_samples + 1)
        time = 1. / bpm * 60 / 4
        self.beat = pyo.Beat(time=time, taps=self.steps, w1=w1, poly=1)
        self._update_pattern()

    def _initialize_patterns(self):
        """
        create empty beat pattern and the full pattern that is used to trigger
        the callback function at each step
        """
        def empty_pattern(value):
            return [[self.steps] + ([value] * self.steps)]

        for _ in self.samples:
            pattern = empty_pattern(0)
            self.patterns.append(pattern)

        all_on_pattern = empty_pattern(1)
        self.patterns.append(all_on_pattern)

    def _create_parameter_matrix(self, value=1.):
        return [[value] * self.steps for _ in self.samples]

    def _update_pattern(self):
        patterns = self.patterns
        self.beat.setPresets(patterns)
        self.beat.recall(0)

    def _update_trigs(self):
        self.trigs = []
        for pos, sample in enumerate(self.samples):
            if not sample:
                continue
            trig = pyo.TrigFunc(self.beat[pos], self.trigger, pos)
            self.trigs.append(trig)
        stepper = pyo.TrigFunc(self.beat[-1], self._step)
        self.trigs.append(stepper)

    def load_sample(self, path: str, sample_pos: int):
        """
        load a sample to a certain position
        :param path: path to sample file
        :param sample_pos: position in sampler to load sample to
        """
        if not os.path.isfile(path):
            raise NotFoundException(f'Sample {path} not found.')
        player = pyo.SfPlayer(path, speed=1, loop=False)
        self.samples[sample_pos] = player
        self._update_trigs()

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
        sample.setMul(self.velocity[sample_pos][self.pos])
        sample.setSpeed(self.speed[sample_pos][self.pos])
        sample.out()

    def activate(self, sample_pos: int, step: int):
        """
        set a sample to trigger at a certain position
        :param sample_pos: sample position
        :param step: position in beat
        """
        self.patterns[sample_pos][0][step + 1] = 1
        self._update_pattern()

    def deactive(self, sample_pos: int, step: int):
        """
        deactivate trigger of a sample at a certain position
        :param sample_pos: sample position
        :param step: position in beat
        """
        self.patterns[sample_pos][0][step + 1] = 0
        self._update_pattern()

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
