![Deploy badge](https://github.com/Saida3232/foodgram-project-react/actions/workflows/main.yml/badge.svg)

#  О проекте
Фудграм» — сайт, на котором пользователи могут публиковать рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Пользователям сайта также будет доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд. 

# Стек
- Python 3.9
- Django 3.2.3
- Django REST framework 3.12.4
- JavaScript
- Nginx
- Docker compose

# Запуск проекта
Убедитесь, что у вас установлен docker и docker-compose последних версий.

Создайте .env файл в корне каталога. Укажите в нем данные для запуска, например:
```.env
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password
DB_NAME=foodgram
DEBUG=True
SECRET_KEY=some_secret_key
ALLOWED_HOST=your_host
DB_HOST=db
DB_PORT=5432
```
2. Для запуска выполните команду:
```
docker compose -f docker-compose.production.yml up
```
(для запуска в фоне, т.е. без вывода в консоль можно использовать флаг -d)
4. Дожидаемся старта.

Для остановки используйте команду:
```
docker compose -f docker-compose.production.yml down
```

# Автор
[Саида](https://github.com/Saida3232)