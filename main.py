from flask import Flask, request, render_template, redirect, url_for, flash, session, Markup
from flaskext.mysql import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import ast
import datetime

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
    conn = mysql.connect()
    cursor = conn.cursor()
    admin = ['admin1']
    visitors = ['isabella_rodriguez', 'nadias_tevens', 'robert_bernheardt', 'xavier_swenson']
    staff = ['benjamin_rao', 'ethan_roswell', 'martha_johnson']
    for i in admin:
        cursor.execute("SELECT Password FROM admins WHERE Username = %s", (i))
        password = cursor.fetchone()[0]
        cursor.execute("""
           UPDATE admins
           SET Password = %s
           WHERE Username = %s
        """, (generate_password_hash(password), i))
    for i in visitors:
        cursor.execute("SELECT Password FROM visitors WHERE Username = %s", (i))
        password = cursor.fetchone()[0]
        cursor.execute("""
           UPDATE visitors
           SET Password = %s
           WHERE Username = %s
        """, (generate_password_hash(password), i))
    for i in staff:
        cursor.execute("SELECT Password FROM staff WHERE Username = %s", (i))
        password = cursor.fetchone()[0]
        cursor.execute("""
           UPDATE staff
           SET Password = %s
           WHERE Username = %s
        """, (generate_password_hash(password), i))
    conn.commit()
    cursor.close()
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and 'cancelReg' in request.form:
        return render_template('Login.html')
    elif request.method == 'POST' and 'login' in request.form:
        validated = loginHelper(request.form)
        if validated == 0:
            return redirect(url_for('visitorHome'))
        elif validated == 1:
            return redirect(url_for('staffHome'))
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
    isAdmin = cursor.fetchone()
    cursor.close()
    if not isAdmin:
        return redirect(url_for('login'))
    if request.method == 'POST':
        if 'viewVis' in request.form:
            return redirect(url_for('adminViewVisitors'))
        elif 'viewStaff' in request.form:
            return redirect(url_for('adminViewStaffs'))
        elif 'viewShow' in request.form:
            return redirect(url_for('adminViewShows'))
        elif 'viewAni' in request.form:
            return redirect(url_for('adminViewAnimals'))
        elif 'addAni' in request.form:
            return redirect(url_for('adminAddAnimals'))
        elif 'addShow' in request.form:
            return redirect(url_for('adminAddShow'))
        elif 'logOut' in request.form:
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
        elif 'search' in request.form:
            option = request.form['searchopt']
            key = request.form['searchkey']
            if key == "":
                cursor.execute("SELECT Username, Email FROM visitors")
            else:
                cursor.execute("SELECT Username, Email FROM visitors WHERE " + str(option) + " LIKE %s", "%" + str(key) + "%")
            data = cursor.fetchall()
            cursor.close()
            return render_template('adminVisitor.html', data=data)
        elif 'back' in request.form:
            cursor.close()
            return redirect(url_for('adminHome'))
        elif 'delete' in request.form:
            vis_name = str(request.form['delete'])
            if vis_name == '':
                cursor.execute("SELECT Username, Email FROM visitors")
                data = cursor.fetchall()
                cursor.close()
                return render_template('adminVisitor.html', data=data)
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
        elif 'search' in request.form:
            option = request.form['searchopt']
            key = request.form['searchkey']
            if key == "":
                cursor.execute("SELECT Username, Email FROM staff")
            else:
                cursor.execute("SELECT Username, Email FROM staff WHERE " + str(option) + " LIKE %s", "%" + str(key) + "%")
            data = cursor.fetchall()
            cursor.close()
            return render_template('adminStaff.html', data=data)
        elif 'back' in request.form:
            cursor.close()
            return redirect(url_for('adminHome'))
        elif 'delete' in request.form:
            stf_name = str(request.form['delete'])
            if stf_name == '':
                cursor.execute("SELECT Username, Email FROM staff")
                data = cursor.fetchall()
                cursor.close()
                return render_template('adminStaff.html', data=data)
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
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT Name, Date_and_time, Located_at FROM shows")
    data = cursor.fetchall()
    if request.method == 'POST':
        if 'sortName' in request.form:
            if session['coin']:
                cursor.execute("SELECT Name, Date_and_time, Located_at FROM shows ORDER BY Name")
            elif not session['coin']:
                cursor.execute("SELECT Name, Date_and_time, Located_at FROM shows ORDER BY Name DESC")
            session['coin'] = not session['coin']
            data = cursor.fetchall()
            cursor.close()
            return render_template('adminShow.html', data=data)
        elif 'sortTime' in request.form:
            if session['coin']:
                cursor.execute("SELECT Name, Date_and_time, Located_at FROM shows ORDER BY Date_and_time")
            elif not session['coin']:
                cursor.execute("SELECT Name, Date_and_time, Located_at FROM shows ORDER BY Date_and_time DESC")
            session['coin'] = not session['coin']
            data = cursor.fetchall()
            cursor.close()
            return render_template('adminShow.html', data=data)
        elif 'sortNumVisit' in request.form:
            if session['coin']:
                cursor.execute("SELECT Name, Date_and_time, Located_at FROM shows ORDER BY Located_at")
            elif not session['coin']:
                cursor.execute("SELECT Name, Date_and_time, Located_at FROM shows ORDER BY Located_at DESC")
            session['coin'] = not session['coin']
            data = cursor.fetchall()
            cursor.close()
            return render_template('adminShow.html', data=data)
        elif 'back' in request.form:
            cursor.close()
            return redirect(url_for('adminHome'))
        elif 'search' in request.form:
            option = request.form['searchopt']
            if option == 'any':
                option = None
            name = request.form['searchname']
            if name == '':
                name = None
            else:
                name = "%" + name + "%"
            searchTime = request.form['datetime']
            if searchTime == '':
                searchTime = None
            else:
                searchTime = datetime.datetime.strptime(searchTime, '%Y-%m-%d')
            if name == "" and option == 'any' and searchTime == "":
                cursor.execute("SELECT Name, Date_and_time, Located_at FROM shows")
            else:
                cursor.execute("SELECT Name, Date_and_time, Located_at FROM shows WHERE (%s IS NULL OR Name LIKE %s) AND (%s IS NULL OR DATE(Date_and_time) = %s) AND (%s IS NULL OR Located_at = %s)", (name, name, searchTime, searchTime, option, option))
            data = cursor.fetchall()
            cursor.close()
            return render_template('adminShow.html', data=data)
        elif 'delete' in request.form:
            show_row = request.form['delete']
            if show_row == '':
                cursor.execute("SELECT Name, Date_and_time, Located_at FROM shows")
                data = cursor.fetchall()
                cursor.close()
                return render_template('adminShow.html', data=data)
            row = ast.literal_eval(show_row)
            show_name = row['name']
            show_exh = row['exhibit']
            show_date = row['date']
            show_datetime = datetime.datetime.strptime(show_date, '%Y-%m-%d %H:%M:%S')
            show_datetime = show_datetime.strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("DELETE FROM shows WHERE Name = %s AND Located_at = %s AND Date_and_time = %s", (str(show_name),
                                                                                                    str(show_exh),
                                                                                                    show_datetime))
            conn.commit()
            cursor.execute("SELECT Name, Date_and_time, Located_at FROM shows")
            data = cursor.fetchall()
            cursor.close()
            return render_template('adminShow.html', data=data)
        elif 'logout' in request.form:
            cursor.close()
            return logout()
    cursor.close()
    return render_template('adminShow.html', data=data)

@app.route('/adminviewanimals', methods=['GET', 'POST'])
def adminViewAnimals():
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal")
    data = cursor.fetchall()
    if request.method == 'POST':
        if 'sortName' in request.form:
            if session['coin']:
                cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal ORDER BY Name")
                session['coin'] = False
            elif not session['coin']:
                cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal ORDER BY Name DESC")
                session['coin'] = True
            data = cursor.fetchall()
            cursor.close()
            return render_template('adminAnimal.html', data=data)
        elif 'sortSpecies' in request.form:
            if session['coin']:
                cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal ORDER BY Species")
                session['coin'] = False
            elif not session['coin']:
                cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal ORDER BY Species DESC")
                session['coin'] = True
            data = cursor.fetchall()
            cursor.close()
            return render_template('adminAnimal.html', data=data)
        elif 'sortExhibit' in request.form:
            if session['coin']:
                cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal ORDER BY Exhibit")
                session['coin'] = False
            elif not session['coin']:
                cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal ORDER BY Exhibit DESC")
                session['coin'] = True
            data = cursor.fetchall()
            cursor.close()
            return render_template('adminAnimal.html', data=data)
        elif 'sortAge' in request.form:
            if session['coin']:
                cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal ORDER BY Age")
                session['coin'] = False
            elif not session['coin']:
                cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal ORDER BY Age DESC")
                session['coin'] = True
            data = cursor.fetchall()
            cursor.close()
            return render_template('adminAnimal.html', data=data)
        elif 'sortType' in request.form:
            if session['coin']:
                cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal ORDER BY Type")
                session['coin'] = False
            elif not session['coin']:
                cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal ORDER BY Type DESC")
                session['coin'] = True
            data = cursor.fetchall()
            cursor.close()
            return render_template('adminAnimal.html', data=data)
        elif 'back' in request.form:
            cursor.close()
            return redirect(url_for('adminHome'))
        elif 'search' in request.form:
            exh_option = request.form['exhopt']
            type_option = request.form['typeopt']
            search_name = request.form['searchname']
            search_spec = request.form['searchspec']
            max_age = int(request.form['max'])
            min_age = int(request.form['min'])
            if exh_option == 'anyExh':
                exh_option = None
            if type_option == 'anyType':
                type_option = None
            if search_name == '':
                search_name = None
            else:
                search_name = "%" + search_name + "%"
            if search_spec == '':
                search_spec = None
            else:
                search_spec = "%" + search_spec + "%"
            if max_age == 0 and min_age == 0:
                max_age = None
                min_age = None
            elif max_age == 0 and min_age > 0:
                max_age = None
            elif max_age > 0 and min_age == 0:
                min_age = None
            cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal WHERE"
                           + " (%s IS NULL OR Name LIKE %s) AND (%s IS NULL OR Species LIKE %s) "
                           + "AND (%s IS NULL OR Exhibit = %s) AND (%s IS NULL OR Age >= %s) "
                           + "AND (%s IS NULL OR Age <= %s) AND (%s IS NULL OR Type = %s)",
                           (search_name, search_name, search_spec, search_spec, exh_option, exh_option, min_age, min_age, max_age, max_age, type_option, type_option))
            data = cursor.fetchall()
            cursor.close()
            return render_template('adminAnimal.html', data=data)
        elif 'delete' in request.form: # TODO Fix DELETE
            ani_row = request.form['delete']
            if ani_row == '':
                cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal")
                data = cursor.fetchall()
                cursor.close()
                return render_template('adminAnimal.html', data=data)
            row = ast.literal_eval(ani_row)
            name = row["name"]
            species = row['species']
            exhibit = row['exhibit']
            age = row['age']
            ani_type = row['type']
            cursor.execute("DELETE FROM animal WHERE Age = %s AND Type = %s AND Species = %s AND Name = %s AND Exhibit = %s", (age, ani_type, species, name, exhibit))
            conn.commit()
            cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal")
            data = cursor.fetchall()
            cursor.close()
            return render_template('adminAnimal.html', data=data)
        elif 'logout' in request.form:
            cursor.close()
            return logout()
    cursor.close()
    return render_template('adminAnimal.html', data=data)

@app.route('/adminaddanimals', methods=['GET', 'POST'])
def adminAddAnimals():
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT Name FROM exhibit")
    data = cursor.fetchall()
    if request.method == 'POST':
        if 'addani' in request.form:
            name = request.form['aniname']
            exh = request.form['aniexh']
            anitype = request.form['anitype']
            spec = request.form['anispec']
            age = int(request.form['aniage'])
            cursor.execute("SELECT Name, Species FROM animal WHERE Name = %s AND Species = %s", (name, spec))
            notHave = cursor.fetchone() == None
            if notHave:
                cursor.execute("INSERT INTO animal (Age, Type, Species, Name, Exhibit) VALUES(%s, %s, %s, %s, %s)", (age, anitype, spec, name, exh))
                conn.commit()
                cursor.close()
            return redirect(url_for('adminAddAnimals'))
        elif 'cancel' in request.form:
            cursor.close()
            return redirect(url_for('adminHome'))
    cursor.close()
    return render_template('addAnimal.html', data=data)

@app.route('/adminaddshow', methods=['GET', 'POST'])
def adminAddShow():
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT Username FROM staff")
    stafdata = cursor.fetchall()
    cursor.execute("SELECT Name FROM exhibit")
    exhdata = cursor.fetchall()
    if request.method == 'POST':
        if 'addshow' in request.form:
            name = request.form['showname']
            aniexh = request.form['aniexh']
            staff = request.form['staff']
            date = request.form['date']
            show_datetime = datetime.datetime.strptime(date, '%d/%m/%Y %I:%M %p')
            show_datetime = show_datetime.strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("SELECT Name, Date_and_time FROM shows WHERE Name = %s AND Date_and_time = %s", (name, show_datetime))
            notHave = cursor.fetchone() == None
            if notHave:
                cursor.execute("INSERT INTO shows (Name, Date_and_time, Located_at, Host) VALUES(%s, %s, %s, %s)",
                               (name, show_datetime, aniexh, staff))
                conn.commit()
                cursor.close()
            return redirect(url_for('adminAddAnimals'))
        elif 'cancel' in request.form:
            cursor.close()
            return redirect(url_for('adminHome'))
    cursor.close()
    return render_template('addShow.html', exhdata=exhdata, stafdata=stafdata)



"""
Staff page starts here
"""
@app.route('/staffhome', methods=['GET', 'POST'])
def staffHome():
    conn = mysql.connect()
    cursor = conn.cursor()
    staff_name = session['username']
    cursor.execute("SELECT Username FROM STAFF WHERE Username = %s", (staff_name))
    isStaff = len(cursor.fetchone()) > 0
    cursor.close()
    if not isStaff:
        return redirect(url_for('login'))
    if request.method == 'POST':
        if 'staffShow' in request.form:
            return redirect(url_for('staffShow'))
        elif 'staffAnimals' in request.form:
            return redirect(url_for('staffAnimals'))
        elif 'staffLogout' in request.form:
            return redirect(url_for('logout'))
    return render_template('staffhome.html')


"""
Staff Show page starts here
"""
@app.route('/staffshow', methods=['GET', 'POST'])
def staffShow():
    conn = mysql.connect()
    cursor = conn.cursor()
    staff_name = session['username']
    cursor.execute("SELECT Name, Date_and_time, Located_at FROM shows WHERE Host = %s", (staff_name))
    data = cursor.fetchall()
    if request.method == 'POST':
        if 'sortName' in request.form:
            if session['coin']:
                cursor.execute("SELECT Name, Date_and_time, Located_at FROM shows WHERE Host = %s ORDER BY Name", (staff_name))
            elif not session['coin']:
                cursor.execute("SELECT Name, Date_and_time, Located_at FROM shows WHERE Host = %s ORDER BY Name DESC", (staff_name))
            session['coin'] = not session['coin']
            data = cursor.fetchall()
            cursor.close()
            return render_template('staffshow.html', data=data)
        elif 'sortExhibit' in request.form:
            if session['coin']:
                cursor.execute("SELECT Name, Date_and_time, Located_at FROM shows WHERE Host = %s ORDER BY Located_at", (staff_name))
            elif not session['coin']:
                cursor.execute("SELECT Name, Date_and_time, Located_at FROM shows WHERE Host = %s ORDER BY Located_at DESC", (staff_name))
            session['coin'] = not session['coin']
            data = cursor.fetchall()
            cursor.close()
            return render_template('staffshow.html', data=data)
        elif 'sortTime' in request.form:
            if session['coin']:
                cursor.execute("SELECT Name, Date_and_time, Located_at FROM shows WHERE Host = %s ORDER BY Date_and_time", (staff_name))
            elif not session['coin']:
                cursor.execute("SELECT Name, Date_and_time, Located_at FROM shows WHERE Host = %s ORDER BY Date_and_time DESC", (staff_name))
            session['coin'] = not session['coin']
            data = cursor.fetchall()
            cursor.close()
            return render_template('staffshow.html', data=data)
        elif 'back' in request.form:
            cursor.close()
            return redirect(url_for('staffHome'))
        elif 'logout' in request.form:
            cursor.close()
            return logout()
    cursor.close()
    return render_template('staffshow.html', data=data)


"""
Staff Animal page starts here
"""

@app.route('/staffAnimals', methods=['GET', 'POST'])
def staffAnimals():
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal")
    data = cursor.fetchall()
    if request.method == 'POST':
        if 'sortName' in request.form:
            if session['coin']:
                cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal ORDER BY Name")
                session['coin'] = False
            elif not session['coin']:
                cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal ORDER BY Name DESC")
                session['coin'] = True
            data = cursor.fetchall()
            cursor.close()
            return render_template('staffAnimals.html', data=data)
        elif 'sortSpecies' in request.form:
            if session['coin']:
                cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal ORDER BY Species")
                session['coin'] = False
            elif not session['coin']:
                cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal ORDER BY Species DESC")
                session['coin'] = True
            data = cursor.fetchall()
            cursor.close()
            return render_template('staffAnimals.html', data=data)
        elif 'sortExhibit' in request.form:
            if session['coin']:
                cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal ORDER BY Exhibit")
                session['coin'] = False
            elif not session['coin']:
                cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal ORDER BY Exhibit DESC")
                session['coin'] = True
            data = cursor.fetchall()
            cursor.close()
            return render_template('staffAnimals.html', data=data)
        elif 'sortAge' in request.form:
            if session['coin']:
                cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal ORDER BY Age")
                session['coin'] = False
            elif not session['coin']:
                cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal ORDER BY Age DESC")
                session['coin'] = True
            data = cursor.fetchall()
            cursor.close()
            return render_template('staffAnimals.html', data=data)
        elif 'sortType' in request.form:
            if session['coin']:
                cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal ORDER BY Type")
                session['coin'] = False
            elif not session['coin']:
                cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal ORDER BY Type DESC")
                session['coin'] = True
            data = cursor.fetchall()
            cursor.close()
            return render_template('staffAnimals.html', data=data)
        elif 'back' in request.form:
            cursor.close()
            return redirect(url_for('staffHome'))
        elif 'search' in request.form:
            exh_option = request.form['exhopt']
            type_option = request.form['typeopt']
            search_name = request.form['searchname']
            search_spec = request.form['searchspec']
            max_age = int(request.form['max'])
            min_age = int(request.form['min'])
            if exh_option == 'anyExh':
                exh_option = None
            if type_option == 'anyType':
                type_option = None
            if search_name == '':
                search_name = None
            else:
                search_name = "%" + search_name + "%"
            if search_spec == '':
                search_spec = None
            else:
                search_spec = "%" + search_spec + "%"
            if max_age == 0 and min_age == 0:
                max_age = None
                min_age = None
            elif max_age == 0 and min_age > 0:
                max_age = None
            elif max_age > 0 and min_age == 0:
                min_age = None
            cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal WHERE"
                           + " (%s IS NULL OR Name LIKE %s) AND (%s IS NULL OR Species LIKE %s) "
                           + "AND (%s IS NULL OR Exhibit = %s) AND (%s IS NULL OR Age >= %s) "
                           + "AND (%s IS NULL OR Age <= %s) AND (%s IS NULL OR Type = %s)",
                           (search_name, search_name, search_spec, search_spec, exh_option, exh_option, min_age, min_age, max_age, max_age, type_option, type_option))
            data = cursor.fetchall()
            cursor.close()
            return render_template('staffAnimals.html', data=data)
        elif 'takenote' in request.form:
            ani_row = request.form['takenote']
            if len(ani_row) == 0:
                cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal")
                data = cursor.fetchall()
                cursor.close()
                return render_template('staffAnimals.html', data=data)
            else:
                session['notenote'] = ani_row
                return redirect(url_for('animalCare'))
        elif 'logout' in request.form:
            cursor.close()
            return logout()
        cursor.close()
    return render_template('staffAnimals.html', data=data)

"""
Staff-- Animal Care page starts here
"""
@app.route('/animalCare', methods=['GET', 'POST'])
def animalCare():
    conn = mysql.connect()
    cursor = conn.cursor()
    notenote = session['notenote']
    message = Markup(str(notenote))
    flash(message)
    cursor.execute("SELECT Username, Text, Time FROM NOTE")
    data = cursor.fetchall()
    if request.method == 'POST':
        if 'sortStaff' in request.form:
            if session['coin']:
                cursor.execute("SELECT Username, Text, Time FROM NOTE ORDER BY Name")
            elif not session['coin']:
                cursor.execute("SELECT Username, Text, Time FROM NOTE ORDER BY Name DESC")
            session['coin'] = not session['coin']
            data = cursor.fetchall()
            cursor.close()
            return render_template('animalCare.html', data=data)
        elif 'sortNote' in request.form:
            if session['coin']:
                cursor.execute("SELECT Username, Text, Time FROM NOTE ORDER BY Text")
            elif not session['coin']:
                cursor.execute("SELECT Username, Text, Time FROM NOTE ORDER BY Text DESC")
            session['coin'] = not session['coin']
            data = cursor.fetchall()
            cursor.close()
            return render_template('animalCare.html', data=data)
        elif 'sortTime' in request.form:
            if session['coin']:
                cursor.execute("SELECT Username, Text, Time FROM NOTE ORDER BY Time")
            elif not session['coin']:
                cursor.execute("SELECT Username, Text, Time FROM NOTE ORDER BY Time DESC")
            session['coin'] = not session['coin']
            data = cursor.fetchall()
            cursor.close()
            return render_template('animalCare.html', data=data)
        elif 'lognote' in request.form:
            note_text = request.form['thisnote']

            row = ast.literal_eval(notenote)
            note_name = row['name']
            note_exh = row['exhibit']
            note_date = datetime.datetime.now()
            note_now = note_date.strftime('%Y-%m-%d %H:%M:%S')
            note_species = row['species']
            note_age = row['age']
            note_host = session['username']
            cursor.execute("SELECT Email FROM staff WHERE Username = %s", (note_host))
            note_email = cursor.fetchone()[0]

            cursor.execute("SELECT Name, Species FROM NOTE WHERE Name = %s AND Species = %s AND Time = %s AND Username = %s", (note_name, note_species, note_now, note_host))
            noteHave = len(cursor.fetchall()) == 0
            if noteHave:
                cursor.execute("INSERT INTO NOTE (Time, Text, Username, Name, Species, Staff_email) VALUES(%s, %s, %s, %s, %s, %s)", (note_now, note_text, note_host, note_name, note_species, note_email))
                conn.commit()
                cursor.close()
            return redirect(url_for('animalCare'))
        elif 'back' in request.form:
            cursor.close()
            return redirect(url_for('staffAnimals'))
        elif 'logout' in request.form:
            return redirect(url_for('logout'))
    return render_template('animalCare.html', data=data)
"""
Visitor page starts here
"""
@app.route('/visitorhome', methods=['GET', 'POST'])
def visitorHome():
    conn = mysql.connect()
    cursor = conn.cursor()
    visitor_name = session['username']
    cursor.execute("SELECT Username FROM visitors WHERE Username = %s", (visitor_name))
    isVisitor = cursor.fetchone()
    cursor.close()
    if not isVisitor:
        return redirect(url_for('login'))
    if request.method == 'POST':
        if request.method == 'POST':
            if 'searchExhibit' in request.form:
                return redirect(url_for('visitorSearchExh'))
            elif 'searchShow' in request.form:
                return redirect(url_for('searchShows'))
            elif 'viewExHis' in request.form:
                return redirect(url_for('exhibitHistory'))
            elif 'viewShHis' in request.form:
                return redirect(url_for('showHistory'))
            elif 'searchAnimal' in request.form:
                return redirect(url_for('searchAnimals'))
            elif 'logOut' in request.form:
                return redirect(url_for('logout'))
    return render_template('visitorHome.html')

"""
Visitor search exhibit page starts here
"""
@app.route('/visistorsearchexhibit', methods=['GET', 'POST'])
def visitorSearchExh():
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT Name FROM exhibit")
    exhdata = cursor.fetchall()
    cursor.execute("SELECT exhibit.*, COUNT(animal.Exhibit) "
                   "FROM exhibit "
                   "LEFT JOIN animal "
                   "ON exhibit.Name = animal.Exhibit "
                   "GROUP BY exhibit.Name")
    data = cursor.fetchall()
    if request.method == 'POST':
        if 'sortName' in request.form:
            if session['coin']:
                cursor.execute("SELECT exhibit.*, COUNT(animal.Exhibit) "
                               "FROM exhibit LEFT JOIN animal "
                               "ON exhibit.Name = animal.Exhibit "
                               "GROUP BY exhibit.Name "
                               "ORDER BY exhibit.Name")
            elif not session['coin']:
                cursor.execute("SELECT exhibit.*, COUNT(animal.Exhibit) "
                               "FROM exhibit LEFT JOIN animal "
                               "ON exhibit.Name = animal.Exhibit "
                               "GROUP BY exhibit.Name "
                               "ORDER BY exhibit.Name DESC")
            session['coin'] = not session['coin']
            data = cursor.fetchall()
            cursor.close()
            return render_template('searchExhibit.html', data=data, exhdata=exhdata)
        elif 'sortSize' in request.form:
            if session['coin']:
                cursor.execute("SELECT exhibit.*, COUNT(animal.Exhibit) "
                               "FROM exhibit LEFT JOIN animal "
                               "ON exhibit.Name = animal.Exhibit "
                               "GROUP BY exhibit.Name "
                               "ORDER BY exhibit.Size")
            elif not session['coin']:
                cursor.execute("SELECT exhibit.*, COUNT(animal.Exhibit) "
                               "FROM exhibit LEFT JOIN animal "
                               "ON exhibit.Name = animal.Exhibit "
                               "GROUP BY exhibit.Name "
                               "ORDER BY exhibit.Size DESC")
            session['coin'] = not session['coin']
            data = cursor.fetchall()
            cursor.close()
            return render_template('searchExhibit.html', data=data, exhdata=exhdata)
        elif 'sortNumber' in request.form:
            if session['coin']:
                cursor.execute("SELECT exhibit.*, COUNT(animal.Exhibit) "
                               "FROM exhibit LEFT JOIN animal "
                               "ON exhibit.Name = animal.Exhibit "
                               "GROUP BY exhibit.Name "
                               "ORDER BY COUNT(animal.Exhibit)")
            elif not session['coin']:
                cursor.execute(
                    "SELECT exhibit.*, COUNT(animal.Exhibit) "
                    "FROM exhibit LEFT JOIN animal "
                    "ON exhibit.Name = animal.Exhibit "
                    "GROUP BY exhibit.Name "
                    "ORDER BY COUNT(animal.Exhibit) DESC")
            session['coin'] = not session['coin']
            data = cursor.fetchall()
            cursor.close()
            return render_template('searchExhibit.html', data=data, exhdata=exhdata)
        elif 'sortWater' in request.form:
            if session['coin']:
                cursor.execute("SELECT exhibit.*, COUNT(animal.Exhibit) "
                               "FROM exhibit LEFT JOIN animal "
                               "ON exhibit.Name = animal.Exhibit "
                               "GROUP BY exhibit.Name "
                               "ORDER BY exhibit.Water_Feature")
            elif not session['coin']:
                cursor.execute("SELECT exhibit.*, COUNT(animal.Exhibit) "
                               "FROM exhibit LEFT JOIN animal "
                               "ON exhibit.Name = animal.Exhibit "
                               "GROUP BY exhibit.Name "
                               "ORDER BY exhibit.Water_Feature DESC")
            session['coin'] = not session['coin']
            data = cursor.fetchall()
            cursor.close()
            return render_template('searchExhibit.html', data=data, exhdata=exhdata)
        elif 'search' in request.form:
            searchkey = request.form['aniexh']
            hasWater = request.form['waterFeature']
            max_size = request.form['max_size']
            min_size = request.form['min_size']
            max_num = request.form['max_num']
            min_num = request.form['min_num']
            if searchkey == 'any':
                searchkey = None
            if hasWater == 'noUse':
                hasWater = None
            elif hasWater == 'yes':
                hasWater = 1
            elif hasWater == 'no':
                hasWater = 0
            if max_size == '' and min_size == '':
                max_size = None
                min_size = None
            elif max_size == '' and min_size > 0:
                max_size = None
            elif max_size > 0 and min_size == '':
                min_size = None
            if max_num == '' and min_num == '':
                max_num = None
                min_num = None
            elif max_num == '' and min_num > 0:
                max_num = None
            elif max_num > 0 and min_num == '':
                min_num = None
            cursor.execute("SELECT Size, Water_Feature, Name, num FROM "
                           "(SELECT exhibit.*, COUNT(animal.Exhibit) as num "
                           "FROM exhibit LEFT JOIN animal ON exhibit.Name = animal.Exhibit "
                           "GROUP BY exhibit.Name) as foo "
                           "WHERE (%s IS NULL OR Name = %s) and (%s IS NULL OR Water_Feature = %s) "
                           "AND (%s IS NULL OR Size >= %s) AND (%s IS NULL OR Size <= %s) "
                           "AND (%s IS NULL OR num >= %s) AND (%s IS NULL OR num <= %s)",
                           (searchkey, searchkey, hasWater, hasWater, min_size, min_size, max_size, max_size, min_num, min_num, max_num, max_num))
            data = cursor.fetchall()
            return render_template('searchExhibit.html', data=data, exhdata=exhdata)
        elif 'takenote' in request.form:
            exh_row = request.form['takenote']
            if len(exh_row) == 0:
                cursor.execute("SELECT exhibit.*, COUNT(animal.Exhibit) "
                               "FROM exhibit "
                               "LEFT JOIN animal "
                               "ON exhibit.Name = animal.Exhibit "
                               "GROUP BY exhibit.Name")
                data = cursor.fetchall()
                cursor.close()
                return render_template('searchExhibit.html', data=data, exhdata=exhdata)
            else:
                session['exhnote'] = exh_row
                return redirect(url_for('detailExhibit'))
        elif 'back' in request.form:
            cursor.close()
            return redirect(url_for('visitorHome'))
        elif 'logout' in request.form:
            cursor.close()
            return redirect(url_for('logout'))
    cursor.close()
    return render_template('searchExhibit.html', data=data, exhdata=exhdata)

@app.route('/detailexh', methods=['GET', 'POST'])
def detailExhibit():
    data = session['exhnote']
    conn = mysql.connect()
    cursor = conn.cursor()
    exhdet = ast.literal_eval(data)
    if len(exhdet) != 5:
        cursor.close()
        return redirect(url_for('visitorSearchExh'))
    hasWater = exhdet['age']
    if hasWater == 1:
        hasWater = 'Yes'
    elif hasWater == 0:
        hasWater = 'No'
    numAni = exhdet['exhibit']
    name = exhdet['name']
    size = exhdet['species']
    if request.method == 'POST':
        if 'log' in request.form:
            note_date = datetime.datetime.now()
            note_now = note_date.strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("SELECT Email FROM visitors WHERE Username = %s", (session['username']))
            email = cursor.fetchone()[0]

            cursor.execute("SELECT Datetime, Exhibit_name, Visitor_username FROM visit_exhibit "
                           "WHERE Datetime = %s AND Exhibit_name = %s AND Visitor_username = %s",
                           (note_now, name, session['username']))
            logexh = len(cursor.fetchall()) == 0
            if logexh:
                cursor.execute(
                    "INSERT INTO visit_exhibit (Datetime, Exhibit_name, Visitor_username, Visitor_Email) VALUES(%s, %s, %s, %s)",
                    (note_now, name, session['username'], email))
                conn.commit()
                cursor.close()
            return redirect(url_for('detailExhibit'))
        elif 'back' in request.form:
            cursor.close()
            return redirect(url_for('visitorSearchExh'))
    cursor.close()
    return render_template('exhibitDetail.html', numAni=numAni, size=size, name=name, water=hasWater)


@app.route('/searchShows', methods=['GET', 'POST'])
def searchShows():
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT Name, Date_and_time, Located_at FROM shows")
    data = cursor.fetchall()
    if request.method == 'POST':
        if 'sortName' in request.form:
            if session['coin']:
                cursor.execute("SELECT Name, Date_and_time, Located_at FROM shows ORDER BY Name")
            elif not session['coin']:
                cursor.execute("SELECT Name, Date_and_time, Located_at FROM shows ORDER BY Name DESC")
            session['coin'] = not session['coin']
            data = cursor.fetchall()
            cursor.close()
            return render_template('searchShows.html', data=data)
        elif 'sortExhibit' in request.form:
            if session['coin']:
                cursor.execute("SELECT Name, Date_and_time, Located_at FROM shows ORDER BY Located_at")
            elif not session['coin']:
                cursor.execute("SELECT Name, Date_and_time, Located_at FROM shows ORDER BY Located_at DESC")
            session['coin'] = not session['coin']
            data = cursor.fetchall()
            cursor.close()
            return render_template('searchShows.html', data=data)
        elif 'sortTime' in request.form:
            if session['coin']:
                cursor.execute("SELECT Name, Date_and_time, Located_at FROM shows ORDER BY Date_and_time")
            elif not session['coin']:
                cursor.execute("SELECT Name, Date_and_time, Located_at FROM shows ORDER BY Date_and_time DESC")
            session['coin'] = not session['coin']
            data = cursor.fetchall()
            cursor.close()
            return render_template('searchShows.html', data=data)
        elif 'back' in request.form:
            cursor.close()
            return redirect(url_for('visitorHome'))
        elif 'search' in request.form:
            option = request.form['searchopt']
            if option == 'any':
                option = None
            name = request.form['searchname']
            if name == '':
                name = None
            else:
                name = "%" + name + "%"
            searchTime = request.form['datetime']
            if searchTime == '':
                searchTime = None
            else:
                searchTime = datetime.datetime.strptime(searchTime, '%Y-%m-%d')
            if name == "" and option == 'any' and searchTime == "":
                cursor.execute("SELECT Name, Date_and_time, Located_at FROM shows")
            else:
                cursor.execute("SELECT Name, Date_and_time, Located_at FROM shows WHERE (%s IS NULL OR Name LIKE %s) AND (%s IS NULL OR DATE(Date_and_time) = %s) AND (%s IS NULL OR Located_at = %s)", (name, name, searchTime, searchTime, option, option))
            data = cursor.fetchall()
            cursor.close()
            return render_template('searchShows.html', data=data)
        elif 'logvisit' in request.form:
            show_row = request.form['logvisit']
            if len(show_row) == 0:
                cursor.execute("SELECT Name, Date_and_time, Located_at FROM shows")
                data = cursor.fetchall()
                cursor.close()
                return render_template('searchShows.html', data=data)
            row = ast.literal_eval(show_row)
            show_name = row['name']
            show_exh = row['exhibit']
            show_date = row['date']
            show_datetime = datetime.datetime.strptime(show_date, '%Y-%m-%d %H:%M:%S')
            show_datetime = show_datetime.strftime('%Y-%m-%d %H:%M:%S')
            user_name = session['username']
            cursor.execute("SELECT Email FROM visitors WHERE Username = %s", (user_name))
            user_email = cursor.fetchone()
            user_email = user_email[0]

            cursor.execute(
                "SELECT Shows_name, Visitor_username, Time FROM visit_show WHERE Shows_name = %s AND Visitor_username = %s AND Time = %s",
                (show_name, user_name, show_datetime))
            noteHave = len(cursor.fetchall()) == 0
            if noteHave:
                cursor.execute("INSERT INTO visit_show (Shows_name, Visitor_username, Visitor_Email, Time) VALUES(%s, %s, %s, %s)", (show_name, user_name, user_email, show_datetime))
                conn.commit()
                cursor.close()
            return render_template('searchShows.html', data=data)
        elif 'logout' in request.form:
            cursor.close()
            return logout()
    cursor.close()
    return render_template('searchShows.html', data=data)

@app.route('/showhistory', methods=['GET', 'POST'])
def showHistory():
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT shows.Name, shows.Located_at, shows.Date_and_time "
                   "FROM (SELECT Shows_name, Time FROM visit_show WHERE visit_show.Visitor_username = %s) as foo "
                   "JOIN shows ON shows.Name = foo.Shows_name AND shows.Date_and_time = foo.Time;", (session['username']))
    data = cursor.fetchall()
    if request.method == 'POST':
        if 'sortName' in request.form:
            if session['coin']:
                cursor.execute("SELECT shows.Name, shows.Located_at, shows.Date_and_time "
                               "FROM (SELECT Shows_name, Time FROM visit_show WHERE visit_show.Visitor_username = %s) as foo "
                               "JOIN shows ON shows.Name = foo.Shows_name AND shows.Date_and_time = foo.Time "
                               "ORDER BY shows.Name;",(session['username']))
            elif not session['coin']:
                cursor.execute("SELECT shows.Name, shows.Located_at, shows.Date_and_time "
                               "FROM (SELECT Shows_name, Time FROM visit_show WHERE visit_show.Visitor_username = %s) as foo "
                               "JOIN shows ON shows.Name = foo.Shows_name AND shows.Date_and_time = foo.Time "
                               "ORDER BY shows.Name DESC;", (session['username']))
            session['coin'] = not session['coin']
            data = cursor.fetchall()
            cursor.close()
            return render_template('showHistory.html', data=data)
        elif 'sortExhibit' in request.form:
            if session['coin']:
                cursor.execute("SELECT shows.Name, shows.Located_at, shows.Date_and_time "
                               "FROM (SELECT Shows_name, Time FROM visit_show WHERE visit_show.Visitor_username = %s) as foo "
                               "JOIN shows ON shows.Name = foo.Shows_name AND shows.Date_and_time = foo.Time "
                               "ORDER BY shows.Located_at;",(session['username']))
            elif not session['coin']:
                cursor.execute("SELECT shows.Name, shows.Located_at, shows.Date_and_time "
                               "FROM (SELECT Shows_name, Time FROM visit_show WHERE visit_show.Visitor_username = %s) as foo "
                               "JOIN shows ON shows.Name = foo.Shows_name AND shows.Date_and_time = foo.Time "
                               "ORDER BY shows.Located_at DESC;", (session['username']))
            session['coin'] = not session['coin']
            data = cursor.fetchall()
            cursor.close()
            return render_template('showHistory.html', data=data)
        elif 'sortTime' in request.form:
            if session['coin']:
                cursor.execute("SELECT shows.Name, shows.Located_at, shows.Date_and_time "
                               "FROM (SELECT Shows_name, Time FROM visit_show WHERE visit_show.Visitor_username = %s) as foo "
                               "JOIN shows ON shows.Name = foo.Shows_name AND shows.Date_and_time = foo.Time "
                               "ORDER BY shows.Date_and_time;", (session['username']))
            elif not session['coin']:
                cursor.execute("SELECT shows.Name, shows.Located_at, shows.Date_and_time "
                               "FROM (SELECT Shows_name, Time FROM visit_show WHERE visit_show.Visitor_username = %s) as foo "
                               "JOIN shows ON shows.Name = foo.Shows_name AND shows.Date_and_time = foo.Time "
                               "ORDER BY shows.Date_and_time DESC;", (session['username']))
            session['coin'] = not session['coin']
            data = cursor.fetchall()
            cursor.close()
            return render_template('showHistory.html', data=data)
        elif 'search' in request.form:
            exh_option = request.form['searchopt']
            search_name = request.form['searchname']
            show_date = request.form['datetime']
            if exh_option == 'any':
                exh_option = None
            if search_name == '':
                search_name = None
            else:
                search_name = "%" + search_name + "%"
            if show_date == '':
                show_date = None
            else:
                show_date = datetime.datetime.strptime(show_date, '%Y-%m-%d')
            cursor.execute("SELECT * FROM "
                           "(SELECT shows.Name, shows.Located_at, shows.Date_and_time "
                           "FROM (SELECT Shows_name, Time FROM visit_show "
                           "WHERE visit_show.Visitor_username = %s) as foo "
                           "JOIN shows ON shows.Name = foo.Shows_name AND shows.Date_and_time = foo.Time) as boo "
                           "WHERE (%s IS NULL OR Name LIKE %s) AND (%s IS NULL OR Located_at = %s) "
                           "AND (%s IS NULL OR DATE(Date_and_time) = %s)", (session['username'], search_name, search_name, exh_option, exh_option, show_date, show_date))
            data = cursor.fetchall()
            cursor.close()
            return render_template('showHistory.html', data=data)
        elif 'back' in request.form:
            cursor.close()
            return redirect(url_for('visitorHome'))
        elif 'logout' in request.form:
            return redirect(url_for('logout'))
    return render_template('showHistory.html', data=data)

@app.route('/exhibithistory', methods=['GET', 'POST'])
def exhibitHistory():
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM "
                   "(SELECT foo.Exhibit_name, foo.Datetime, boo.cc FROM atlzoo.visit_exhibit AS foo "
                   "Left Join ( SELECT Exhibit_name, Count(*) as cc FROM atlzoo.visit_exhibit "
                   "WHERE visit_exhibit.Visitor_username = %s GROUP BY Exhibit_name ) AS boo "
                   "On foo.Exhibit_name = boo.Exhibit_name) as haa", (session['username']))
    data = cursor.fetchall()
    if request.method == 'POST':
        if 'sortName' in request.form:
            if session['coin']:
                cursor.execute("SELECT * FROM "
                               "(SELECT foo.Exhibit_name, foo.Datetime, boo.cc FROM atlzoo.visit_exhibit AS foo "
                               "Left Join ( SELECT Exhibit_name, Count(*) as cc FROM atlzoo.visit_exhibit "
                               "WHERE visit_exhibit.Visitor_username = %s GROUP BY Exhibit_name ) AS boo "
                               "On foo.Exhibit_name = boo.Exhibit_name) as haa ORDER BY haa.Exhibit_name",
                               (session['username']))
            elif not session['coin']:
                cursor.execute("SELECT * FROM "
                               "(SELECT foo.Exhibit_name, foo.Datetime, boo.cc FROM atlzoo.visit_exhibit AS foo "
                               "Left Join ( SELECT Exhibit_name, Count(*) as cc FROM atlzoo.visit_exhibit "
                               "WHERE visit_exhibit.Visitor_username = %s GROUP BY Exhibit_name ) AS boo "
                               "On foo.Exhibit_name = boo.Exhibit_name) as haa ORDER BY haa.Exhibit_name DESC",
                               (session['username']))
            session['coin'] = not session['coin']
            data = cursor.fetchall()
            cursor.close()
            return render_template('exhibitHistory.html', data=data)
        elif 'sortTime' in request.form:
            if session['coin']:
                cursor.execute("SELECT * FROM "
                               "(SELECT foo.Exhibit_name, foo.Datetime, boo.cc FROM atlzoo.visit_exhibit AS foo "
                               "Left Join ( SELECT Exhibit_name, Count(*) as cc FROM atlzoo.visit_exhibit "
                               "WHERE visit_exhibit.Visitor_username = %s GROUP BY Exhibit_name ) AS boo "
                               "On foo.Exhibit_name = boo.Exhibit_name) as haa ORDER BY haa.Datetime",
                               (session['username']))
            elif not session['coin']:
                cursor.execute("SELECT * FROM "
                               "(SELECT foo.Exhibit_name, foo.Datetime, boo.cc FROM atlzoo.visit_exhibit AS foo "
                               "Left Join ( SELECT Exhibit_name, Count(*) as cc FROM atlzoo.visit_exhibit "
                               "WHERE visit_exhibit.Visitor_username = %s GROUP BY Exhibit_name ) AS boo "
                               "On foo.Exhibit_name = boo.Exhibit_name) as haa ORDER BY haa.Datetime DESC",
                               (session['username']))
            session['coin'] = not session['coin']
            data = cursor.fetchall()
            cursor.close()
            return render_template('exhibitHistory.html', data=data)
        elif 'sortNumVisit' in request.form:
            if session['coin']:
                cursor.execute("SELECT * FROM "
                               "(SELECT foo.Exhibit_name, foo.Datetime, boo.cc FROM atlzoo.visit_exhibit AS foo "
                               "Left Join ( SELECT Exhibit_name, Count(*) as cc FROM atlzoo.visit_exhibit "
                               "WHERE visit_exhibit.Visitor_username = %s GROUP BY Exhibit_name ) AS boo "
                               "On foo.Exhibit_name = boo.Exhibit_name) as haa ORDER BY haa.cc",
                               (session['username']))
            elif not session['coin']:
                cursor.execute("SELECT * FROM "
                               "(SELECT foo.Exhibit_name, foo.Datetime, boo.cc FROM atlzoo.visit_exhibit AS foo "
                               "Left Join ( SELECT Exhibit_name, Count(*) as cc FROM atlzoo.visit_exhibit "
                               "WHERE visit_exhibit.Visitor_username = %s GROUP BY Exhibit_name ) AS boo "
                               "On foo.Exhibit_name = boo.Exhibit_name) as haa ORDER BY haa.cc DESC",
                               (session['username']))
            session['coin'] = not session['coin']
            data = cursor.fetchall()
            cursor.close()
            return render_template('exhibitHistory.html', data=data)
        elif 'search' in request.form:
            search_exh = request.form['exhopt']
            exh_date = request.form['datetime']
            max_num = request.form['max_num']
            min_num = request.form['min_num']
            print request.form
            if search_exh == 'anyExh':
                search_exh = None
            if exh_date == '':
                exh_date = None
            else:
                exh_date = datetime.datetime.strptime(exh_date, '%Y-%m-%d')
            if max_num == '' and min_num == '':
                max_num = None
                min_num = None
            elif max_num == '' and min_num > 0:
                max_num = None
            elif max_num > 0 and min_num == '':
                min_num = None
            cursor.execute("SELECT * FROM "
                       "(SELECT foo.Exhibit_name, foo.Datetime, boo.cc FROM atlzoo.visit_exhibit AS foo "
                       "Left Join ( SELECT Exhibit_name, Count(*) as cc FROM atlzoo.visit_exhibit "
                       "WHERE visit_exhibit.Visitor_username = %s GROUP BY Exhibit_name ) AS boo "
                       "On foo.Exhibit_name = boo.Exhibit_name) as haa "
                       "WHERE (%s IS NULL OR haa.Exhibit_name = %s) AND (%s IS NULL OR DATE(haa.Datetime) = %s) "
                       "AND (%s IS NULL OR haa.cc >= %s) AND (%s IS NULL OR haa.cc <= %s)",
                       (session['username'], search_exh, search_exh, exh_date, exh_date, min_num, min_num, max_num, max_num))
            data = cursor.fetchall()
            cursor.close()
            return render_template('exhibitHistory.html', data=data)
        elif 'back' in request.form:
            cursor.close()
            return redirect(url_for('visitorHome'))
        elif 'logout' in request.form:
            return redirect(url_for('logout'))
    return render_template('exhibitHistory.html', data=data)


"""
Visitor search animal page starts here
"""
@app.route('/searchAnimals', methods=['GET', 'POST'])
def searchAnimals():
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal")
    data = cursor.fetchall()
    if request.method == 'POST':
        if 'sortName' in request.form:
            if session['coin']:
                cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal ORDER BY Name")
                session['coin'] = False
            elif not session['coin']:
                cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal ORDER BY Name DESC")
                session['coin'] = True
            data = cursor.fetchall()
            cursor.close()
            return render_template('searchAnimals.html', data=data)
        elif 'sortSpecies' in request.form:
            if session['coin']:
                cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal ORDER BY Species")
                session['coin'] = False
            elif not session['coin']:
                cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal ORDER BY Species DESC")
                session['coin'] = True
            data = cursor.fetchall()
            cursor.close()
            return render_template('searchAnimals.html', data=data)
        elif 'sortExhibit' in request.form:
            if session['coin']:
                cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal ORDER BY Exhibit")
                session['coin'] = False
            elif not session['coin']:
                cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal ORDER BY Exhibit DESC")
                session['coin'] = True
            data = cursor.fetchall()
            cursor.close()
            return render_template('searchAnimals.html', data=data)
        elif 'sortAge' in request.form:
            if session['coin']:
                cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal ORDER BY Age")
                session['coin'] = False
            elif not session['coin']:
                cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal ORDER BY Age DESC")
                session['coin'] = True
            data = cursor.fetchall()
            cursor.close()
            return render_template('searchAnimals.html', data=data)
        elif 'sortType' in request.form:
            if session['coin']:
                cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal ORDER BY Type")
                session['coin'] = False
            elif not session['coin']:
                cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal ORDER BY Type DESC")
                session['coin'] = True
            data = cursor.fetchall()
            cursor.close()
            return render_template('searchAnimals.html', data=data)
        elif 'detail' in request.form:
            ani_row = request.form['detail']
            if len(ani_row) == 0:
                cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal")
                data = cursor.fetchall()
                cursor.close()
                return render_template('searchAnimals.html', data=data)
            else:
                session['detanimal'] = ani_row
                return redirect(url_for('animalDetail'))
        elif 'back' in request.form:
            cursor.close()
            return redirect(url_for('visitorHome'))
        elif 'search' in request.form:
            exh_option = request.form['exhopt']
            type_option = request.form['typeopt']
            search_name = request.form['searchname']
            search_spec = request.form['searchspec']
            max_age = int(request.form['max'])
            min_age = int(request.form['min'])
            if exh_option == 'anyExh':
                exh_option = None
            if type_option == 'anyType':
                type_option = None
            if search_name == '':
                search_name = None
            else:
                search_name = "%" + search_name + "%"
            if search_spec == '':
                search_spec = None
            else:
                search_spec = "%" + search_spec + "%"
            if max_age == 0 and min_age == 0:
                max_age = None
                min_age = None
            elif max_age == 0 and min_age > 0:
                max_age = None
            elif max_age > 0 and min_age == 0:
                min_age = None
            cursor.execute("SELECT Name, Species, Exhibit, Age, Type FROM animal WHERE"
                           + " (%s IS NULL OR Name LIKE %s) AND (%s IS NULL OR Species LIKE %s) "
                           + "AND (%s IS NULL OR Exhibit = %s) AND (%s IS NULL OR Age >= %s) "
                           + "AND (%s IS NULL OR Age <= %s) AND (%s IS NULL OR Type = %s)",
                           (search_name, search_name, search_spec, search_spec, exh_option, exh_option, min_age, min_age, max_age, max_age, type_option, type_option))
            data = cursor.fetchall()
            cursor.close()
            return render_template('searchAnimals.html', data=data)
        elif 'logout' in request.form:
            cursor.close()
            return logout()
    cursor.close()
    return render_template('searchAnimals.html', data=data)

@app.route('/animalDetail', methods=['GET', 'POST'])
def animalDetail():
    conn = mysql.connect()
    cursor = conn.cursor()
    notenote = session['detanimal']
    message = Markup(str(notenote))
    flash(message)
    if request.method == 'POST':
        if 'back' in request.form:
            cursor.close()
            print 'haha'
            return redirect(url_for('searchAnimals'))
        elif 'logout' in request.form:
            return redirect(url_for('logout'))
    return render_template('animalDetail.html')
"""
Logout page starts here
"""
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('username', None)
    session.clear()
    if request.method == 'POST' and 'toLog' in request.form:
        return redirect(url_for('login'))

    return render_template('logout.html')

if __name__ == '__main__':
    app.run()


