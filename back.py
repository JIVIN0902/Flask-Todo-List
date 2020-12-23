from flask import Flask, request, render_template, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash 
import re, os
from datetime import timedelta
from functools import wraps


app = Flask(__name__)
app.secret_key = "hello"
#app.permanent_session_lifetime = timedelta(minutes = 5)
import sqlite3

#c.execute("CREATE TABLE customers (username text, email text, age integer, password_hash text) ")
#c.execute("""CREATE TABLE tasks (username text,task text)""")


# To use session id for other pages

# if 'user' in session:
#   do the thing

def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function


@app.route("/", methods = ["GET","POST"])
def login():

    if request.method == "GET":
        
        return render_template("login.html")

    else:
        
        # Set permanent session
        #session.permanent = True
        name = request.form.get("username")
        
        password = request.form.get("password")

        if name and password:
            conn = sqlite3.connect("todo_list.db")
            c = conn.cursor()

            c.execute("SELECT rowid,* FROM customers WHERE username = (?)", (name,))

            x = c.fetchall()
            if len(x) != 1 or not check_password_hash(x[0][4], password):
                flash("No such user exists")
                return render_template("login.html")
            
            session['user'] = x[0][1]
            session['id'] = x[0][0]

            print(session['id'], session['user'])

            return redirect("/index")


@app.route("/register", methods = ["GET","POST"])
def register():
    if request.method == 'GET':
        return render_template("register.html")

    else:
        username = request.form.get('username')
        mail = request.form.get("email")
        age = request.form.get("age")
        password = request.form.get('password')
        pass_again = request.form.get("password-again")


        

        if not username or not mail or not age or not pass_again or not password:
            flash("Passwords do not match or details insufficient")
            return render_template("register.html")

        email_layout = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
        email_layout2 = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w+[.]+\w+$'

        if not re.search(email_layout, mail) and not re.search(email_layout2, mail):
            flash("Invalid Email!")
            return render_template("register.html")

        if password == pass_again and username and mail and age:
            conn = sqlite3.connect("todo_list.db")
            c = conn.cursor()

            pass_hash = generate_password_hash(password)

            c.execute("SELECT * FROM customers WHERE username = (?)", (username,))

            existing = c.fetchall()

            if existing:
                flash("Username already in use.")
                return render_template("register.html")

            c.execute("INSERT INTO customers VALUES(?,?,?,?)",(username, mail, age, pass_hash))
            
            message = "Congrats!!\nYou have successfully registered to my todo-list app!"

            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()

            server.login("jivinvaidya@gmail.com", os.getenv("PASSWORD"))
            server.sendmail("jivinvaidya@gmail.com", mail, message)

            conn.commit()

            conn.close()
        
        flash("Account created!", "info")
        return render_template("index.html")


@app.route("/index",methods = ["GET","POST"])
@login_required
def index():
    if request.method == "GET":

        conn = sqlite3.connect("todo_list.db")
        c = conn.cursor()

        c.execute("SELECT task from tasks WHERE username= (?)", (session['user'],))
        lst = c.fetchall()

        conn.commit()
        conn.close()

        return render_template("index.html", lst=lst)

    else:
        task = request.form.get("task")
        if not task:
            flash("Enter task!")
            return render_template("index.html")
        conn = sqlite3.connect("todo_list.db")
        c = conn.cursor()

        c.execute("INSERT INTO tasks VALUES (?,?)",(session['user'], task))

        conn.commit()
        conn.close()
        if 'user' in session:
            user = session['user']
        flash("Task added successfully!", "info")

        conn = sqlite3.connect("todo_list.db")
        c = conn.cursor()

        c.execute("SELECT task from tasks WHERE username= (?)", (session['user'],))
        lst = c.fetchall()

        conn.commit()
        conn.close()

        return render_template("index.html", lst=lst)


@app.route("/list")
@login_required
def list():
        conn = sqlite3.connect("todo_list.db")
        c = conn.cursor()

        c.execute("SELECT task from tasks WHERE username= (?)", (session['user'],))
        lst = c.fetchall()

        conn.commit()
        conn.close()

        return render_template("index.html", lst=lst)


@app.route("/logout")
@login_required
def logout():
    session.pop("user", None)

    flash("You have been logged out!", 'info')

    return render_template("login.html")


@app.route("/edit", methods = ['GET','POST'])
@login_required
def edit():
        if request.method == "GET":
            conn = sqlite3.connect("todo_list.db")
            c = conn.cursor()

            c.execute("SELECT * from customers WHERE username = (?)", (session['user'],))
            lst = c.fetchall()
            
            conn.commit()
            conn.close()

            username = lst[0][0]
            email = lst[0][1]
            age = lst[0][2]

            return render_template("edit.html", username=username, email=email, age=age)

        else:
            new_name = request.form.get('new-name')
            new_email = request.form.get('new-email')
            new_age = request.form.get('new-age')

            if new_name == '0' or new_email == '0' or new_age == '0':
                flash("Please re-type all the details.")
                return render_template("edit.html")

            conn = sqlite3.connect("todo_list.db")
            c = conn.cursor()

            c.execute("UPDATE customers SET username = (?), email = (?), age = (?) WHERE username = (?)",(new_name, new_email, new_age, session['user']))
            
            conn.commit()
            conn.close()
            print(session['user'])
            flash("Details Edited!")
            return render_template("index.html")


@app.route("/cp", methods=['POST'])
@login_required
def change_pass():
    if request.method == "POST":
        old = request.form.get("old-pass")
        new = request.form.get("new-pass")
        new_again = request.form.get("new-pass-again")

        print(old,new,new_again)

        if not old or not new or not new_again:
            flash("Please provide all the details!")
            return render_template("edit.html")

        if new_again != new:
            flash("New passwords don't match")
            return render_template("edit.html")

        conn = sqlite3.connect("todo_list.db")
        c = conn.cursor()

        c.execute("SELECT password_hash FROM customers WHERE username = (?)", (session['user'],))
        x = c.fetchall()
        result = check_password_hash(x[0][0], old)

        if not result:
            flash("Old password incorrect")
            return render_template("edit.html")
        
        new_pass_hash = generate_password_hash(new_again)
        print(new_pass_hash)

        c.execute("UPDATE customers SET password_hash = (?) WHERE username = (?)",(new_pass_hash, session['user']))
        
        conn.commit()
        conn.close()

        flash("Password Changed")
        return render_template("edit.html")
  

@app.route("/delete/<task_name>", methods = ['POST'])
@login_required
def delete(task_name):
    if request.method == 'POST':
        task = request.form.get("{{ i[0] }}")

        conn = sqlite3.connect("todo_list.db")
        c = conn.cursor()

        c.execute("DELETE FROM tasks WHERE task = (?)", [task_name])

        conn.commit()
        conn.close()

        flash("Task Deleted!")

        return redirect("/index")

@app.route('/remove', methods = ['POST'])
@login_required
def remove():

    if request.method == 'POST':

        account = request.form.get('remove')
        conn = sqlite3.connect("todo_list.db")
        c = conn.cursor()

        c.execute("DELETE FROM customers WHERE username = (?)", (session['user'],))
        c.execute("DELETE FROM tasks WHERE username = (?)", (session['user'],))

        conn.commit()
        conn.close()

        flash("Account Deleted!")
        return render_template("login.html")


if __name__ == "__main__":
    app.run(debug = True)