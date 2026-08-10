from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS

# Instances partagées, initialisées dans create_app() via .init_app(app)
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()