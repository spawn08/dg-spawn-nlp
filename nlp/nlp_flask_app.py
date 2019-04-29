import spacy
from flask import Flask, request, jsonify, Response, json
from functools import wraps

from time import gmtime, strftime
from nlp import crf_entity
import requests

app = Flask(__name__)
nlp = spacy.load("en_core_web_md")
crf_entity.set_nlp(nlp)
cache = {}

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


@app.route('/entity_extract', methods=['GET'])
@requires_auth
def get_ner_test():
    global cache
    entities = []
    labels = {}
    query = request.args.get('q')
    if (cache.get(query) is not None):
        return jsonify(cache.get(query))
    res = requests.get(
            "https://spawnai.com/api/classify?q={query}&model=spawn&project=spawn_wiki".format(query=query))
    print(res.json())
    ml_response = res.json()

    if query is not None:
        doc = nlp(query)
        if len(doc.ents):
            ent = doc.ents[0]
            labels['tag'] = ent.label_
            labels['entity'] = ent.text
            entities.append(labels)
            labels = {}
            print(ent.text, ent.label_)

            ml_response['entities'] = entities
            cache[query] = ml_response
        else:
            crf_ent = crf_entity.predict(query)
            print(crf_ent)
            if(crf_ent.get('entities') is not None and len(list(crf_ent.get('entities').keys())) > 0 and len(list(crf_ent.get('entities').values())[0]) > 0  ):
                entities = [{'tag': list(crf_ent.get('entities').keys())[0], 'value': list(crf_ent.get('entities').values())[0]}]
            ml_response['entities'] = entities
            cache[query] = ml_response
            return jsonify(ml_response)
    else:
        entities = [{'tag': '', 'entity': ''}]
        ml_response['entities'] = entities
        cache[query] = ml_response
        return jsonify(ml_response)
    return jsonify(ml_response)
