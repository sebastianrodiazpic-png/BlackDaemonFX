"""Capa de persistencia: configuración, modelos ORM, repositorio e informes.

- `database`: rutas, motor SQLite y migraciones ligeras.
- `models`: definicion de todas las tablas.
- `repository`: la API de acceso a datos que usa el resto del proyecto.
- `reporting`: exportacion del informe a Excel.

Toda escritura y lectura de produccion pasa por `repository`; los demas
modulos no acceden a las tablas directamente.
"""
