from csv import reader as csv_reader
from django.core.management import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    """Команда для импорта данных об ингредиентах из CSV файла"""

    help_text = 'Загрузка списка ингредиентов в базу данных'

    def execute_command(self):
        """Основная логика выполнения команды"""
        csv_file_path = 'data/ingredients.csv'

        try:
            with open(csv_file_path, mode='r', encoding='UTF-8') as file:
                food_items = self._prepare_food_items(file)
                saved_count = self._save_to_database(food_items)

                self._show_success_message(saved_count, csv_file_path)

        except FileNotFoundError:
            self._show_error_message(f'Отсутствует файл данных: {csv_file_path}')
        except Exception as error:
            self._show_error_message(f'Произошла ошибка: {error}')

    def _prepare_food_items(self, file_object):
        """Подготовка объектов модели из CSV файла"""
        return [
            Ingredient(
                name=row[0].strip(),
                measurement_unit=row[1].strip()
            )
            for row in csv_reader(file_object)
        ]

    def _save_to_database(self, items):
        """Сохранение объектов в базу данных"""
        return len(Ingredient.objects.bulk_create(
            items,
            ignore_conflicts=True
        ))

    def _show_success_message(self, count, path):
        """Вывод сообщения об успешном выполнении"""
        self.stdout.write(
            self.style.SUCCESS(
                f'Загружено {count} записей из файла {path}'
            )
        )

    def _show_error_message(self, text):
        """Вывод сообщения об ошибке"""
        self.stdout.write(
            self.style.ERROR(text)
        )

    def handle(self, *args, **options):
        """Точка входа для выполнения команды"""
        self.execute_command()