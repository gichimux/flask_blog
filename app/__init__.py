from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap

bootstrap = Bootstrap()
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    #initialize flask extensions
    bootstrap.init_app(app)
    db.init_app(db)