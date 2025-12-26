import os
import datetime
import pytz
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'SUPER_SECRET_KEY_999'

# Твоя база данных на Render
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://lifepill_db_user:6AOp4tRkMjZveS4s6y6SsZQtJGtrvmmT@dpg-d56qi6shg0os73as97bg-a/lifepill_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Настройки почты
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'ikthomeworkproj5@gmail.com'
app.config['MAIL_PASSWORD'] = 'udxb ikds zdlv jhqp' 
app.config['MAIL_DEFAULT_SENDER'] = 'ikthomeworkproj5@gmail.com'

db = SQLAlchemy(app)
mail = Mail(app)

# Модели на основе твоего кода
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    timezone = db.Column(db.String(50), default='Europe/Moscow')

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    med_name = db.Column(db.String(100), nullable=False)
    time_str = db.Column(db.String(5), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    frequency = db.Column(db.String(10), default='daily')
    slot = db.Column(db.Integer, default=1)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@app.route('/')
def index():
    user = User.query.get(session.get('user_id')) if 'user_id' in session else None
    return render_template('index.html', 
                           user_logged_in=bool(user),
                           username=user.username if user else None,
                           user_email=user.email if user else None,
                           user_timezone=user.timezone if user else 'Europe/Moscow',
                           timezones=[('Europe/Moscow', 'Москва (GMT+3)'), ('Asia/Almaty', 'Алматы (GMT+5)')])

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = User(username=request.form['username'], email=request.form['email'], 
                    password=generate_password_hash(request.form['password']))
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# API для твоего script.js
@app.route('/api/set_reminder', methods=['POST'])
def set_reminder():
    data = request.json
    new_rem = Reminder(med_name=data['med_name'], time_str=data['reminder_time'], 
                       email=data['reminder_email'], frequency=data['frequency'], 
                       slot=int(data['slot']), user_id=session['user_id'])
    db.session.add(new_rem)
    db.session.commit()
    return jsonify({'message': 'Протокол установлен!'})

@app.route('/api/get_reminders')
def get_reminders():
    rems = Reminder.query.filter_by(user_id=session['user_id']).all()
    return jsonify([{'id': r.id, 'med_name': r.med_name, 'time': r.time_str, 'slot': r.slot, 'frequency': r.frequency, 'email': r.email} for r in rems])

@app.route('/api/delete_reminder/<int:id>', methods=['POST'])
def delete_reminder(id):
    rem = Reminder.query.filter_by(id=id, user_id=session['user_id']).first()
    if rem:
        db.session.delete(rem)
        db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/cron-check-secret-777')
def cron_check():
    # Простейшая логика рассылки для проверки
    return "OK", 200

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
