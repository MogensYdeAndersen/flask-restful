from datetime import datetime, timedelta, tzinfo
import unittest

import pytest
import six

from flask_restful import inputs

# http://docs.python.org/library/datetime.html?highlight=datetime#datetime.tzinfo.fromutc
ZERO = timedelta(0)
HOUR = timedelta(hours=1)


class UTC(tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO


class CET(tzinfo):
    """CET"""

    def utcoffset(self, dt):
        return HOUR

    def tzname(self, dt):
        return "CET"

    def dst(self, dt):
        return ZERO


@pytest.mark.parametrize('date_obj,expected', [
    (datetime(2011, 1, 1),
     "Sat, 01 Jan 2011 00:00:00 -0000"),
    (datetime(2011, 1, 1, 23, 59, 59),
     "Sat, 01 Jan 2011 23:59:59 -0000"),
    (datetime(2011, 1, 1, 23, 59, 59, tzinfo=UTC()),
     "Sat, 01 Jan 2011 23:59:59 -0000"),
    (datetime(2011, 1, 1, 23, 59, 59, tzinfo=CET()),
     "Sat, 01 Jan 2011 22:59:59 -0000"),
])
def test_rfc822_datetime_formatters(date_obj, expected):
    assert inputs.rfc822(date_obj), expected


@pytest.mark.parametrize('date_obj,expected', [
    (datetime(2011, 1, 1),
     "2011-01-01T00:00:00+00:00"),
    (datetime(2011, 1, 1, 23, 59, 59),
     "2011-01-01T23:59:59+00:00"),
    (datetime(2011, 1, 1, 23, 59, 59, tzinfo=UTC()),
     "2011-01-01T23:59:59+00:00"),
    (datetime(2011, 1, 1, 23, 59, 59, tzinfo=CET()),
     "2011-01-01T22:59:59+00:00")
])
def test_iso8601_datetime_formatters(date_obj, expected):
    assert inputs.iso8601(date_obj) == expected


@pytest.mark.parametrize('date_string,expected', [
    ("Sat, 01 Jan 2011 00:00:00 -0000",
     datetime(2011, 1, 1, tzinfo=UTC())),
    ("Sat, 01 Jan 2011 23:59:59 -0000",
     datetime(2011, 1, 1, 23, 59, 59, tzinfo=UTC())),
    ("Sat, 01 Jan 2011 21:59:59 -0200",
     datetime(2011, 1, 1, 23, 59, 59, tzinfo=UTC())),
])
def test_reverse_rfc822_datetime(date_string, expected):
    assert inputs.datetime_from_rfc822(date_string) == expected


@pytest.mark.parametrize('date_string,expected', [
    ("2011-01-01T00:00:00+00:00",
     datetime(2011, 1, 1, tzinfo=UTC())),
    ("2011-01-01T23:59:59+00:00",
     datetime(2011, 1, 1, 23, 59, 59, tzinfo=UTC())),
    ("2011-01-01T23:59:59+02:00",
     datetime(2011, 1, 1, 21, 59, 59, tzinfo=UTC())),
])
def test_reverse_iso8601_datetime(date_string, expected):
    assert inputs.datetime_from_iso8601(date_string) == expected


@pytest.mark.parametrize('value', [
    'http://www.djangoproject.com/',
    'http://localhost/',
    'http://example.com/',
    'http://www.example.com/',
    'http://www.example.com:8000/test',
    'http://valid-with-hyphens.com/',
    'http://subdomain.example.com/',
    'http://200.8.9.10/',
    'http://200.8.9.10:8000/test',
    'http://valid-----hyphens.com/',
    'http://example.com?something=value',
    'http://example.com/index.php?something=value&another=value2',
    'http://foo:bar@example.com',
    'http://foo:@example.com',
    'http://foo:@2001:db8:85a3::8a2e:370:7334',
    'http://foo2:qd1%r@example.com',
])
def test_urls(value):
    assert inputs.url(value) == value


@pytest.mark.parametrize('value', [
    'foo',
    'http://',
    'http://example',
    'http://example.',
    'http://.com',
    'http://invalid-.com',
    'http://-invalid.com',
    'http://inv-.alid-.com',
    'http://inv-.-alid.com',
    'foo bar baz',
    u'foo \u2713',
    'http://@foo:bar@example.com',
    'http://:bar@example.com',
    'http://bar:bar:bar@example.com',
])
def test_bad_urls(value):
    with pytest.raises(ValueError):
        inputs.url(value)


def check_url_error_message(value):
    try:
        inputs.url(value)
        assert False, u"inputs.url({0}) should raise an exception".format(value)
    except ValueError as e:
        assert six.text_type(e) == (u"{0} is not a valid URL. Did you mean: "
                                    u"http://{0}".format(value))


@pytest.mark.parametrize('value', [
    'google.com',
    'domain.google.com',
    'kevin:pass@google.com/path?query',
    u'google.com/path?\u2713',
])
def test_bad_url_error_message(value):
    check_url_error_message(value)


class TypesTestCase((unittest.TestCase)):

    def test_boolean_false(self):
        assert inputs.boolean("False") == False

    def test_boolean_is_false_for_0(self):
        assert inputs.boolean("0") == False

    def test_boolean_true(self):
        assert inputs.boolean("true") == True

    def test_boolean_is_true_for_1(self):
        assert inputs.boolean("1") == True

    def test_boolean_upper_case(self):
        assert inputs.boolean("FaLSE") == False

    def test_boolean(self):
        assert inputs.boolean("FaLSE") == False

    def test_boolean_with_python_bool(self):
        """Input that is already a native python `bool` should be passed through
        without extra processing."""
        assert inputs.boolean(True) == True
        assert inputs.boolean(False) == False

    def test_bad_boolean(self):
        with pytest.raises(ValueError):
            inputs.boolean("blah")

    def test_date_later_than_1900(self):
        assert inputs.date("1900-01-01") == datetime(1900, 1, 1)

    def test_date_too_early(self):
        with pytest.raises(ValueError):
            inputs.date("0001-01-01")

    def test_date_input_error(self):
        with pytest.raises(ValueError):
            inputs.date("2008-13-13")

    def test_date_input(self):
        assert inputs.date("2008-08-01") == datetime(2008, 8, 1)

    def test_natual_negative(self):
        with pytest.raises(ValueError):
            inputs.natural(-1)

    def test_natural(self):
        assert inputs.natural(3) == 3

    def test_natual_string(self):
        with pytest.raises(ValueError):
            inputs.natural('foo')

    def test_positive(self):
        assert inputs.positive(1) == 1
        assert inputs.positive(10000) == 10000

    def test_positive_zero(self):
        with pytest.raises(ValueError):
            inputs.positive(0)

    def test_positive_negative_input(self):
        with pytest.raises(ValueError):
            inputs.positive(-1)

    def test_int_range_good(self):
        assert inputs.int_range(1, 5, 3, 'my_arg') == 3

    def test_int_range_inclusive(self):
        assert inputs.int_range(1, 5, 5, 'my_arg') == 5

    def test_int_range_low(self):
        with pytest.raises(ValueError):
            inputs.int_range(0, 5, -1, 'my_arg')

    def test_int_range_high(self):
        with pytest.raises(ValueError):
            inputs.int_range(0, 5, 6, 'my_arg')


@pytest.mark.parametrize('value,expected', [
    (
        # Full precision with explicit UTC.
        "2013-01-01T12:30:00Z/P1Y2M3DT4H5M6S",
        (
            datetime(2013, 1, 1, 12, 30, 0, tzinfo=UTC()),
            datetime(2014, 3, 5, 16, 35, 6, tzinfo=UTC()),
        ),
    ),
    (
        # Full precision with alternate UTC indication
        "2013-01-01T12:30+00:00/P2D",
        (
            datetime(2013, 1, 1, 12, 30, 0, tzinfo=UTC()),
            datetime(2013, 1, 3, 12, 30, 0, tzinfo=UTC()),
        ),
    ),
    (
        # Implicit UTC with time
        "2013-01-01T15:00/P1M",
        (
            datetime(2013, 1, 1, 15, 0, 0, tzinfo=UTC()),
            datetime(2013, 1, 31, 15, 0, 0, tzinfo=UTC()),
        ),
    ),
    (
        # TZ conversion
        "2013-01-01T17:00-05:00/P2W",
        (
            datetime(2013, 1, 1, 22, 0, 0, tzinfo=UTC()),
            datetime(2013, 1, 15, 22, 0, 0, tzinfo=UTC()),
        ),
    ),
    (
        # Date upgrade to midnight-midnight period
        "2013-01-01/P3D",
        (
            datetime(2013, 1, 1, 0, 0, 0, tzinfo=UTC()),
            datetime(2013, 1, 4, 0, 0, 0, 0, tzinfo=UTC()),
        ),
    ),
    (
        # Start/end with UTC
        "2013-01-01T12:00:00Z/2013-02-01T12:00:00Z",
        (
            datetime(2013, 1, 1, 12, 0, 0, tzinfo=UTC()),
            datetime(2013, 2, 1, 12, 0, 0, tzinfo=UTC()),
        ),
    ),
    (
        # Start/end with time upgrade
        "2013-01-01/2013-06-30",
        (
            datetime(2013, 1, 1, tzinfo=UTC()),
            datetime(2013, 6, 30, tzinfo=UTC()),
        ),
    ),
    (
        # Start/end with TZ conversion
        "2013-02-17T12:00:00-07:00/2013-02-28T15:00:00-07:00",
        (
            datetime(2013, 2, 17, 19, 0, 0, tzinfo=UTC()),
            datetime(2013, 2, 28, 22, 0, 0, tzinfo=UTC()),
        ),
    ),
    # Resolution expansion for single date(time)
    (
        # Second with UTC
        "2013-01-01T12:30:45Z",
        (
            datetime(2013, 1, 1, 12, 30, 45, tzinfo=UTC()),
            datetime(2013, 1, 1, 12, 30, 46, tzinfo=UTC()),
        ),
    ),
    (
        # Second with tz conversion
        "2013-01-01T12:30:45+02:00",
        (
            datetime(2013, 1, 1, 10, 30, 45, tzinfo=UTC()),
            datetime(2013, 1, 1, 10, 30, 46, tzinfo=UTC()),
        ),
    ),
    (
        # Second with implicit UTC
        "2013-01-01T12:30:45",
        (
            datetime(2013, 1, 1, 12, 30, 45, tzinfo=UTC()),
            datetime(2013, 1, 1, 12, 30, 46, tzinfo=UTC()),
        ),
    ),
    (
        # Minute with UTC
        "2013-01-01T12:30+00:00",
        (
            datetime(2013, 1, 1, 12, 30, tzinfo=UTC()),
            datetime(2013, 1, 1, 12, 31, tzinfo=UTC()),
        ),
    ),
    (
        # Minute with conversion
        "2013-01-01T12:30+04:00",
        (
            datetime(2013, 1, 1, 8, 30, tzinfo=UTC()),
            datetime(2013, 1, 1, 8, 31, tzinfo=UTC()),
        ),
    ),
    (
        # Minute with implicit UTC
        "2013-01-01T12:30",
        (
            datetime(2013, 1, 1, 12, 30, tzinfo=UTC()),
            datetime(2013, 1, 1, 12, 31, tzinfo=UTC()),
        ),
    ),
    (
        # Hour, explicit UTC
        "2013-01-01T12Z",
        (
            datetime(2013, 1, 1, 12, tzinfo=UTC()),
            datetime(2013, 1, 1, 13, tzinfo=UTC()),
        ),
    ),
    (
        # Hour with offset
        "2013-01-01T12-07:00",
        (
            datetime(2013, 1, 1, 19, tzinfo=UTC()),
            datetime(2013, 1, 1, 20, tzinfo=UTC()),
        ),
    ),
    (
        # Hour with implicit UTC
        "2013-01-01T12",
        (
            datetime(2013, 1, 1, 12, tzinfo=UTC()),
            datetime(2013, 1, 1, 13, tzinfo=UTC()),
        ),
    ),
    (
        # Interval with trailing zero fractional seconds should
        # be accepted.
        "2013-01-01T12:00:00.0/2013-01-01T12:30:00.000000",
        (
            datetime(2013, 1, 1, 12, tzinfo=UTC()),
            datetime(2013, 1, 1, 12, 30, tzinfo=UTC()),
        ),
    ),
])
def test_isointerval(value, expected):
    assert inputs.iso8601interval(value) == expected


def test_invalid_isointerval_error():
    with pytest.raises(ValueError):
        inputs.iso8601interval('2013-01-01/blah')


@pytest.mark.parametrize('interval', [
    '2013-01T14:',
    '',
    'asdf',
    '01/01/2013',
])
def test_bad_isointervals(interval):
    with pytest.raises(ValueError):
        inputs.iso8601interval(interval)
