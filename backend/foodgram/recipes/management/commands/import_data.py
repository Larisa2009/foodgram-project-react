import json

from recipes.models import Ingredient, Tag
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        with open(f'{settings.BASE_DIR}/data/ingredients.json', 'r') as file:
            ingredients = json.loads(file.read())
            Ingredient.objects.bulk_create(
                Ingredient(**x) for x in ingredients)
        with open(f'{settings.BASE_DIR}/data/tags.json', 'r') as file:
            tags = json.loads(file.read())
            Tag.objects.bulk_create(
                Tag(**x) for x in tags)
        self.stdout.write('Данные загружены')
