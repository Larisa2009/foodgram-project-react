import re

from django.core.exceptions import ValidationError


REGEX_SLUG = re.compile(r'^[-a-zA-Z0-9_]+$')


def validate_slug(value):
    if not REGEX_SLUG.fullmatch(value):
        raise ValidationError(
            'Можно использовать только буквы, цифры')
    return value
