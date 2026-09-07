import os
import webbrowser
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
    # WERKZUEG_RUN_MAIN ensures the browser only opens once and not on Flask debug reloads
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        webbrowser.open("http://127.0.0.1:5000/login")

    app.run(debug=True)