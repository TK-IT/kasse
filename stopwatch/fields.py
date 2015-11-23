import datetime

from django.core.exceptions import ValidationError
from django.utils.encoding import force_str, force_text
from django.utils.translation import ugettext_lazy as _
from django.utils.dateparse import parse_duration
from django.forms.utils import from_current_timezone, to_current_timezone
from django.forms.fields import BaseTemporalField, Field
from django.forms.widgets import DateTimeInput, Textarea


class DateTimeDefaultTodayField(BaseTemporalField):
    widget = DateTimeInput
    input_formats = (
        '%H:%M:%S',
        '%H:%M:%S.%f',
        '%H:%M',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M:%S.%f',
        '%Y-%m-%d %H:%M',
        '%d.%m.%Y %H:%M:%S',
        '%d.%m.%Y %H:%M:%S.%f',
        '%d.%m.%Y %H:%M',
    )
    default_error_messages = {
        'invalid': _('Enter a valid date/time.'),
    }

    def widget_attrs(self, widget):
        attrs = super(DateTimeDefaultTodayField, self).widget_attrs(widget)
        now = datetime.datetime.now().replace(tzinfo=None)
        date = now.date()
        time = datetime.time(hour=21, minute=0)
        d = datetime.datetime.combine(date, time)
        if now < d:
            date = date - datetime.timedelta(1)
            d = datetime.datetime.combine(date, time)
        attrs.update({'placeholder': d.strftime('f.eks. %Y-%m-%d %H:%M')})
        return attrs

    def prepare_value(self, value):
        if isinstance(value, datetime.datetime):
            value = to_current_timezone(value)
        return value

    def to_python(self, value):
        """
        Validates that the input can be converted to a datetime. Returns a
        Python datetime.datetime object.
        """
        if value in self.empty_values:
            return None
        if isinstance(value, datetime.datetime):
            return from_current_timezone(value)
        if isinstance(value, datetime.date):
            result = datetime.datetime(value.year, value.month, value.day)
            return from_current_timezone(result)
        result = super(DateTimeDefaultTodayField, self).to_python(value)
        return from_current_timezone(result)

    def strptime(self, value, format):
        dt = datetime.datetime.strptime(force_str(value), format)
        if '%Y' not in format:
            dt = datetime.datetime.combine(datetime.date.today(), dt.time())
        return dt


def duration_string(duration):
    try:
        duration = datetime.timedelta(seconds=duration.duration)
    except AttributeError:
        pass

    seconds = int(duration.total_seconds())
    microseconds = duration.microseconds

    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    if minutes or hours:
        string = '{:02d}:{:02d}' % (minutes, seconds)
    else:
        string = '{}'.format(seconds)
    if hours:
        string = '{:02d}:{}' % (hours, string)
    if microseconds:
        string += '.{:06d}'.format(microseconds).rstrip('0')

    return string


class DurationListField(Field):
    widget = Textarea
    default_error_messages = {
        'invalid': _('Enter a valid duration.'),
        'invalid_list': _('Enter a list of values.'),
    }

    def prepare_value(self, value):
        """Used by BoundField to display the value in a form."""
        if isinstance(value, (list, tuple)):
            return '\n'.join(duration_string(v) for v in value)
        else:
            return value

    def to_python(self, value):
        if not value:
            return []
        elif not isinstance(value, (list, tuple)):
            value = force_text(value).split()
        r = []
        for val in value:
            d = parse_duration(val)
            if d is None:
                raise ValidationError(
                    self.error_messages['invalid'], code='invalid')
            r.append(d)
        return r

    def validate(self, value):
        return value

    def has_changed(self, initial, data):
        return tuple(initial) != tuple(data)
