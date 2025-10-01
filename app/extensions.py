from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Tạo các extension ở đây để tránh circular import
db = SQLAlchemy()
migrate = Migrate()
