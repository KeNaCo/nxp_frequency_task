"""
To use the script please import and call `configure_frequency` function.
Script doesn't use any external libraries except for testing.
To run tests, please install pytest:

pip install pytest

I implemented two versions, I kept them both for comparison.
The version 2 is more modular and can be used to easily define bigger structures.
The algorithm will return a near frequency in the case exact match is not achieved.
"""
from typing import Self

BUS_CLOCK = 16  # Mhz


# Version 2


class ClockDividerUnit:
    """Clock divider is a block containing multiplexer and dividers."""

    @property
    def _is_parent(self) -> bool:
        return self._child is not None

    @property
    def _is_child(self) -> bool:
        return self._parent is not None

    def __init__(self, dividers: tuple[int, ...]):
        self._dividers = sorted(dividers, reverse=True)
        self._configuration: int = 1
        self._temp_configuration: int = self._configuration
        self._best_frequency: float = 0

        self._child: "ClockDividerUnit" | None = None
        self._parent: "ClockDividerUnit" | None = None

    def _set_best_configuration(self):
        self._configuration = self._temp_configuration
        if self._is_child:
            self._parent._set_best_configuration()

    def chain(self, divider_unit: "ClockDividerUnit") -> Self:
        self._child = divider_unit
        divider_unit._parent = self
        return self

    def divide(self, expected_frequency: float):
        """Do the division and returns internal clock after the division."""
        for i, value in enumerate(self._dividers):
            clock = expected_frequency * value
            if clock > BUS_CLOCK:  # we overshoot the frequency
                continue

            self._temp_configuration = i
            if self._is_parent:
                self._child.divide(clock)
            else:
                if clock > self._best_frequency:  # do we close from the bottom?
                    self._best_frequency = clock
                    self._set_best_configuration()

    def get_chain_configuration(self):
        configuration = len(self._dividers) - self._configuration
        if self._is_parent:
            return configuration, *self._child.get_chain_configuration()
        return (configuration,)


# Note: depend on how precise the results must be we can replace float with Decimal
def configure_frequency(expected: float) -> tuple[int, ...]:
    """Compute multiplexer configuration to decrease bud clock frequency to expected one.

    :param expected: Expected clock value in the same unit as BUS_CLOCK
    :return: tuple of multiplexer configuration, indexed in the same order as stages
    Multiplexer 1 configuration is under tuple[0]
    Multiplexer 2 configuration is under tuple[1]
    """
    # Note: I assume that dividers are send in increasing order, this way I don't need additional index mapping
    clock_divider_1 = ClockDividerUnit(dividers=(1, 2, 4, 8, 16))
    clock_divider_2 = ClockDividerUnit(dividers=(1, 2, 3, 4, 5))
    clock_divider_1.chain(clock_divider_2)
    clock_divider_1.divide(expected)
    return clock_divider_1.get_chain_configuration()


# Version 1


# Note: depend on how precise the results must be we can replace float with Decimal
# def configure_frequency(expected: float) -> tuple[int, int]:
#    """Compute multiplexer configuration to decrease bud clock frequency to expected one.
#
#    :param expected: Expected clock value in the same unit as BUS_CLOCK
#    :return: tuple of multiplexer configuration, indexed in the same order as stages
#    Multiplexer 1 configuration is under tuple[0]
#    Multiplexer 2 configuration is under tuple[1]
#    """
#    level_1_dividers = (16, 8, 4, 2, 1)
#    multiplexer_index_1 = 1
#    level_2_dividers = (5, 4, 3, 2, 1)
#    multiplexer_index_2 = 1
#    best_clock: float = 0
#
#    for i, value in enumerate(level_1_dividers):
#        clock = expected * value
#        if clock > BUS_CLOCK:  # we overshoot the frequency
#            continue##
#
#        for j, value2 in enumerate(level_2_dividers):
#            clock2 = clock * value2
#            if clock2 > BUS_CLOCK:  # we overshoot the frequency
#                continue
#
#            if clock2 > best_clock:  # do we close from the bottom?
#                best_clock = clock2
#                multiplexer_index_1 = 5 - i
#                multiplexer_index_2 = 5 - j
#
#    return multiplexer_index_1, multiplexer_index_2


def test_bus_clock_whithout_changes():
    assert configure_frequency(16) == (1, 1)


def test_bus_clock_divided_by_two():
    assert configure_frequency(8) == (2, 1)


def test_bus_clock_divided_by_the_last_divider():
    assert configure_frequency(1) == (5, 1)


def test_bus_clock_divided_by_second_level():
    assert configure_frequency(1.33) == (3, 3)


def test_bus_clock_divided_to_smallest_value():
    assert configure_frequency(0.2) == (5, 5)


def test_bus_clock_near_the_result():
    assert configure_frequency(1.35) == (2, 5)
