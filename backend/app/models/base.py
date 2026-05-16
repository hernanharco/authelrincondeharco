from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Importamos los modelos aquí para que se registren en el objeto Base
# Asegúrate de que la ruta coincida con tus archivos reales
try:
    from app.models.user import User
except ImportError:
    pass

try:
    from app.models.company_profile import CompanyProfile
except ImportError:
    pass
