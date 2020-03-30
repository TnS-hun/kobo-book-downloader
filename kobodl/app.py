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
    return render_template('users.j2', users=users)


@app.route('/books', methods=['GET'])
def books():
    userlist = Globals.Settings.UserList.users
    books = actions.ListBooks(userlist, False)
    return render_template('books.j2', books=books)
