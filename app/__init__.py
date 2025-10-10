from flask import Flask        # ✅ Flask ở đây
from app.extensions import db, migrate   # ✅ chỉ import db và migrate thôi

def create_app():
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object("config.Config")

    # Khởi tạo extension
    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        from app import models       # import models sau khi db đã init
        from app.views import bp      # import blueprint
        app.register_blueprint(bp)

    return app



