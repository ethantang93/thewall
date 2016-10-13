from flask import Flask, request, redirect, render_template, session, flash
from mysqlconnection import MySQLConnector
import re

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

app =  Flask(__name__)
app.secret_key = "thisisasecret"
mysql = MySQLConnector(app, 'thewalldb')


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    form= request.form
    if validate_input(form):
        print "register success!!!"
        query = """INSERT INTO users(first_name, last_name, email, password, created_at, updated_at)
        VALUES(:first_name, :last_name, :email, :password, NOW(), NOW())"""
        data = {
                'first_name':form['first_name'],
                'last_name':form['last_name'],
                'email':form['email'],
                'password':form['password']
        }
        user_id=mysql.query_db(query, data)
        print user_id
        session['current_user']=user_id
        return redirect('/wall')
    else:
        flash('Validation errors found, please correct them.')
        return redirect('/')

@app.route('/login', methods=['POST'])
def login():
    query= "SELECT * FROM users WHERE email=:email"
    data = {'email': request.form['email']}
    result = mysql.query_db(query, data)
    if result:
        if request.form['password'] == result[0]['password']:
            session['current_user'] = result[0]['id']
            print "the user's id is " + str(result[0]['id'])
            print "login successful!!!"
            return redirect('/wall')
        else:
            flash("password do not match")
            return redirect('/')
    else:
        flash("user does not exist")
        return redirect('/')


@app.route('/logout')
def logout():
    session.pop('current_user')
    flash('You have been logged out, sucka.')
    return redirect('/')


@app.route('/wall')
def wall():
    if 'current_user' in session:
        query= "SELECT * FROM users WHERE id = :id"
        data = {'id':session['current_user']
        }
        user = mysql.query_db(query,data)

        query= """SELECT messages.id, messages.message, users.first_name, users.last_name, messages.created_at FROM messages
        LEFT JOIN users ON users.id= messages.user_id
        ORDER BY created_at DESC"""
        all_posts = mysql.query_db(query)

        query = """SELECT * FROM comments
        LEFT JOIN users ON users.id = comments.user_id
        ORDER BY comments.created_at ASC"""
        all_comments = mysql.query_db(query)

        return render_template('wall.html', user=user[0], all_posts=all_posts, all_comments=all_comments)
    else:
        flash("Dont try to sneak in here bitch")
        return redirect('/')

@app.route('/postmessage/<id>', methods=['POST'])
def postmessage(id):
    print id
    print request.form['post']
    query = """INSERT INTO messages(user_id, message, created_at, updated_at)
    VALUES (:id, :post, NOW(), NOW())"""
    data = {
            'id':id,
            'post':request.form['post']
    }
    mysql.query_db(query, data)
    print query
    return redirect('/wall')

@app.route('/postcomments/<postid>', methods=['POST'])
def postcomments(postid):
    userid=session['current_user']
    print postid, userid
    query = """INSERT INTO comments(message_id, user_id, comment, created_at, updated_at)
    VALUES (:postid, :userid, :comment, NOW(), NOW())"""
    data = {
            'postid':postid,
            'userid':userid,
            'comment':request.form['comments']
    }
    mysql.query_db(query, data)
    print query
    return redirect('/wall')






# validation function
def validate_input(form):
    isValid = True
    if form['password'] != form['confirmpassword']:
        flash('Passwords do not match!')
        isValid = False

    if len(form['password']) < 8:
        flash('Password is not long enough!')
        isValid = False

    if not EMAIL_REGEX.match(form['email']):
        flash('Email is not valid!')
        isValid = False

    # first name & last name  -- at least 2 chars, no numbers
    if len(form['first_name']) < 2:
        flash('First name must be longer than 2 characters')
        isValid = False

    if any(char.isdigit() for char in form['first_name']):
        flash('First name may not contain any numbers')
        isValid = False

    if len(form['last_name']) < 2:
        flash('Last name must be longer than 2 characters')
        isValid = False

    if any(char.isdigit() for char in form['last_name']):
        flash('Last name may not contain any numbers')
        isValid = False

    return isValid


app.run(debug=True)
