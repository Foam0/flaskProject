import random
from flask import *
import flask
from pymongo import MongoClient
from time import time
from datetime import datetime


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
    key1 = (request.values['psw1'])
    key2 = (request.values['psw2'])
    if key1 != key2:
        resp = (flask.render_template("gt.html", message='Passwords doesn\'t match'))
    elif not users.count_documents({"name": name}):
        users.insert_one({"id": _64(), "name": name, "key": key1})
        resp = flask.redirect('/list')
        cookie = users.find_one({"name": name})["id"]
        resp.set_cookie('userID', cookie)
    else:
        resp = flask.render_template("gt.html", message='Such login already exists')
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
    return flask.render_template("gt.html", message='Incorrect login/password')


@app.route('/list', methods=['post', 'get'])
def main():
    userID = request.cookies.get("userID")
    name = users.find_one({"id": userID})["name"]
    if userID == '': return flask.redirect('/')
    try:
        lst = list(boards.find({"users": userID}))
        for ind, e in enumerate(lst):
            m = []
            for i in e["users"]:
                m.append(users.find_one({"id": i})["name"])
            lst[ind]["users"] = m
    except IndexError:
        lst = []
    d = []
    for j in lst:
        cnt_todo = 0
        cnt_in_progress = 0
        cnt_done = 0
        count_mine = 0
        for task in j["notes"]:
            count_mine += task["contributors"] == (str(name))
            if task["status"] == "to do":
                cnt_todo += 1
            if task["status"] == "in progress":
                cnt_in_progress += 1
            if task["status"] == "done":
                cnt_done += 1
        count_mine = str(count_mine)
        cnt_todo = str(cnt_todo)
        cnt_done = str(cnt_done)
        cnt_in_progress = str(cnt_in_progress)
        d.append([j['name'], count_mine, cnt_todo, cnt_in_progress, cnt_in_progress, j["id"]])
    return flask.render_template("Projects table.html", lst=d, nickname=users.find_one({"id": userID})["name"])


@app.route('/list/add', methods=['POST'])
def add():
    userID = request.cookies.get("userID")
    board_name = request.form.get("board_name")
    if request.form.get("board_name") == '':
        board_name = 'Project ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    boards.insert_one({
        "id": _64(),
        "name": board_name,
        "users": [userID],
        "notes": []

    })

    return flask.redirect('/list')


'''
            {
                "id": "",
                "importance": '',
                "name": "",
                "status": "",
                "contributor": '',  # выполняющий и задающётся именем
                "host": "",
                "time": time(),
                "desc": ''
            }            '''


@app.route('/list/new_user', methods=['post', 'get'])
def new_user():  # new user in list
    userID = request.cookies.get("userID")
    boardID = request.args.get("id")
    boardID = boardID.split()[0]
    if not boards.count_documents({"users": userID}): boards.update_one({"id": boardID}, {"$push": {"users": userID}})
    return flask.redirect('/list')


@app.route("/list/board/task/update", methods=['get', 'post'])
def update_status():
    boardID = request.args.get("boardID")
    status_task = request.args.get("status")
    task_id = request.args.get("taskID")
    boards.update_one({"id": boardID, "notes.id": task_id}, {"$set": {"notes.$.status": status_task}})
    return flask.redirect(f"/list/board?id={boardID}")


@app.route('/list/board/task/add', methods=['POST', 'GET'])
def add_task():
    boardID = request.values['id']
    userID = request.cookies.get('userID')
    taskname = request.values['short_name']
    who_do = request.values['who_do_task']
    fullcopy = request.values['fullname']
    fullname = ''
    for i in range(len(fullcopy)):
        fullname += fullcopy[i]
        if i % 40 == 39:
            fullname += '\n'
    imp = request.values['importance']
    boards.update_one({"id": boardID},
                      {"$push": {"notes": {"id": _64(), 'importance': imp, 'name': taskname, 'status': 'to do',
                                           'contributors': who_do, 'host': userID, 'time': time(), 'desc': fullname}}})
    return flask.redirect(f"/list/board?id={boardID}")


@app.route("/list/board/task/del", methods=['get', 'post'])
def del_task():
    boardID = request.values["id"]
    taskID = request.values["taskID"]
    boards.update_one({"id": boardID}, {'$pull': {"notes": {"id": taskID}}})
    return flask.redirect(f"/list/board?id={boardID}")


@app.route('/list/board/', methods=['POST', 'GET'])
def mai1():
    boardID = request.args.get("id")
    lst = boards.find_one({"id": boardID})["notes"]
    userids = boards.find_one({"id": boardID})["users"]
    username = []
    status = ['to do', 'in progress', 'done']
    for id_ in userids:
        username.append(users.find_one({'id': id_})['name'])
    resp = flask.render_template("board.html", lst=lst, un=username, boardID=boardID, status=status)
    return resp


@app.route('/list/del_board', methods=['post', 'get'])
def de_l():
    boardID = request.values['id']
    userID = request.cookies.get("userID")
    boards.update_one({"id": boardID}, {'$pull': {"users": userID}})
    return flask.redirect('/list')


@app.route('/list/board/exit', methods=['post'])
def exxit():
    return flask.redirect('/list')


@app.route('/list/board', methods=['POST'])
def go_to_board():
    boardID = request.query_string.get('id')
    resp = make_response(flask.redirect(f"/board?id={boardID}"))
    return resp


@app.route('/list/logout')
def logout():
    resp = flask.redirect('/')
    resp.set_cookie('userID', '', expires=0)
    return resp


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
