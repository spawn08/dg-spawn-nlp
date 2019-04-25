import spacy
from flask import Flask, request, jsonify, Response, json
from functools import wraps

from time import gmtime, strftime

app = Flask(__name__)
nlp = spacy.load("en_core_web_md")


def check_auth(username, password):
    return username == 'spawnai' and password == 'spawn1992'


def authenticate():
    message = {'message': 'You are not authorized user to access this url'}
    return Response(json.dumps(message), mimetype='application/json')


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth:
            return authenticate()

        elif not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)

    return decorated


@app.route('/entity', methods=['GET'])
@requires_auth
def get_ner():
    entities = []
    labels = {}
    query = request.args.get('q')
    if query is not None:
        doc = nlp(query)
        for ent in doc.ents:
            labels['tag'] = ent.label_
            labels['value'] = ent.text
            labels['timestamp']= strftime("%Y-%m-%dT%H:%M:%SZ", gmtime())
            entities.append(labels)
            labels = {}
            print(ent.text, ent.label_)
        if (len(entities) == 0):
            return jsonify([{'tag': '', 'value': query}])
    else:
        return jsonify([{'tag': '', 'value': query}])
    return jsonify(entities)

