# Paso 1: Abrir la configuración de VS Code
1. Presiona Ctrl + , (coma) para abrir los Settings.

2. En la barra de búsqueda superior, escribe: files:exclude.

# Paso 2: Añadir los patrones de ocultación
Haz clic en el botón Add Pattern y añade estos dos:

1. **/__pycache__: Esto ocultará todas las carpetas de caché en cualquier nivel de tu proyecto.

2. **/__init__.py: Esto ocultará los archivos de inicialización.

**Nota para tu aprendizaje:** Aunque los ocultes de la vista, siguen ahí. No los borres, ya que sin los __init__.py, FastAPI podría tener problemas para encontrar tus rutas en app.api.v1.endpoints.
_________
**Bonus: Hacerlo solo para este proyecto**

Si prefieres que esto solo pase en este SaaS y no en otros proyectos, puedes crear un archivo en la raíz de tu carpeta llamado .vscode/settings.json y pegar esto:

```JSON
{
  "files.exclude": {
    "**/__pycache__": true,
    "**/__init__.py": true
  }
}
```

Esto es muy útil para mantener tus principios de desarrollo optimizado y rapidez de iteración, permitiéndote concentrarte solo en los archivos que realmente editas, como auth.py y users.py.