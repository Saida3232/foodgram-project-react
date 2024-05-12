import csv

from django.core.management.base import BaseCommand

from foodgram.models import Ingredient,Tag


class Command(BaseCommand):
    help = 'load ingredients from csv'

    def handle(self, *args, **options):
        file = 'data/ingredients.csv'
        with open(file, newline='', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file, delimiter=',')
            for row in csv_reader:
                id = row['id']
                name = row['name']
                measurement_unit = row['measurement_unit']
                ingredient = Ingredient(id=id, name=name, measurement_unit=measurement_unit)
                ingredient.save()

    def handle(self, *args, **options):
        file = 'data/recipes_tag.csv'
        with open(file, newline='', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file, delimiter=',')
            for row in csv_reader:
                name = row['name']
                slug = row['slug']
                color = row['color']
                tag = Tag(name=name, slug=slug, color=color)
                tag.save()
    
