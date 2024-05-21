from flask import Flask, render_template, request
import ibm_db
import os
from passlib.hash import sha256_crypt

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Database Connection Functions
def connect_to_db():
    conn_str = os.environ.get("DB_CONNECTION_STRING")
    conn = ibm_db.connect(conn_str, "", "")
    return conn

def close_db_connection(conn):
    if conn is not None:
        ibm_db.close(conn)

@app.teardown_appcontext
def teardown_appcontext(exception):
    conn = getattr(Flask, '_database', None)
    close_db_connection(conn)


@app.route('/')
def index():
    return render_template("index.html")

@app.route('/login')
def login():
    return render_template("login.html")

@app.route('/register')
def register():
    return render_template("register.html")


@app.route('/About-Us')
def About_Us():
    return render_template("About-Us.html")

@app.route('/register1', methods=['POST'])
def register_user():
    x = [x for x in request.form.values()]
    name = x[0]
    email = x[1]
    password = sha256_crypt.hash(x[2])

    conn = connect_to_db()
    cursor = ibm_db.prepare(conn, "SELECT * FROM REGISTER WHERE EMAIL = ?")
    ibm_db.bind_param(cursor, 1, email)
    ibm_db.execute(cursor)
    account = ibm_db.fetch_assoc(cursor)

    if account:
        close_db_connection(conn)
        return render_template('login.html', pred="You are already a member. Please log in using your details.")
    else:
        insert_stmt = "INSERT INTO REGISTER (NAME, EMAIL, PASSWORD) VALUES (?, ?, ?)"
        insert_cursor = ibm_db.prepare(conn, insert_stmt)
        ibm_db.bind_param(insert_cursor, 1, name)
        ibm_db.bind_param(insert_cursor, 2, email)
        ibm_db.bind_param(insert_cursor, 3, password)
        ibm_db.execute(insert_cursor)
        close_db_connection(conn)
        return render_template('login.html', pred="Registration successful. Please log in using your details.")

@app.route('/login1', methods=['POST'])
def login_user():
    email = request.form['EMAIL']
    password = request.form['PASSWORD']

    conn = connect_to_db()
    cursor = ibm_db.prepare(conn, "SELECT * FROM REGISTER WHERE EMAIL = ?")
    ibm_db.bind_param(cursor, 1, email)
    ibm_db.execute(cursor)
    account = ibm_db.fetch_assoc(cursor)

    if account and sha256_crypt.verify(password, account['PASSWORD']):
        close_db_connection(conn)
        return render_template('login.html', pred="Login successful.")
    else:
        close_db_connection(conn)
        return render_template('login.html', pred="Login unsuccessful. Incorrect email or password.")


if __name__ == "__main__":
    app.run(debug=True)
