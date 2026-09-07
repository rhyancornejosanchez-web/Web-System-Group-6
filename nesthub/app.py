from flask import Flask
from models import init_db
from views import main_bp

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'apartment-mgmt-secret-2024'
    app.register_blueprint(main_bp)
    init_db()
    from seed import seed_data
    seed_data()
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)