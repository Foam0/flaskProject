import random
from flask import make_response
import flask
from flask import Flask, request
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

@app.route('/list/board/exit', methods=['post'])
def exxit():
    return flask.redirect('/list')

    return resp


@app.route('/list/logout')
def logout():
    resp = flask.redirect('/')
    resp.set_cookie('userID', '', expires=0)
    return resp


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
