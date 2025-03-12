# CurrencyConverter



## Установка и запуск
### Способ 1. Native
#### 1. Клонируйте репозиторий и создайте виртуальное окружение
```bash
python -m venv venv
venv\Scripts\activate.ps1
```

#### 2. Зависимости
```bash
pip install -r requirements.txt
```

#### 3. Запуск сервера
```bash
fastapi dev main.py
```

#### 4. Консольная команда для импорта данных с ЕЦБ в бд
```bash
python import_rates.py
```

#### 5. Откройте приложение в браузере
Форма для приложения: (http://127.0.0.1:8000/)
Документация API: (http://127.0.0.1:8000/docs)

### Способ 2. Docker

#### 1. Клонируйте репозиторий

#### 2. Сбилдите контейнер и запустите его
```bash
docker-compose build && docker-compose up -d
```
#### 3. Консольная команда для импорта данных с ЕЦБ в бд(Мы запускали в DockerDesktop, в Exec)
```bash
docker exec <containerid> python import_rates.py
```
#### 4. Откройте приложение в браузере
Форма для приложения: (http://127.0.0.1:8000/)
Документация API: (http://127.0.0.1:8000/docs)


------
Вводные данные: 


Котировки ecb для разных валют — https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml 


Основное задание:


1.	~~Написать консольную команду для импорта данных из этого источника - https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml~~ - сделано
2.	~~Сделать API для получения списка импортированных котировок, API для удаления и редактирования.~~ - сделано
3.	~~Сделать API конвертера валют. Если нет прямой конвертации, то пытаться конвертировать через другую валюту (кросс-курс).~~ - сделано
4.	~~Калькулятор - выбираем From, To, Amount и видим конвертированную сумму. (минимум красоты, максимум функционала, просто форма)~~ - сделано


Требования к выполнению:


1.	~~Весь проект должен быть в docker контейнерах~~ - кое-как сделано
2.	~~Code coverage 100% (покрыть тестами)~~ - кое-как сделано
3.	~~Автоматизация сборок~~ и тестов 



Форма выполнения тестового задания:
Ответ в виде репозитория на github/bitbucket с инструкцией (readme) по запуску.


------
https://fastapi.tiangolo.com/tutorial
https://sqlmodel.tiangolo.com/tutorial/
https://youtu.be/GONyd0CUrPc
https://docs.python.org/3/library/xml.etree.elementtree.html
https://jinja.palletsprojects.com/en/stable/templates/





