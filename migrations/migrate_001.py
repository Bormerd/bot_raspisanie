"""Добавление ссылки на предыдущее занятие"""

import sys
from playhouse.migrate import MySQLMigrator
from core.models import DB


def migrate(migrator=None):
    """Добавление поля old_lesson"""
    # Убедитесь, что есть подключение
    if not DB.is_connection_usable():
        DB.connect()

    # Инициализация мигратора
    migrator = migrator or MySQLMigrator(DB)

    # Выполнение миграции за один запрос
    with DB.atomic():
        DB.execute_sql("""
            ALTER TABLE lesson
            ADD COLUMN old_lesson_id INT(11) NULL,
            ADD COLUMN arhiv TINYINT(1) DEFAULT 0,
            ADD CONSTRAINT fk_old_lesson
            FOREIGN KEY (old_lesson_id) REFERENCES lesson(id)
            ON DELETE CASCADE ON UPDATE CASCADE;
        """)

        print('Миграция завершена')


def rollback(migrator=None):
    """Удаление поля old_lesson"""
    # Убедитесь, что есть подключение
    if not DB.is_connection_usable():
        DB.connect()

    # Инициализация мигратора
    migrator = migrator or MySQLMigrator(DB)

    with DB.atomic():
        # Удаление внешнего ключа и столбца за один запрос
        DB.execute_sql("""
            ALTER TABLE lesson
            DROP FOREIGN KEY fk_old_lesson,
            DROP COLUMN old_lesson,
            DROP COLUMN arhiv;
        """)

        print('Откат миграции завершён')


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else None

    if action == "migrate":
        mysql_migrator = MySQLMigrator(DB)
        migrate(mysql_migrator)
    elif action == "rollback":
        mysql_migrator = MySQLMigrator(DB)
        rollback(mysql_migrator)
    else:
        print("Usage: py -m migrations.migrate_001 [migrate|rollback]")
