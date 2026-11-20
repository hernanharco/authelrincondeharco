"""
Migraciones idempotentes para bases de datos ya existentes.

`Base.metadata.create_all` (ver `main.py`) crea tablas que faltan, pero NO
agrega columnas a tablas que ya existen. Por eso las columnas nuevas de
`users` se agregan acá: detectar y agregar sólo lo que falta, de modo que
reejecutar en cada arranque sea seguro y no toque las filas existentes.

No reemplaza a Alembic (`entrypoint.sh` intenta `alembic upgrade head` y hoy
no está configurado); es la red de seguridad para que un deploy no arranque
con un modelo que pide columnas inexistentes.
"""

import logging
from typing import List, Sequence, Tuple

from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncConnection

logger = logging.getLogger("authCore.migrations")

USERS_TABLE = "users"

# (columna, tipo DDL). Agregar acá las columnas nuevas de `users`.
USER_COLUMNS: Sequence[Tuple[str, str]] = (
    ("request_country", "VARCHAR(2)"),
    ("request_city", "VARCHAR(128)"),
    ("request_region", "VARCHAR(128)"),
)


def _existing_columns(sync_conn: Connection, table: str) -> List[str]:
    inspector = inspect(sync_conn)
    if table not in inspector.get_table_names():
        return []
    return [column["name"] for column in inspector.get_columns(table)]


def _sync_apply(sync_conn: Connection) -> List[str]:
    existing = set(_existing_columns(sync_conn, USERS_TABLE))
    if not existing:
        # Sin tabla no hay nada que migrar: create_all la crea completa.
        return []

    added: List[str] = []
    for column, ddl_type in USER_COLUMNS:
        if column in existing:
            continue
        sync_conn.execute(
            text(f"ALTER TABLE {USERS_TABLE} ADD COLUMN {column} {ddl_type}")
        )
        added.append(column)
    return added


async def apply_idempotent_migrations(conn: AsyncConnection) -> List[str]:
    """
    Agrega las columnas faltantes de `users`.

    Returns:
        Nombres de las columnas efectivamente agregadas (vacío si no faltaba
        ninguna, que es el caso normal en cada arranque posterior al primero).
    """
    added = await conn.run_sync(_sync_apply)
    if added:
        logger.info("Columnas agregadas a %s: %s", USERS_TABLE, ", ".join(added))
    return added
