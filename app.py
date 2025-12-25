import os
import datetime
import pytz
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# ==========================================
# ⚙️ НАСТРОЙКИ (Render + Твоя Postgres)
# ==========================================
app.config['SECRET_KEY'] = 'SUPER_SECRET_KEY_999'

# Твоя ссылка на базу данных (уже исправленная для Flask)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://lifepill_db_user:6AOp4tRkMjZveS4s6y6SsZQtJGtrvmmT@dpg-d56qi6shg0os73as97bg-a/lifepill_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Настройка сессий (чтобы не вылетало сразу после входа)
app.config['SESSION_PERMANENT'] = True
app.permanent_session_lifetime = datetime.timedelta(days=7)

# Настройки почты (твои данные)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'ikthomeworkproj5@gmail.com'
app.config['MAIL_PASSWORD'] = 'udxb ikds zdlv jhqp' 
app.config['MAIL_DEFAULT_SENDER'] = 'ikthomeworkproj5@gmail.com'

db = SQLAlchemy(app)
mail = Mail(app)

# ==========================================
# 📊 МОДЕЛИ БАЗЫ ДАННЫХ
# ==========================================
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
    day_sent = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# ==========================================
# 🌐 РОУТЫ (ЛОГИКА САЙТА)
# ==========================================

@app.route('/')
def index():
    # Если в сессии нет ID пользователя, отправляем на логин
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_reminders = Reminder.query.filter_by(user_id=session['user_id']).all()
    return render_template('index.html', reminders=user_reminders)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed_pw = generate_password_hash(request.form['password'])
        try:
            new_user = User(
                username=request.form['username'],
                email=request.form['email'],
                password=hashed_pw
            )
            db.session.add(new_user)
            db.session.commit()
            flash('Регистрация успешна! Теперь войдите.')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Ошибка! Возможно, такой email или ник уже занят.')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session.permanent = True
            session['user_id'] = user.id
            return redirect(url_for('index'))
        flash('Неверный логин или пароль')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/add_reminder', methods=['POST'])
def add_reminder():
    if 'user_id' not in session: 
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    new_rem = Reminder(
        med_name=request.form['med_name'],
        time_str=request.form['time'],
        email=user.email,
        user_id=user.id
    )
    db.session.add(new_rem)
    db.session.commit()
    return redirect(url_for('index'))

# СЕКРЕТНЫЙ РОУТ ДЛЯ CRON-JOB.ORG (Запуск раз в минуту)
@app.route('/cron-check-secret-777')
def cron_check():
    utc_now = datetime.datetime.now(pytz.utc)
    users = User.query.all()
    for user in users:
        try:
            user_tz = pytz.timezone(user.timezone)
            local_now = utc_now.astimezone(user_tz)
            current_time = local_now.strftime('%H:%M')
            
            reminders = Reminder.query.filter_by(user_id=user.id, time_str=current_time, day_sent=False).all()
            for rem in reminders:
                msg = Message("LifePill: Время принять лекарство!", recipients=[rem.email])
                msg.body = f"Пора принять лекарство: {rem.med_name}"
                mail.send(msg)
                rem.day_sent = True
                db.session.commit()
        except:
            continue
    return "Checked", 200

# Инициализация таблиц в Postgres
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
