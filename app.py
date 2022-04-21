import random
from flask import make_response
import flask
from flask import Flask, request
from pymongo import MongoClient


def _64():
    alpf = 'abcdefghigklmnopqrstuvwxyzABCDEFGHIGKLMNOPQRSTUVWXYZ1234567890_.'
    n = ''
    for i in range(10): n += alpf[random.randint(0, 63)]
    return n


client = MongoClient('localhost', 27017)
database = client.test_database
users = database.users
boards = database.board

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def home():
    return flask.render_template('gt.html')


@app.route('/reg', methods=['GET', 'POST'])
def reg_parse():
    name = (request.values['login'])
    key = (request.values['psw'])
    if not users.count_documents({"name": name}):
        users.insert_one({"id": _64(), "name": name, "key": key})
        resp = flask.redirect('/list')
        cookie = users.find_one({"name": name})["id"]
        resp.set_cookie('userID', cookie)
    else:
        resp = (flask.render_template("gt.html"))
        resp += "<p class=text>извините данный логин уже занят</p>"
    return resp


@app.route('/auth', methods=['GET', 'POST'])
def authorize():
    name = (request.values['login'])
    key = (request.values['psw'])
    if users.count_documents({"name": name}):
        if users.find_one({"name": name})["key"] == key:
            resp = make_response(flask.redirect("/list"))
            cookie = users.find_one({"name": name})["id"]
            resp.set_cookie('userID', cookie)
            return resp
        return flask.render_template("gt.html") + "<p class=red>неверный пароль</p>"
    return flask.render_template("gt.html") + "<p class=red>неверный логин</p>"


@app.route("/form_reg")
def reg_send():
    return flask.render_template("register.html")


@app.route("/form_auth")
def auth_send():
    return flask.render_template("authorize.html")


@app.route('/list')
def main():
    userID = request.cookies.get("userID")
    try:
        lst = list(boards.find({"users": userID}))
        for ind, e in enumerate(lst):
            m = []
            for i in e["users"]:
                m.append(users.find_one({"id": i})["name"])
            lst[ind]["users"] = m
    except IndexError:
        lst = []
    return flask.render_template("main.html", lst=lst, nickname=users.find_one({"id": userID})["name"])


@app.route('/list/add', methods=['POST'])
def add():
    userID = request.cookies.get("userID")
    boards.insert_one({"id": _64(), "name": request.form.get("board_name"), "users": [userID]})
    return flask.redirect('/list')


@app.route('/list/new_user', methods=['get'])
def new_user():  # new user in list
    userID = request.cookies.get("userID")
    boardID = request.args.get("id")
    if not boards.count_documents({"users": userID}): boards.update_one({"id": boardID}, {"$push": {"users": userID}})
    return flask.redirect('/list')


@app.route('/list/board/', methods=['post'])
def mai():
    return "main"


@app.route('/list/board', methods=['post'])
def go_to_board():
    boardID = request.query_string.get('id')
    userID = request.users.get("userID")
    resp = make_response(flask.redirect(f"/board/id={boardID}"))
    # cookie = users.find_one({"name": name})["id"]
    resp.set_cookie('userID', userID)
    lst = boards.find_one({"id": boardID})
    td = lst["to_do"]
    ip = lst["in_progress"]
    dn = lst["done"]
    return resp

    # return flask.redirect(f'/list/boardID/{boardID}')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
