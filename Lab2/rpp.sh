#!/bin/bash

DB_NAME="lab2"
DB_USER="postgres"
DB_PASS="postgres"
DB_HOST="localhost"
DB_PORT="5432"
MIGRATIONS_DIR="./"  
export PATH='C:\Program Files\PostgreSQL\16\bin'

# Функция для выполнения SQL-запросов из файла
run_sql() {
    local file="$1"
    psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -f "$file" 
    return $?
}

# Функция для выполнения SQL-запроса из строки
run_sql_c() {
    local query="$1"
    psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "$query"
    return $?
}

run_sql_c "CREATE TABLE IF NOT EXISTS migrations (
    id SERIAL PRIMARY KEY,
    migration_name VARCHAR(255) UNIQUE NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"

applied_migrations=$(run_sql_c "SELECT migration_name FROM migrations;")

# Применение новых миграций
for file in "$MIGRATIONS_DIR"/*.sql; do
    migration_name=${file:3:-4}

    # Проверка, была ли миграция уже применена
    if [[ "$applied_migrations" == *"$migration_name"* ]]; then
        echo "Миграция '$migration_name' уже применена."
    else
        echo "Применение миграции '$migration_name'..."

        # Пробуем выполнить миграцию и проверяем результат
        if run_sql "$file"; then
            # Запись информации о примененной миграции
            if run_sql_c "INSERT INTO migrations (migration_name) VALUES ('$migration_name');"; then
                echo "Миграция '$migration_name' успешно применена."
            else
                echo "Ошибка при записи миграции '$migration_name' в таблицу migrations."
            fi
        else
            echo "Ошибка при применении миграции '$migration_name'."
        fi
    fi
done
