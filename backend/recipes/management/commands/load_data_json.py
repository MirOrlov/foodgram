import json
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загружаем данные из json'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='data/ingredients.json',
            help='Путь до JSON файла'
        )

    def handle(self, *args, **options):
        file_path = options['file']

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                ingredients = [
                    Ingredient(
                        name=item['name'].strip(),
                        measurement_unit=item['measurement_unit'].strip()
                    )
                    for item in data
                ]
                created = Ingredient.objects.bulk_create(
                    ingredients,
                    ignore_conflicts=True,
                    batch_size=1000
                )

            self.stdout.write(
                self.style.SUCCESS(f'Успешно загружено {len(created)}\
                                    ингредиентов {file_path}')
            )

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Файл не найден: {file_path}'))
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(
                f'Неправильный формат {file_path}'))
        except KeyError as e:
            self.stdout.write(self.style.ERROR(
                f'Пропущено обязательное поле: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка: {e}'))
