import csv
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загружаем данные из json'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='data/ingredients.csv',
            help='Путь до JSON файла'
        )

    def handle(self, *args, **options):
        file_path = options['file']

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                ingredients = [
                    Ingredient(
                        name=item[0].strip(),
                        measurement_unit=item[1].strip()
                    )
                    for item in csv.reader(f)
                ]
                created = Ingredient.objects.bulk_create(
                    ingredients,
                    ignore_conflicts=True
                )

            self.stdout.write(
                self.style.SUCCESS(f'Успешно загруженно {len(created)} ингредиентов {file_path}')
            )

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Файл не найден: {file_path}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка: {e}'))