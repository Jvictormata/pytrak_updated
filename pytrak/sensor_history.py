"""Sensor History with moving average filtering and distance, velocity"""

import math



class SensorHistory():
    """The Sensory History keeps track of the last n recorded sample and
    calculates online the moving average (running mean).

    SensorHistory.moving_average

    """

    def __init__(self, history_size, number_of_parameter):
        self.history = [[0] * number_of_parameter] * history_size
        self.moving_average = [0] * number_of_parameter
        self._correction_cnt = 0
        self._previous_moving_average = self.moving_average

        self._motion_index = 0
        self._reference_position = None
        self._reference_radius = None

    def __str__(self):
        return str(self.history)

    def update(self, values):
        """Update history and calculate moving average

        (correct for accumulated rounding errors ever 10000 samples)

        Parameter
        ---------
        values : list of values for all sensor parameters

        """

        self._previous_moving_average = self.moving_average
        pop = self.history.pop(0)
        self.history.append(values)
        # pop first element and calc moving average
        if self._correction_cnt > 10000:
            self._correction_cnt = 0
            self.moving_average = self.calc_history_average()
        else:
            self._correction_cnt += 1
            self.moving_average = [x[0] + (float(x[1] - x[2]) / len(self.history)) for x in zip(self.moving_average, values, pop)]


    def calc_history_average(self):
        """Calculate history averages for all sensor parameter.

        The method is more time consuming than calling the property
        `moving_average`. It is does however not suffer from accumulated
        rounding-errors such as moving average.

        """

        s = [float(0)] * self.number_of_parameter
        for t in self.history:
            s = [x[0] + x[1] for x in zip(s, t)]
        return [x / len(self.history) for x in s]

    def distance_to_point(self, point):
        """returns current euclidian distance to a point in space, based on
        filtered data (moving average)

        Note
        ----
        point has to match in the number of dimensions
        """

        return math.sqrt(sum([(x[1] - x[0]) ** 2 for x in zip(self.moving_average, point)]))

    @property
    def history_size(self):
        return len(self.history)

    @property
    def number_of_parameter(self):
        return len(self.history[0])

    @property
    def previous_moving_average(self):
        return self._previous_moving_average

    @property
    def replacement(self):
        """returns the current replacement based on filtered data"""
        return [x[0] - x[1] for x in zip(self.moving_average,
                                              self._previous_moving_average)]

    def velocity(self, sampling_rate):
        """returns the current velocity based on filtered data"""
        return self.distance_to_point(self._previous_moving_average) * sampling_rate

    def is_moving(self, velocity_threshold, min_n_samples, sampling_rate):
        """min_n_samples : minimum number of samples in motion/non-motion

        Returns
        -------
        is_moving : `True` if sensor moving or `False` if sensor is still
                    otherwise (if unclear) `None`

        """

        if self.velocity(sampling_rate) > velocity_threshold:
            if self._motion_index > 0:
                self._motion_index += 1
            else:
                self._motion_index = 1
        else:
            if self._motion_index < 0:
                self._motion_index -= 1
            else:
                self._motion_index = -1

        if abs(self._motion_index) >= min_n_samples:
            return (self._motion_index > 0)

        return None

    def set_reference_area(self, radius):
        self._reference_position = self.moving_average
        self._reference_radius = radius

    def reset_reference_area(self):
        self._reference_position = None
        self._reference_radius = None
        
    def is_in_reference_area(self):
        if self._reference_radius is not None:
            return (self.distance_to_point(self._reference_position) <=
                        self._reference_radius)
        return None
        
if __name__ == "__main__":
    import random
    def run():
        sh = SensorHistory(history_size=5, number_of_parameter=3)
        for x in range(19908):
            x = [random.randint(0, 100), random.randint(0, 100),
                    random.randint(0, 100)]
            sh.update(x)

        print(sh.moving_average, sh.calc_history_average())
        print(sh.velocity(100))

    import timeit
    print(timeit.timeit(run, number=4))

