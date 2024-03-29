import sklearn_crfsuite
import spacy
import json
from spacy.gold import GoldParse
import os
import joblib

nlp = None
crf = None


def train(filePath):
    try:
        global crf
        global nlp
        if not filePath.lower().endswith('json'):
            return {'success': False, 'message': 'Training file should be in json format'}
        with open(filePath) as file:
            ent_data = json.load(file)
        dataset = [jsonToCrf(q, nlp) for q in ent_data['entity_examples']]
        X_train = [sent2features(s) for s in dataset]
        y_train = [sent2labels(s) for s in dataset]
        crf = sklearn_crfsuite.CRF(
            algorithm='lbfgs',
            c1=0.01,
            c2=0.01,
            max_iterations=100,
            all_possible_transitions=True
        )
        crf.fit(X_train, y_train)
        if (not os.path.exists("/opt/models/crfModel/")):
            os.mkdir("/opt/models/crfModel/")
        if (os.path.isfile("/opt/models/crfModel/classifier.pkl")):
            os.remove("/opt/models/crfModel/classifier.pkl")
        joblib.dump(crf, "/opt/models/crfModel/classifier.pkl")
        return {'success': True, 'message': 'Model Trained Successfully'}
    except Exception as ex:
        return {'success': False, 'message': 'Error while Training the model - ' + str(ex)}


def predict(utterance):
    try:
        global crf
        global nlp
        tagged = []
        finallist = []
        if len(utterance.split()) > 1:
            parsed = nlp(utterance)
            for i in range(len(parsed)):
                tagged.append((str(parsed[i]), parsed[i].tag_))
            finallist.append(tagged)
            test = [sent2features(s) for s in finallist]
            if (os.path.isfile(
                    "/opt/models/crfModel/classifier.pkl") and crf is None):
                crf = joblib.load("/opt/models/crfModel/classifier.pkl")
                print("CRF MODEL LOADED")
                predicted = crf.predict(test)
                entityList = extractEntities(predicted[0], tagged)
                return {'success': True, 'entities': entityList}
            elif crf is not None:
                predicted = crf.predict(test)
                entityList = extractEntities(predicted[0], tagged)
                return {'success': True, 'entities': entityList}
            else:
                return {'success': False, 'entities': None}
        else:
            return {'success': False, 'entities': None}
    except Exception as ex:
        return {'success': False, 'entities': None}


def jsonToCrf(json_eg, spacy_nlp):
    global nlp
    entity_offsets = []
    doc = spacy_nlp(json_eg['text'])
    for i in json_eg['entities']:
        entity_offsets.append(tuple((i['start'], i['end'], i['entity'])))
    gold = GoldParse(doc, entities=entity_offsets)
    ents = [l[5] for l in gold.orig_annot]
    crf_format = [(doc[i].text, doc[i].tag_, ents[i]) for i in range(len(doc))]
    return crf_format


def word2features(sent, i):
    global nlp
    word = sent[i][0]
    postag = sent[i][1]
    features = {
        'bias': 1.0,
        'word.lower()': word.lower(),
        'word[-3:]': word[-3:],
        'word[-2:]': word[-2:],
        'word.isupper()': word.isupper(),
        'word.istitle()': word.istitle(),
        'word.isdigit()': word.isdigit(),
        'postag': postag,
        'postag[:2]': postag[:2],
    }
    if i > 0:
        word1 = sent[i - 1][0]
        postag1 = sent[i - 1][1]
        features.update({
            '-1:word.lower()': word1.lower(),
            '-1:word.istitle()': word1.istitle(),
            '-1:word.isupper()': word1.isupper(),
            '-1:postag': postag1,
            '-1:postag[:2]': postag1[:2],
        })
    else:
        features['BOS'] = True

    if i < len(sent) - 1:
        word1 = sent[i + 1][0]
        postag1 = sent[i + 1][1]
        features.update({
            '+1:word.lower()': word1.lower(),
            '+1:word.istitle()': word1.istitle(),
            '+1:word.isupper()': word1.isupper(),
            '+1:postag': postag1,
            '+1:postag[:2]': postag1[:2],
        })
    else:
        features['EOS'] = True

    return features


def sent2features(sent):
    return [word2features(sent, i) for i in range(len(sent))]


def sent2labels(sent):
    return [label for token, postag, label in sent]


def extractEntities(predicted, tagged):
    global nlp
    rslt = {}
    label = ''
    for i in range(len(predicted)):
        if predicted[i].startswith('U-'):
            label = tagged[i][0]
            try:
                rslt[predicted[i][2:]].append(label)
            except:
                rslt[predicted[i][2:]] = [label]
            label = ''
            continue
        if predicted[i].startswith('B-'):
            label += tagged[i][0] + " "
        if predicted[i].startswith('I-'):
            label += tagged[i][0] + " "
        if predicted[i].startswith('L-'):
            label += tagged[i][0]
            try:
                rslt[predicted[i][2:]].append(label)
            except:
                rslt[predicted[i][2:]] = [label]
            label = ''
            continue
    return rslt


def set_nlp(nlp_load):
    global nlp
    nlp = nlp_load


