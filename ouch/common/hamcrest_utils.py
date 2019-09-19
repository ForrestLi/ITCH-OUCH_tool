import datetime
import re
import math
from hamcrest.core.base_matcher import Matcher, BaseMatcher
from hamcrest.core.core.described_as import DescribedAs
from hamcrest.core.helpers.wrap_matcher import wrap_matcher
from hamcrest import *
from raptor_utils import fromFixTimeStamp


class Converted(BaseMatcher):

    def __init__(self, convert, matcher, description):
        self.convert = convert
        self.matcher = wrap_matcher(matcher)
        self.description = description

    def matches(self, item):
        return self.matcher.matches(self.convert(item))

    def describe_to(self, description):
        self.matcher.describe_to(description)
        description.append_text(self.description)


def converted(convert, matcher, description=""):
    """Matches if `matcher` matches after passed through `convert`.
    :param convert: The function to convert the value to be matched.
    :param matcher: The matcher to match the converted value."""
    return Converted(convert, matcher, description)


class IsCloseToDateTime(BaseMatcher):

    def __init__(self, value, delta):
        if not isinstance(value, datetime.datetime):
            raise TypeError('IsCloseToDateTime value must be datetime')
        if not isinstance(delta, datetime.timedelta):
            raise TypeError('IsCloseToDateTime delta must be timedelta')

        self.value = value
        self.delta = delta

    def matches(self, item):
        if not isinstance(item, datetime.datetime):
            return False
        return math.fabs((item - self.value).total_seconds()) <= self.delta.total_seconds()

    def describe_mismatch(self, item, mismatch_description):
        if not isinstance(item, datetime.datetime):
            super(IsCloseToDateTime, self).describe_mismatch(
                item, mismatch_description)
        else:
            actual_delta = datetime.timedelta(
                seconds=math.fabs((item - self.value).total_seconds()))
            mismatch_description.append_description_of(item)            \
                                .append_text(' differed by ')           \
                                .append_description_of(actual_delta)

    def describe_to(self, description):
        description.append_text('a datetime value within ')  \
                   .append_description_of(self.delta)       \
                   .append_text(' of ')                     \
                   .append_description_of(self.value)


def close_to_datetime(value, delta):
    """
    Matches if object is a FIX date/time string close to a given datetime, 
    within a given timedelta.

    :param value: The value to compare against as the expected value.
    :param delta: The maximum timedelta between the values for which the numbers
        are considered close.

    This matcher compares the evaluated object against `value` to see if the
    difference is within a positive `delta`.

    Example::

        close_to_datetime(datetime.datetime.utcnow(), datetime.timedelta(seconds=1))
    """
    return IsCloseToDateTime(value, delta)


def fix_close_to_datetime(value, delta):
    """Matches if object is a datetime close to a given value, within a given
    timedelta.

    :param value: The value to compare against as the expected value.
    :param delta: The maximum timedelta between the values for which the numbers
        are considered close.

    This matcher interprets the evaluated object as a FIX time stamp and compares 
    it against `value` to see if the difference is within a positive `delta`.

    Example::

        fix_close_to_datetime(datetime.datetime.utcnow(), datetime.timedelta(seconds=1))
    """
    return converted(fromFixTimeStamp, close_to_datetime(value, delta), " as fix datetime")


ARG_PATTERN = re.compile('%([0-9]+)')


class AppendDescription(BaseMatcher):

    def __init__(self, description_template, matcher, *values):
        self.template = description_template
        self.matcher = wrap_matcher(matcher)
        self.values = values

    def matches(self, item):
        return self.matcher.matches(item)

    def describe_mismatch(self, item, mismatch_description):
        self.matcher.describe_mismatch(item, mismatch_description)
        text_start = 0
        for match in re.finditer(ARG_PATTERN, self.template):
            mismatch_description.append_text(
                self.template[text_start:match.start()])
            arg_index = int(match.group()[1:])
            mismatch_description.append_description_of(self.values[arg_index])
            text_start = match.end()

        if text_start < len(self.template):
            mismatch_description.append_text(self.template[text_start:])

    def describe_to(self, description):
        self.matcher.describe_to(description)


def append_description(matcher, description, *values):
    """Appends custom failure description to a given matcher's description.
    :param matcher: The matcher to satisfy.
    :param description: Description to append.
    :param value1,...: Optional comma-separated list of substitution values.
    The description may contain substitution placeholders %0, %1, etc. These
    will be replaced by any values that follow the matcher.
    """
    return AppendDescription(description, matcher, *values)
