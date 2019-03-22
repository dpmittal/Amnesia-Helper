import os
import time
from pytz import utc
from flask import Flask, request, render_template, flash, redirect, url_for, session, send_file
from flask import Blueprint, g
from flask_mysqldb import MySQL
from flask_session import Session
from twilio.rest import Client
from flask_apscheduler import APScheduler
from datetime import datetime
from app import *

# Bluprint Initialization
main = Blueprint('main', __name__)

# Twilio Auth Setup
# account_sid = account_sid goes here
# auth_token = auth_token goes here
client = Client(account_sid, auth_token)

# Scheduler Set-up for scheduling reminders
scheduler = APScheduler()
app.config['SCHEDULER_TIMEZONE'] = utc
scheduler.init_app(app)
scheduler.start()

# Start of Timer as soon as the App Starts
st_time = time.time()

# Scheduling Reminders at Startup by fetching Data from Database
@app.before_first_request
def at_startup():
    query = query_db("SELECT * from phone_numbers;")
    if query is not None:
        start = datetime.strptime(str(query[0][2]), '%H:%M:%S').time()
        end = datetime.strptime(str(query[0][3]), '%H:%M:%S').time()
        for i in range(24):
            value = datetime.strptime(str(i)+":00:00", '%H:%M:%S').time()
            if start>end:
                if value<start and value>end:
                    scheduler.add_job(func=send_sms, trigger='cron', args=[query[0][1]], hour=i, id='j'+str(i))
            else:
                if value<start or value>end:
                    scheduler.add_job(func=send_sms, trigger='cron', args=[query[0][1]], hour=i, id='j'+str(i))

# Index Page where the user adds or modifies personal details
@main.route('/', methods=['GET', 'POST'])
def index():
    if request.method=="POST":
        phone_number = request.form["phone_number"]
        start_time = request.form["start_time"]
        end_time = request.form["end_time"]
        p = query_db("SELECT * FROM phone_numbers;")
        if p is None:
            execute_db("INSERT INTO phone_numbers(phone_number, start_time, end_time) VALUES (%s, %s, %s);", (
                phone_number,
                start_time,
                end_time,
            ))
        else:
            execute_db("UPDATE phone_numbers SET phone_number=%s, start_time=%s, end_time=%s where id=1;", (
                phone_number,
                start_time,
                end_time,
            ))

        # Empties the Schedule Queue and reloads the queue according to the modified data
        scheduler.remove_all_jobs()
        query = query_db("SELECT * from phone_numbers;")
        start = datetime.strptime(str(query[0][2]), '%H:%M:%S').time()
        end = datetime.strptime(str(query[0][3]), '%H:%M:%S').time()
        for i in range(24):
            value = datetime.strptime(str(i)+":00:00", '%H:%M:%S').time()
            if start>end:
                if value<start and value>end:
                    scheduler.add_job(func=send_sms, trigger='cron', args=[phone_number], hour=i, id='j'+str(i))
            else:
                if value<start or value>end:
                    scheduler.add_job(func=send_sms, trigger='cron', args=[phone_number], hour=i, id='j'+str(i))
        flash("Successfully Added/Modified Number", "success")
        return redirect(url_for('main.index'))
    else:
        phone_number = query_db("SELECT * from phone_numbers;")
        if phone_number is None:
            phone_number = []
        return render_template("main.html", **locals())

# Page to display error log as well as the App execution time
@main.route("/error_log")
def error_log():
    errors = query_db("SELECT * from error_log;")

    # Calculating app Execution time (in hours)
    time_execution = int((time.time() - st_time)/3600)
    if errors is None:
        errors = []
    return render_template("error_logs.html", **locals())

# Handler to interact with Twilio to send Reminders to the number provided as the argument
def send_sms(phone_number):
    count = 0
    while True: # Loop to make 5 tries if sending reminders fails

        # Sending messages to the provided number
        message = client.messages \
                        .create(
                             body="REMINDER: Your name is JOHN!",
                             from_='+17274931881',
                             to=phone_number
                         )
        if message.error_code: # Inserts into the error log if sending reminder fails
            execute_db("INSERT INTO error_log(error_code, error_message, time) VALUES (%s, %s, %s);", (
                message.error_code,
                message.error_message,
                message.date_updated,
            ))
            count+=1
            if count==5:
                break
            else:
                continue
        else:
            break
