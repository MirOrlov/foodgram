
# Foodgram - Кулинарный онлайн-журнал  

## Описание проекта  
Foodgram — это платформа для публикации рецептов с возможностью подписки на авторов, создания списка покупок и добавления рецептов в избранное.  

🚀 **Работающий сайт**: [https://MirOrlov](https://MirOrlov)

👨‍💻 **Автор**: [Ваше ФИО](https://github.com/MirOrlov)  

## Технологический стек  

### Серверная часть:  
- Python 3.10  
- Django 4.2  
- Django REST Framework  
- PostgreSQL  
- Gunicorn  
- Nginx  

### Клиентская часть:  
- React  
- JavaScript  
- HTML/CSS  

### Инфраструктура:  
- Docker  
- Docker-compose  
- GitHub Actions (CI/CD)  

## Развертывание с Docker  

1. Клонируйте репозиторий:  
   ```bash  
   git clone https://github.com/MirOrlov/foodgram  
   ```  

2. Перейдите в папку `infra`:  
   ```bash  
   cd foodgram/infra  
   ```  

3. Создайте файл `.env` на основе примера `example.env`:  
   ```bash  
   cp example.env .env  
   ```  
   Пример содержимого `example.env`:  
   ```  
   DB_ENGINE=django.db.backends.postgresql  
   DB_NAME=postgres  
   POSTGRES_USER=postgres  
   POSTGRES_PASSWORD=postgres  
   DB_HOST=db  
   DB_PORT=5432  
   SECRET_KEY=your-secret-key  
   ```  

4. Запустите контейнеры:  
   ```bash  
   docker-compose up -d --build  
   ```  

5. Выполните миграции:  
   ```bash  
   docker-compose exec backend python manage.py migrate  
   ```  

6. Создайте суперпользователя:  
   ```bash  
   docker-compose exec backend python manage.py createsuperuser  
   ```  

7. Соберите статику:  
   ```bash  
   docker-compose exec backend python manage.py collectstatic --no-input  
   ```  

8. Импортируйте фикстуры (если необходимо):  
   ```bash  
   docker-compose exec backend python manage.py loaddata fixtures.json  
   ```  

9. Сервер будет доступен по адресу: [http://clowerlover.redirectme.net](http://clowerlover.redirectme.net)  

## Локальное развертывание без Docker  

1. Клонируйте репозиторий:  
   ```bash  
   git clone https://github.com/MirOrlov/foodgram  
   ```  

2. Перейдите в папку проекта:  
   ```bash  
   cd foodgram/backend  
   ```  

3. Создайте и активируйте виртуальное окружение:  
   ```bash  
   python -m venv venv  
   source venv/bin/activate  # для Linux/MacOS  
   venv\Scripts\activate     # для Windows  
   ```  

4. Установите зависимости:  
   ```bash  
   pip install -r requirements.txt  
   ```  

5. Создайте файл `.env` (см. пример выше).  

6. Выполните миграции:  
   ```bash  
   python manage.py migrate  
   ```  

7. Создайте суперпользователя:  
   ```bash  
   python manage.py createsuperuser  
   ```  

8. Импортируйте фикстуры:  
   ```bash  
   python manage.py loaddata fixtures.json  
   ```  

9. Запустите сервер:  
   ```bash  
   python manage.py runserver  
   ```  

10. Сервер будет доступен по адресу: [http://127.0.0.1:8000](http://127.0.0.1:8000)  

## Документация API  
📚 Полная документация API доступна после запуска сервера:  
- Для Docker: [http://localhost/api/docs/](http://localhost/api/docs/)  
- Для локального развертывания: [http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/)  

## Контакты  
📧 Email: [test.email@example.com](mailto:test.email@example.com)  
🔗 GitHub: [https://github.com/MorOrlov](https://github.com/MorOrlov)  
