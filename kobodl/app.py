from flask import Flask, render_template

from kobodl import actions
from kobodl.globals import Globals

app = Flask(__name__)

@app.route('/')
def index():
    return 'Hello World'


@app.route('/users', methods=['GET'])
def users():
    users = Globals.Settings.UserList.users
    headers = ["Email", "UserKey", "DeviceId", "Authed"]
    return render_template('users.j2', headers=headers, users=users)

@app.route('/books', methods=['GET'])
def books():
    userlist = Globals.Settings.UserList.users
    books = actions.ListBooks(userlist, False)
    headers = ['Title', 'Author', 'RevisionId', 'Archived', 'Owner']
    return render_template('books.j2', headers=headers, books=books)
