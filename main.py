from flask import Flask
from routes.movfinanceira_routes import movfinanceira_route

app = Flask(__name__)

app.register_blueprint(movfinanceira_route)

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5002,
        debug=True
    )