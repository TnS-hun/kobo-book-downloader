import os

from flask import abort, Flask, render_template, request, redirect, send_from_directory

from kobodl import actions
from kobodl.globals import Globals
from kobodl.settings import User


app = Flask(__name__)


@app.route('/')
def index():
    return redirect('/user')


@app.route('/user', methods=['GET', 'POST'])
def users():
    error = None
    if request.method == 'POST':
        print(request.form)
        email = request.form.get('email')
        password = request.form.get('password')
        captcha = request.form.get('captcha')
        print(email, password, captcha)
        if email and password and captcha:
            user = User(Email=email)
            try:
                actions.Login(user, password, captcha)
                Globals.Settings.UserList.users.append(user)
                Globals.Settings.Save()
            except Exception as err:
                error = str(err)
        else:
            error = 'email, password, or captcha missing'
    users = Globals.Settings.UserList.users
    return render_template('users.j2', users=users, error=error)


@app.route('/user/<userid>/book', methods=['GET'])
def getUserBooks(userid):
    user = Globals.Settings.UserList.getUser(userid)
    if not user:
        abort(404)
    books = actions.ListBooks([user], False)
    return render_template('books.j2', books=books)


@app.route('/user/<userid>/book/<productid>', methods=['GET'])
def downloadBook(userid, productid):
    user = Globals.Settings.UserList.getUser(userid)
    if not user:
        abort(404)
    outputRelPath = app.config.get('output_dir')
    os.makedirs(outputRelPath, exist_ok=True)
    outputPath = actions.GetBookOrBooks(user, outputRelPath, productId=productid)
    _, tail = os.path.split(outputPath)
    directory = os.path.join(os.getcwd(), outputRelPath)
    return send_from_directory(
        directory, tail, as_attachment=True, attachment_filename=tail
    )


@app.route('/book', methods=['GET'])
def books():
    userlist = Globals.Settings.UserList.users
    books = actions.ListBooks(userlist, False)
    return render_template('books.j2', books=books)
