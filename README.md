# Foodgram - кулинарный журнал 

## 📌 Основные функции
- 📝 Публикация рецептов с фото  
- ❤️ Избранное и подписки  
- 🛒 Генератор списка покупок  
- 🔍 Поиск по тегам/ингредиентам  

## 🛠 Технологии
| Компонент       | Технологии                          |
|----------------|-----------------------------------|
| **Backend**    | Python 3.10, Django 4.2, DRF, PostgreSQL |
| **Frontend**   | React 18, Redux Toolkit           |
| **Инфраструктура** | Docker, Nginx, GitHub Actions |

## 🚀 Запуск (Docker)
```bash
git clone https://github.com/yourname/foodgram.git && cd foodgram/infra
docker-compose up -d --build  # сборка
docker-compose exec backend python manage.py migrate  # миграции
docker-compose exec backend python manage.py createsuperuser  # админ