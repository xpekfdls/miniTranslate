from textblob import TextBlob, Word
from flask import Flask, render_template, request, session, jsonify, redirect
import json
from flask_login import LoginManager, login_required, login_user, current_user, logout_user
from User import User
from bs4 import BeautifulSoup
from utils.dic_daum import get_meaning_all
import asyncio

USERS = {
    "asdf": User("asdf", passwd_hash='asdf'),
    "user02": User("user02", passwd_hash='user_02'),
    "user03": User("user03", passwd_hash='user_03'),
}

except_words =  ["a", "the", "to", "where", "an", "which", "or", "how", 
    "can", "should", "would", "shall", "as", "like", "you", "for", "in", "of",
    "your", "I", "will", "from", "we", "they", "us", "our", "he", "she", "on", "not", 
    "be", "with", "without", "it", "his", "him", "her", "them" ,"out",
    "this", "that", "those", "these", "what", "do", "is", "are", "than", "if", "'s",
    "and", "at", "one", "thing", "two", "just"
    ]

app = Flask(__name__)
app.config['SECRET_KEY'] = "ut4u--nj0ai_0$o4q)6h4rrvgw6_qo246juzrzj%yz4rv8cvs^"
login_manager = LoginManager()
login_manager.init_app(app)

@app.route("/api/auth_func", methods=['POST'])
@login_required
def auth_func():
    user = current_user
    json_res = {'ok': True, 'msg': 'auth_func(%s),user_id=%s' % (request.json, user.user_id)}
    return jsonify(json_res)

@app.route("/api/notauth_func", methods=['POST'])
def notauth_func():
    json_res = {'ok': True, 'msg': 'notauth_func(%s)' % request.json}
    return jsonify(json_res)

@app.route('/login', methods=['POST'])
def login():
    user_id = request.form['user_id']
    passwd_hash = request.form['passwd_hash']
    if user_id not in USERS:
        return render_template("login.html", message = "Invalid user_id or password")
    elif not USERS[user_id].can_login(passwd_hash):
        return render_template("login.html", message = "Invalid user_id or password")
    else:
        USERS[user_id].authenticated = True
        login_user(USERS[user_id], remember=True)
    return redirect("/")

@app.route('/login', methods=['GET'])
def login_page():
    return render_template("login.html")

@login_manager.unauthorized_handler
def unauthorized():
    return redirect("/login")

@app.route('/logout', methods=["GET"])
@login_required
def logout():
    user = current_user
    user.authenticated = False
    logout_user()
    return redirect("/login")

@login_manager.user_loader
def user_loader(user_id):
    return USERS[user_id]

@app.route('/', methods=["GET"])
@login_required
def main():
    return render_template("main.html")

@app.route('/api/translate')
@login_required
def translate():
    to = request.args.get('to', default="ko")
    from_lang = request.args.get('to', default="en")
    sentence = request.args.get('q', '')
    if len(sentence) == 0:
        return json.dumps({ "result" : "" }, ensure_ascii=False), 200
    blob = TextBlob(sentence)
    return json.dumps({ "result" : blob.translate(to=to, from_lang=from_lang).string }, ensure_ascii=False), 200

def lemmatize(x):
    return Word(x).lemmatize()

def definition(x): 
    return  Word(x).definitions

@app.route('/api/definition/ko')
@login_required
def get_definition_ko():
    sentence = request.args.get('q', '')
    if len(sentence) == 0:
        return json.dumps({ "result" : "" }, ensure_ascii=False), 200
    words = TextBlob(sentence).words
    words = [x for x in TextBlob(sentence).words if x.lower() not in except_words]
    lemmatized_words = list(map(lemmatize, words))
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    definition_words = loop.run_until_complete(get_meaning_all(lemmatized_words))
    loop.close()
    return json.dumps({ "result" : {"definitions":definition_words} }, ensure_ascii=False), 200

@app.route('/api/definition/en')
@login_required
def get_definition_en():
    sentence = request.args.get('q', '')
    if len(sentence) == 0:
        return json.dumps({ "result" : "" }, ensure_ascii=False), 200
    words = TextBlob(sentence).words
    words = [x for x in TextBlob(sentence).words if x.lower() not in except_words]
    lemmatized_words = list(map(lemmatize, words))
    definition_words = list(map(definition, lemmatized_words))
    return json.dumps({ "result" : [ {"lemmatized":lemmatized_words},{"definitions":definition_words}] }, ensure_ascii=False), 200

if __name__ == '__main__':
    app.run("0.0.0.0")