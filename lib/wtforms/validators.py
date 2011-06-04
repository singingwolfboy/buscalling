import re


__all__ = (
    'Email', 'email', 'EqualTo', 'equal_to', 'IPAddress', 'ip_address',
    'Length', 'length', 'NumberRange', 'number_range', 'Optional', 'optional',
    'Required', 'required', 'Regexp', 'regexp', 'URL', 'url', 'AnyOf',
    'any_of', 'NoneOf', 'none_of'
)


class ValidationError(ValueError):
    """
    Raised when a validator fails to validate its input.
    """
    def __init__(self, message=u'', *args, **kwargs):
        ValueError.__init__(self, message, *args, **kwargs)


class StopValidation(Exception):
    """
    Causes the validation chain to stop.

    If StopValidation is raised, no more validators in the validation chain are
    called. If raised with a message, the message will be added to the errors
    list.
    """
    def __init__(self, message=u'', *args, **kwargs):
        Exception.__init__(self, message, *args, **kwargs)


class EqualTo(object):
    """
    Compares the values of two fields.

    :param fieldname:
        The name of the other field to compare to.
    :param message:
        Dict of error messages to raise in case of validation errors. Can be
        interpolated with `%(other_label)s` and `%(other_name)s` to provide a
        more helpful error. Relevant keys are "invalid" and "invalid-name".
    """
    def __init__(self, fieldname, messages={}):
        self.fieldname = fieldname
        self.messages = {
            u'invalid': u'Field must be equal to %(other_name)s.',
            u'invalid-name': u"Invalid field name '%s'." % self.fieldname,
        }
        self.messages.update(messages)

    def __call__(self, form, field):
        try:
            other = form[self.fieldname]
        except KeyError:
            raise ValidationError(self.messages['invalid-name'])
        if field.data != other.data:
            d = {
                'other_label': hasattr(other, 'label') and other.label.text or self.fieldname,
                'other_name': self.fieldname
            }
            raise ValidationError(self.messages['invalid'] % d)


class Length(object):
    """
    Validates the length of a string.

    :param min:
        The minimum required length of the string. If not provided, minimum
        length will not be checked.
    :param max:
        The maximum length of the string. If not provided, maximum length
        will not be checked.
    :param messages:
        Dict of error message to raise in case of validation errors. Relevant keys
        are "singular", "plural", "min", "max", and "between". Can be interpolated
        using `%(min)d` and `%(max)d` if desired.
        Useful defaults are provided depending on the existence of min and max.
    """
    def __init__(self, min=None, max=None, messages={}):
        assert not (min is None and max is None), 'At least one of `min` or `max` must be specified.'
        if (min is not None and max is not None):
            assert max > min, '`min` cannot be more than `max`.'
        self.min = min
        self.max = max
        self.messages = {
            u'singular':u"character",
            u'plural':  u"characters",
            u'min':     u"Field must be at least %(min)d %(noun)s long.",
            u'max':     u"Field cannot be longer than %(max)d %(noun)s.",
            u'between': u"Field must be between %(min)d and %(max)d %(noun)s long.",
        }
        self.messages.update(messages)

    def __call__(self, form, field):
        interpolate = {u'min': self.min, u'max': self.max,
                u'noun': self.messages['plural']}
        l = field.data and len(field.data) or 0
        if self.min is not None and self.max is not None:
            if not (self.min <= l <= self.max):
                raise ValidationError(self.messages[u'between'] % interpolate)
        elif self.min is not None:
            if self.min == 1:
                interpolate[u'noun'] = self.messages[u'singular']
            if not (self.min <= l):
                raise ValidationError(self.messages[u'min'] % interpolate)
        elif self.max is not None:
            if self.max == 1:
                interpolate[u'noun'] = self.messages[u'singular']
            if not (l <= self.max):
                raise ValidationError(self.messages[u'max'] % interpolate)

class NumberRange(object):
    """
    Validates that a number is of a minimum and/or maximum value, inclusive.
    This will work with any comparable number type, such as floats and
    decimals, not just integers.

    :param min:
        The minimum required value of the number. If not provided, minimum
        value will not be checked.
    :param max:
        The maximum value of the number. If not provided, maximum value
        will not be checked.
    :param messages:
        Dict of error messageto raise in case of validation errors. Relevant keys
        are "min", "max", and "between". Can be
        interpolated using `%(min)s` and `%(max)s` if desired. Useful defaults
        are provided depending on the existence of min and max.
    """
    def __init__(self, min=None, max=None, messages={}):
        self.min = min
        self.max = max
        self.messages = {
            u'min': u"Number must be greater than %(min)s.",
            u'max': u"Number must be less than %(max)s.",
            u'between': u"Number must be between %(min)s and %(max)s.",
        }
        self.messages.update(messages)

    def __call__(self, form, field):
        data = field.data
        interpolate = {u'min': self.min, u'max': self.max}
        if data is None:
            raise ValidationError(self.messages[u'between'] % interpolate)
        if self.min is not None and self.max is not None:
            if not (self.min <= data <= self.max):
                raise ValidationError(self.messages[u'between'] % interpolate)
        elif self.min is not None:
            if not self.min <= data:
                raise ValidationError(self.messages[u'min'] % interpolate)
        elif self.max is not None:
            if not data <= self.max:
                raise ValidationError(self.messages[u'max'] % interpolate)


class Optional(object):
    """
    Allows empty input and stops the validation chain from continuing.

    If input is empty, also removes prior errors (such as processing errors)
    from the field.
    """
    field_flags = ('optional', )

    def __call__(self, form, field):
        if not field.raw_data or isinstance(field.raw_data[0], basestring) and not field.raw_data[0].strip():
            field.errors[:] = []
            raise StopValidation()


class Required(object):
    """
    Validates that the field contains data. This validator will stop the
    validation chain on error.

    :param messages:
        Error messages to raise in case of validation errors. Relevant key is
        "invalid".
    """
    field_flags = ('required', )

    def __init__(self, messages={}):
        self.messages = {
            u'invalid': u"This field is required.",
        }
        self.messages.update(messages)

    def __call__(self, form, field):
        if not field.data or isinstance(field.data, basestring) and not field.data.strip():
            field.errors[:] = []
            raise StopValidation(self.messages[u'invalid'])


class Regexp(object):
    """
    Validates the field against a user provided regexp.

    :param regex:
        The regular expression string to use. Can also be a compiled regular
        expression pattern.
    :param flags:
        The regexp flags to use, for example re.IGNORECASE. Ignored if
        `regex` is not a string.
    :param messages:
        Dict of error messages to raise in case of validation errors. Relevant
        key is "invalid".
    """
    def __init__(self, regex, flags=0, messages={}):
        if isinstance(regex, basestring):
            regex = re.compile(regex, flags)
        self.regex = regex
        self.messages = {
            u'invalid': u"Invalid input.",
        }
        self.messages.update(messages)

    def __call__(self, form, field):
        if not self.regex.match(field.data or u''):
            raise ValidationError(self.messages[u'invalid'])


class Email(Regexp):
    """
    Validates an email address. Note that this uses a very primitive regular
    expression and should only be used in instances where you later verify by
    other means, such as email activation or lookups.

    :param messages:
        Dict of error messages to raise in case of validation errors. Relevant
        key is "invalid".
    """
    def __init__(self, messages={}):
        default_messages = {
            u'invalid': u'Invalid email address.',
        }
        default_messages.update(messages)
        super(Email, self).__init__(r'^.+@[^.].*\.[a-z]{2,10}$', re.IGNORECASE, default_messages)


class IPAddress(object):
    """
    Validates an IP(v4) address.

    :param messages:
        A dict of error messages to raise in case of validation errors. Relevant
        keys are "invalid", "four-octets", and "int-range".
    """
    def __init__(self, messages={}):
        self.messages = {
            u"invalid": u"Invalid IP address.",
            u"four-octets": u"IP address must contain exactly four integers, separated by dots.",
            u"int-range": u"IP address must contain four integers between 0 and 255.",
        }
        self.messages.update(messages)

    def __call__(self, form, field):
        try:
            octets = field.data.split('.')
        except AttributeError:
            raise ValidationError(self.messages['invalid'])
        if len(octets) != 4:
            raise ValidationError(self.messages['four-octets'])
        try:
            octets = [int(o) for o in octets]
        except ValueError:
            raise ValidationError(self.messages['four-octets'])
        for o in octets:
            if o < 0 or o > 255:
                raise ValidationError(self.messages['int-range'])


class URL(Regexp):
    """
    Simple regexp based url validation. Much like the email validator, you
    probably want to validate the url later by other means if the url must
    resolve.

    :param require_tld:
        If true, then the domain-name portion of the URL must contain a .tld
        suffix.  Set this to false if you want to allow domains like
        `localhost`.
    :param messages:
        Dict of error messages to raise in case of validation errors. Relevant
        key is "invalid".
    """
    def __init__(self, require_tld=True, messages={}):
        tld_part = (require_tld and ur'\.[a-z]{2,10}' or u'')
        regex = ur'^[a-z]+://([^/:]+%s|([0-9]{1,3}\.){3}[0-9]{1,3})(:[0-9]+)?(\/.*)?$' % tld_part
        default_messages = {
            u'invalid': u"Invalid URL.",
        }
        default_messages.update(messages)
        super(URL, self).__init__(regex, re.IGNORECASE, default_messages)


class AnyOf(object):
    """
    Compares the incoming data to a sequence of valid inputs.

    :param values:
        A sequence of valid inputs.
    :param messages:
        Dict of error messages to raise in case of validation errors. Relevant key
        is "invalid". `%(values)s` contains the list of values.
    :param values_formatter:
        Function used to format the list of values in the error message.
    """
    def __init__(self, values, messages={}, values_formatter=None):
        self.values = values
        self.messages = {
            u'invalid': u'Invalid value, must be one of: %(values)s.',
        }
        self.messages.update(messages)
        if values_formatter is None:
            values_formatter = lambda v: u', '.join(v)
        self.values_formatter = values_formatter

    def __call__(self, form, field):
        if field.data not in self.values:
            raise ValueError(self.messages[u'invalid'] % \
                    dict(values=self.values_formatter(self.values)))


class NoneOf(object):
    """
    Compares the incoming data to a sequence of invalid inputs.

    :param values:
        A sequence of invalid inputs.
    :param messages:
        Dict of error messages to raise in case of validation errors. Relevant key
        is "invalid". `%(values)s` contains the list of values.
    :param values_formatter:
        Function used to format the list of values in the error message.
    """
    def __init__(self, values, messages={}, values_formatter=None):
        self.values = values
        self.messages = {
            u'invalid': u"Invalid value, can't be any of: %(values)s.",
        }
        self.messages.update(messages)
        if values_formatter is None:
            values_formatter = lambda v: u', '.join(v)
        self.values_formatter = values_formatter

    def __call__(self, form, field):
        if field.data in self.values:
            raise ValueError(self.messages[u'invalid'] % \
                    dict(values=self.values_formatter(self.values)))


email = Email
equal_to = EqualTo
ip_address = IPAddress
length = Length
number_range = NumberRange
optional = Optional
required = Required
regexp = Regexp
url = URL
any_of = AnyOf
none_of = NoneOf
