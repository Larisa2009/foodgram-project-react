import json

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient, Tag


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        with open(f'{settings.BASE_DIR}/data/ingredients.json', 'r') as file:
            ingredients = json.loads(file.read())
            Ingredient.objects.bulk_create(
                Ingredient(**ingredient) for ingredient in ingredients)

        with open(f'{settings.BASE_DIR}/data/tags.json', 'r') as file:
            tags = json.loads(file.read())
            Tag.objects.bulk_create(
                Tag(**tag) for tag in tags)

        self.stdout.write('Данные загружены')
