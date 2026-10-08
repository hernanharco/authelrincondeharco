from sqlalchemy.orm import declarative_base

Base = declarative_base()

# ── Registro de modelos en Base.metadata ────────────────────────
# Los modelos NO se importan aquí para evitar circular imports.
# Se importan en app/models/__init__.py que a su vez es importado
# en main.py antes de create_all().
