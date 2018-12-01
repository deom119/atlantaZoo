from flask import Flask, request, render_template, redirect, url_for, flash, session
from flaskext.mysql import MySQL

from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = b'gomtaengtang'

mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = '1234'
app.config['MYSQL_DATABASE_DB'] = 'atlzoo'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)



@app.route('/', methods=['GET', 'POST'])
def index():
    print 'haha'
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and 'cancelReg' in request.form:
        return render_template('Login.html')
    elif request.method == 'POST' and 'login' in request.form:
        validated = loginHelper(request.form)
        if validated == 0:
            return render_template('visitorHomes.html')
        elif validated == 1:
            return render_template('staffhome.html')
        elif validated == 2:
            return redirect(url_for('adminHome'))
        else:
            return render_template('badLogin.html')
    else:
        return render_template('Login.html')

def loginHelper(list):
    input_email = str(list['email'])
    input_password = str(list['password'])
    conn = mysql.connect()
    cursor = conn.cursor()
    db_names = ['visitors', 'staff', 'admins']
    for db in db_names:
        cursor.execute("SELECT * FROM " + db + " WHERE Email = %s", (input_email))
        data = cursor.fetchall()
        if len(data) == 1:
            username = data[0][0]
            password = data[0][1]
            if db == 'visitor':
                exception_password = ['password4', 'password5', 'password6', 'password7']
            elif db == 'staff':
                exception_password = ['password1', 'password2', 'password3']
            else:
                exception_password = ['adminpassword']
            if check_password_hash(password, input_password) or (password in exception_password and password == input_password):
                session['username'] = username
                session['coin'] = True
                if db == 'visitors':
                    return 0
                elif db == 'staff':
                    return 1
                else:
                    return 2
            else:
                return -1
    return -1


"""
Register page starts here
"""
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if 'renderReg' in request.form:
            return render_template('Register.html')
        elif 'cancelReg' in request.form:
            return redirect(url_for('login'))
        elif 'regVis' in request.form:
            db_name = 'visitors'
        else:
            db_name = 'staff'
        signal = RegisterUser(request.form, db_name)
        if signal:
            return redirect(url_for('login'))
        else:
            return redirect(url_for('register'))
    return render_template('Register.html')

def RegisterUser(list, db_name):
    if len(list) == 5:
        conn = mysql.connect()
        cursor = conn.cursor()

        email = str(list['email'])
        username = str(list['username'])
        password = generate_password_hash(str(list['password']))
        password2 = str(list['password2'])

        move_to_login = False
        if check_password_hash(password, password2):
            if db_name == 'visitors':
                othername = 'staff'
            else:
                othername = 'visitors'
            cursor.execute("SELECT * FROM admins WHERE Username = %s", (username))
            notHaveName = cursor.fetchone() == None
            cursor.execute("SELECT * FROM " + othername + " WHERE Username = %s", (username))
            notHaveName = cursor.fetchone() == None and notHaveName
            cursor.execute("SELECT * FROM " + db_name + " WHERE Username = %s", (username))
            notHaveName = cursor.fetchone() == None and notHaveName

            cursor.execute("SELECT * FROM admins WHERE Email = %s", (email))
            notHaveEmail = cursor.fetchone() == None
            cursor.execute("SELECT * FROM " + othername + " WHERE Email = %s", (email))
            notHaveEmail = cursor.fetchone() == None and notHaveName
            cursor.execute("SELECT * FROM " + db_name + " WHERE Email = %s", (email))
            notHaveEmail = cursor.fetchone() == None and notHaveName

            if notHaveName and notHaveEmail:
                cursor.execute("INSERT INTO " + db_name + " (Username, Password, Email) VALUES(%s, %s, %s)", (username, password, email))
                conn.commit()
                move_to_login = True
            else:
                flash('Username or email already exists')
        else:
            flash('Passwords do not match')
        cursor.close()
        return move_to_login


"""
Admin page starts here
"""
@app.route('/adminhome', methods=['GET', 'POST'])
def adminHome():
    conn = mysql.connect()
    cursor = conn.cursor()
    admin_name = session['username']
    cursor.execute("SELECT Username FROM admins WHERE Username = %s", (admin_name))
    isAdmin = len(cursor.fetchone()) > 0
    cursor.close()
    if not isAdmin:
        return redirect(url_for('login'))
    if request.method == 'POST':
        if 'viewVis' in request.form:
            return redirect(url_for('adminViewVisitors'))
        if 'viewStaff' in request.form:
            return redirect(url_for('adminViewStaffs'))
        if 'viewShow' in request.form:
            return redirect(url_for('adminViewShows'))
        if 'viewAni' in request.form:
            return redirect(url_for('adminViewAnimals'))
        if 'addAni' in request.form:
            return redirect(url_for('adminAddAnimals'))
        if 'addShow' in request.form:
            return redirect(url_for('adminAddShow'))
        if 'logOut' in request.form:
            return redirect(url_for('logout'))
    return render_template('adminhome.html')

#TODO: Search option
@app.route('/adminviewvisitors', methods=['GET', 'POST'])
def adminViewVisitors():
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT Username, Email FROM visitors")
    data = cursor.fetchall()
    if request.method == 'POST':
        if 'sortName' in request.form:
            if session['coin']:
                cursor.execute("SELECT Username, Email FROM visitors ORDER BY Username")
            elif not session['coin']:
                cursor.execute("SELECT Username, Email FROM visitors ORDER BY Username DESC")
            session['coin'] = not session['coin']
            data = cursor.fetchall()
            cursor.close()
            return render_template('adminVisitor.html', data=data)
        elif 'sortEmail' in request.form:
            if session['coin']:
                cursor.execute("SELECT Username, Email FROM visitors ORDER BY Email")
            elif not session['coin']:
                cursor.execute("SELECT Username, Email FROM visitors ORDER BY Email DESC")
            session['coin'] = not session['coin']
            data = cursor.fetchall()
            cursor.close()
            return render_template('adminVisitor.html', data=data)
        elif 'back' in request.form:
            cursor.close()
            return redirect(url_for('adminHome'))
        elif 'delete' in request.form:
            vis_name = str(request.form['delete'])
            print vis_name
            cursor.execute("DELETE FROM visitors WHERE Username = %s", (vis_name))
            conn.commit()
            cursor.execute("SELECT Username, Email FROM visitors")
            data = cursor.fetchall()
            cursor.close()
            return render_template('adminVisitor.html', data=data)
    cursor.close()
    return render_template('adminVisitor.html', data=data)

#TODO: Search option
@app.route('/adminviewstaffs', methods=['GET', 'POST'])
def adminViewStaffs():
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT Username, Email FROM staff")
    data = cursor.fetchall()
    if request.method == 'POST':
        if 'sortName' in request.form:
            if session['coin']:
                cursor.execute("SELECT Username, Email FROM staff ORDER BY Username")
            elif not session['coin']:
                cursor.execute("SELECT Username, Email FROM staff ORDER BY Username DESC")
            session['coin'] = not session['coin']
            data = cursor.fetchall()
            cursor.close()
            return render_template('adminStaff.html', data=data)
        elif 'sortEmail' in request.form:
            if session['coin']:
                cursor.execute("SELECT Username, Email FROM staff ORDER BY Email")
            elif not session['coin']:
                cursor.execute("SELECT Username, Email FROM staff ORDER BY Email DESC")
            session['coin'] = not session['coin']
            data = cursor.fetchall()
            cursor.close()
            return render_template('adminStaff.html', data=data)
        elif 'back' in request.form:
            cursor.close()
            return redirect(url_for('adminHome'))
        elif 'delete' in request.form:
            stf_name = str(request.form['delete'])
            print stf_name
            cursor.execute("DELETE FROM staff WHERE Username = %s", (stf_name))
            conn.commit()
            cursor.execute("SELECT Username, Email FROM staff")
            data = cursor.fetchall()
            cursor.close()
            return render_template('adminStaff.html', data=data)
    cursor.close()
    return render_template('adminStaff.html', data=data)

@app.route('/adminviewshows', methods=['GET', 'POST'])
def adminViewShows():
    return render_template('adminShow.html')

@app.route('/adminviewanimals', methods=['GET', 'POST'])
def adminViewAnimals():
    return render_template('adminAnimal.html')

@app.route('/adminaddanimals', methods=['GET', 'POST'])
def adminAddAnimals():
    return render_template('addAnimal.html')

@app.route('/adminaddshow', methods=['GET', 'POST'])
def adminAddShow():
    return render_template('addShow.html')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('username', None)
    session.clear()
    if request.method == 'POST' and 'toLog' in request.form:
        return redirect(url_for('login'))
    return render_template('logout.html')

if __name__ == '__main__':
    app.run()