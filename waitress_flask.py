from nlp.nlp_flask_app import app
from waitress import serve

serve(app, host='localhost', port=8080)
