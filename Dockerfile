# Используем официальный образ Python
FROM python:3.13.1

# Копируем зависимости проекта
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем остальные файлы проекта
COPY . .

CMD ["fastapi", "run", "main.py", "--port", "80"]