import datetime

from django.utils.encoding import force_str
from django.utils.translation import ugettext_lazy as _
from django.forms.utils import from_current_timezone, to_current_timezone
from django.forms.fields import BaseTemporalField
from django.forms.widgets import DateTimeInput


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
