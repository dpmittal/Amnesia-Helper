import os
from flask import Flask, request, render_template, flash, redirect, url_for, session, send_file
from flask import Blueprint, g
from flask_mysqldb import MySQL
from flask_session import Session
from twilio.rest import Client
from app import *

main = Blueprint('main', __name__)
account_sid = #account_sid
auth_token = #auth_token
client = Client(account_sid, auth_token)


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
            execute_db("MODIFY phone_numbers SET phone_number=%s, start_time=%s, end_time=%s where id=1;", (
                phone_number,
                start_time,
                end_time,
            ))
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
