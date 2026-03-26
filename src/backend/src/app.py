from flask import Flask
from flask_cors import CORS
from routes.signature_routes import bp
from routes.verify_routes import verify_bp
app = Flask(__name__)
CORS(app)

app.register_blueprint(bp)
app.register_blueprint(verify_bp)
if __name__ == "__main__":
    app.run(debug=True)
