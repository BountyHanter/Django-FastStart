from pathlib import Path

from django.core.management.utils import get_random_secret_key


env_path = Path(".env")

if not env_path.exists():
    raise FileNotFoundError(".env файл не найден")


content = env_path.read_text(encoding="utf-8").splitlines()

new_secret = f"SECRET_KEY=django-insecure-{get_random_secret_key()}"

updated = False
new_lines = []

for line in content:
    if line.startswith("SECRET_KEY="):
        new_lines.append(new_secret)
        updated = True
    else:
        new_lines.append(line)

if not updated:
    raise ValueError("Строка SECRET_KEY= не найдена в .env")

env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

print("SECRET_KEY успешно обновлён")