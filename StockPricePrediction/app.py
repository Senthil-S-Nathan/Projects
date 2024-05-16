from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import MySQLdb.cursors
import re
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objs as go
from prophet import Prophet
from prophet.plot import plot_plotly,plot_forecast_component_plotly
from datetime import datetime, timedelta
import csv



app = Flask(__name__)
app.config['SECRET_KEY'] = 'abc123'


app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '12345'
app.config['MYSQL_DB'] = 'stuser'
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
mysql = MySQL(app)

# Loading Home Page


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/team")
def team():
    return render_template("team.html")

@app.route("/why")
def why():
    return render_template("why.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and 'mail' in request.form and 'password' in request.form:
        mail = request.form['mail']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE mail = %s', (mail,))
        account = cursor.fetchone()
        if account and check_password_hash(account['password_hash'], password):
            # Password matches, proceed with login
            user_name = account['user_name']
            session['loggedin'] = True
            session['mail'] = account['mail']  
            session['user_name'] = account['user_name']  
            flash(f"Welcome {user_name} :)")
            return redirect(url_for("home"))
        else:
            # Invalid email or password
            flash('Incorrect email or password!')
            return redirect(url_for("login"))

    return render_template('login.html')

@app.route('/logout')
def logout():
	session.pop('loggedin', None)
	session.pop('mail', None)
	session.pop('user_name', None)
	flash('Logged out successfully!')
	return redirect(url_for('index'))

@app.route('/Sign up', methods=['GET', 'POST'])
def Signup():
    msg = ''
    if request.method == 'POST' and 'user_name' in request.form and 'password1' in request.form and 'password2' in request.form and 'mail' in request.form:
        mail = request.form['mail']
        username = request.form['user_name']
        password1 = request.form['password1']
        password2 = request.form['password2']

        con = mysql.connection.cursor()
        con.execute('SELECT * FROM users WHERE mail = %s', (mail,))
        mysql.connection.commit()
        account = con.fetchone()
        con.execute('SELECT * FROM users WHERE user_name = %s', (username,))
        mysql.connection.commit()
        user_name_exist = con.fetchone()
        if account:
            flash('Account already exists! Try to Login!!')
            return redirect(url_for("index"))
        elif user_name_exist:
            flash('Username already exists! Try another name.')
            return redirect(url_for("Signup"))
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', mail):
            flash('Invalid email address!')
            return redirect(url_for("Signup"))
        elif password1 != password2:
            flash("Passwords don't match", category='warning')
            return redirect(url_for("Signup"))
        elif not re.match(r'[A-Za-z0-9]+', username):
            flash('Username must contain only characters and numbers!')
        else:
            # Hash the password before storing it in the database
            hashed_password = generate_password_hash(password1)
            con = mysql.connection.cursor()
            sql = "INSERT INTO users (mail, user_name, password_hash) VALUES (%s, %s, %s)"
            con.execute(sql, (mail, username, hashed_password))
            mysql.connection.commit()
            con.close()
            flash('User details added. Now you can login.')
            return redirect(url_for("login"))
    return render_template('reg.html')

##############################################################################################################


def get_company_data(company_name, start, end):
    try:
        data = yf.download(company_name, start=start, end=end, auto_adjust=True)
        return data, company_name
    except ValueError:
        print("Invalid symbol or data not available")
        return None, None


def symbolToName(company_name):
    with open('static/nasdaq.csv', 'r') as file:
     	csv_data = list(csv.reader(file))
    for i in csv_data:
            if i[0] == company_name:
                return i[1]

@app.route('/chart', methods=['GET', 'POST'])
def chart():
    with open('static/nasdaq.csv', 'r') as file:
     	csv_data = list(csv.reader(file))
        #Skip the header row
        # next(csv_reader)

    if request.method == 'POST':
        company_name = request.form.get('company_name')
        cname = symbolToName(company_name)
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        data, name = get_company_data(company_name, start_date, end_date)

        if data is not None:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=data.index, y=data['Open'], mode="lines", name='Open Price', line=dict(color="blue", width=2)))
            fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='Close Price', line=dict(color='red', width=2)))
            fig.update_layout(title_text=f'Open and Close Prices of {cname}', xaxis_title='Time (in days)', yaxis_title='Price (in USD.)')
            plot_div = fig.to_html(full_html=False)

            # Set show_table_button to True only if the plot is visualized
            return render_template('chart.html', plot_div=plot_div, show_table_button=True, company_name=company_name, start_date=start_date, end_date=end_date, csv_data=csv_data)

    # Render the initial form with show_table_button set to False
    return render_template('chart.html', plot_div=None, show_table_button=False, csv_data=csv_data)



@app.route('/view_table', methods=['POST'])
def view_table():
    company_name = request.form.get('company_name')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    data, name = get_company_data(company_name, start_date, end_date)
    cname = symbolToName(company_name)
    
    return render_template('table_view.html', data=data, cname = cname)


@app.route('/forecast', methods=['GET', 'POST'])
def forecast():
    with open('static/nasdaq.csv', 'r') as file:
     	csv_data = list(csv.reader(file))
        
    if request.method == 'POST':
        # Get the company name from the user
        company_name = request.form.get('company_name')
        cname = symbolToName(company_name)

        # Get the number of days for forecasting from the user, default to 10 if not provided
        forecast_days = int(request.form.get('forecast_days'))

        # Calculate the current date
        current_date = datetime.now()

        # Fetch past 365 days actual data for the specified company
        start_date_actual = (current_date - timedelta(days=365)).strftime('%Y-%m-%d')
        end_date_actual = current_date
        actual_data, _ = get_company_data(company_name, start_date_actual, end_date_actual)

        if actual_data is not None:
            # Forecast into the future based on the user-input forecast_days
            model = Prophet()
            datas = actual_data.reset_index().rename(columns={'Date': 'ds', 'Close': 'y'})
            model.fit(datas)

            future = model.make_future_dataframe(periods=forecast_days)
            forecast = model.predict(future)

            train = forecast.iloc[:len(datas) + 1, :]
            predicted = forecast.iloc[len(datas):, :]

            figp = plot_plotly(model, train)
            figp.update_layout(title=f'Forecast for {forecast_days} days from {current_date.strftime("%Y-%m-%d")}')
            figp.add_trace(go.Scatter(x=predicted['ds'], y=predicted['yhat'], mode='lines', line=dict(color='green')))
            
            # Do not use full_html=False
            plot_div = figp.to_html(full_html=False)

            return render_template('forecast.html', plot_div=plot_div, show_table_button=True, cname = cname, company_name=company_name, periods=forecast_days, csv_data=csv_data)

    # Render the initial form
    return render_template('forecast.html', plot_div=None, show_table_button=False, csv_data=csv_data)



@app.route('/forecast_table', methods=['POST'])
def forecast_table():
    if request.method == 'POST':
        # Get the company name from the form data
        company_name = request.form.get('company_name')
        cname = symbolToName(company_name)


        # Get the number of days for forecasting from the form data, default to 10 if not provided
        forecast_days = int(request.form.get('forecast_days'))

        # Calculate the current date
        current_date = datetime.now()

        # Fetch past 365 days actual data for the specified company
        start_date_actual = (current_date - timedelta(days=365)).strftime('%Y-%m-%d')
        end_date_actual = current_date
        actual_data, _ = get_company_data(company_name, start_date_actual, end_date_actual)

        if actual_data is not None:
            # Forecast into the future based on the user-input forecast_days
            model = Prophet()
            datas = actual_data.reset_index().rename(columns={'Date': 'ds', 'Close': 'y'})
            model.fit(datas)

            future = model.make_future_dataframe(periods=forecast_days)
            forecast = model.predict(future)

            train = forecast.iloc[:len(datas) + 1, :]
            predicted = forecast.iloc[len(datas):, :]

            # Extract the last column values of datas and forecast
            datas_last_column = datas.iloc[:, -1]
            predicted_last_column = predicted.iloc[:, -1]

            # Combine the last column values into a dictionary
            data = {
				'Forecast Date': predicted['ds'].tolist(),
                'Forecast': predicted_last_column.tolist()
            }

            # Render the forecast table view template with the combined data
            return render_template('table_view_forecast.html', data=data, cname = cname)

    # Handle other HTTP methods or errors as needed


#############################################################################################################


if (__name__ == '__main__'):
    app.secret_key = "abc123"
    app.run(debug=True)
