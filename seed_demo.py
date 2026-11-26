"""Совместимость с запуском python seed_demo.py имя_пользователя."""
import os
import sys

from django.core.management import execute_from_command_line


if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    args = ['--username', *sys.argv[1:]] if sys.argv[1:] else []
    execute_from_command_line([sys.argv[0], 'seed_demo', *args])
