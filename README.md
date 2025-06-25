# Foodgram - Кулинарный журнал  

## О проекте  

Foodgram - это удобная платформа для любителей готовить, где можно:  
- Публиковать свои рецепты  
- Сохранять понравившиеся рецепты в избранное  
- Подписываться на других авторов  
- Создавать список покупок  
- Искать рецепты по категориям и тегам  

Техническая реализация:  
- Бэкенд на Django REST Framework  
- Фронтенд на React  
- База данных PostgreSQL  
- Развертывание в Docker-контейнерах 


## Используемые технологии  

**Серверная часть:**  
- Python 3.10  
- Django 4.2  
- Django REST Framework  
- PostgreSQL  
- Gunicorn  
- Nginx  

**Клиентская часть:**  
- React  
- JavaScript  
- HTML/CSS  

**Инфраструктура:**  
- Docker  
- Docker-compose  
- GitHub Actions (CI/CD)  

## Запуск (Docker)
```bash
git clone https://github.com/MirOrlov/foodgram.git && cd foodgram/infra
docker-compose up -d --build  # сборка
docker-compose exec backend python manage.py migrate  # миграции
docker-compose exec backend python manage.py createsuperuser  # админ