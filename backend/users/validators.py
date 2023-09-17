import re

from django.core.exceptions import ValidationError


REGEX_USERNAME = re.compile(r'^[\w.@+-]+\w')


def validate_username(value):
    if not REGEX_USERNAME.fullmatch(value):
        raise ValidationError(
            'Можно использовать только буквы, цифры и символы @.+-_".')
    return value
