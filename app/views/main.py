import os
from pytz import utc
from flask import Flask, request, render_template, flash, redirect, url_for, session, send_file
from flask import Blueprint, g
from flask_mysqldb import MySQL
from flask_session import Session
from twilio.rest import Client
from flask_apscheduler import APScheduler
from datetime import datetime
from app import *

main = Blueprint('main', __name__)
# account_sid = account_sid goes here
# auth_token = auth_token goes here
client = Client(account_sid, auth_token)
scheduler = APScheduler()
app.config['SCHEDULER_TIMEZONE'] = utc
scheduler.init_app(app)
scheduler.start()

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

@main.route("/error_log")
def error_log():
    errors = query_db("SELECT * from error_log;")
    if errors is None:
        errors = []
    return render_template("error_logs.html", **locals())

def send_sms(phone_number):
    count = 0
    while True:
        message = client.messages \
                        .create(
                             body="REMINDER: Your name is JOHN!",
                             from_='+17274931881',
                             to=phone_number
                         )
        if message.error_code:
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
