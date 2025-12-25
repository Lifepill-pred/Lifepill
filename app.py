import os
import datetime
import pytz
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# ==========================================
# ⚙️ КОНФИГУРАЦИЯ (НАСТРОЙ ПОД СЕБЯ)
# ==========================================
app.config['SECRET_KEY'] = 'SUPER_SECRET_KEY_999'

# База данных (SQLite)
basedir = os.path.abspath(os.path.dirname(__file__))
# Было (удаляем):
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'site.db')

# Стало (вставляем):
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://lifepill_db_user:6AOp4tRkMjZveS4s6y6SsZQtJGtrvmmT@dpg-d56qi6shg0os73as97bg-a/lifepill_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Настройки почты Gmail (ВСТАВЬ СВОЙ ПАРОЛЬ ПРИЛОЖЕНИЯ)
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
    reminders = db.relationship('Reminder', backref='owner', lazy=True)

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    med_name = db.Column(db.String(100), nullable=False)
    time_str = db.Column(db.String(5), nullable=False) # Формат "HH:MM"
    email = db.Column(db.String(120), nullable=False)
    frequency = db.Column(db.String(10), default='daily')
    sent = db.Column(db.Boolean, default=False)
    day_sent = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    med_name = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    status = db.Column(db.String(10), default='pending') # pending, received, skipped
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# ==========================================
# ⏰ ЛОГИКА ПРОВЕРКИ (ШЕДУЛЕР)
# ==========================================
def check_all_reminders():
    with app.app_context():
        utc_now = datetime.datetime.now(pytz.utc)
        print(f"[{utc_now}] Запуск проверки...")
        
        users = User.query.all()
        for user in users:
            try:
                user_tz = pytz.timezone(user.timezone)
                local_now = utc_now.astimezone(user_tz)
                current_time = local_now.strftime('%H:%M')
                
                # Сброс ежедневных отметок в полночь
                if current_time == "00:00":
                    for r in Reminder.query.filter_by(user_id=user.id, frequency='daily').all():
                        r.day_sent = False
                    db.session.commit()

                # Ищем напоминания на текущую минуту
                reminders = Reminder.query.filter_by(user_id=user.id, time_str=current_time).all()
                for rem in reminders:
                    if rem.frequency == 'daily' and rem.day_sent: continue
                    if rem.frequency == 'once' and rem.sent: continue
                    
                    # Записываем в историю
                    new_h = History(med_name=rem.med_name, user_id=user.id, status='pending')
                    db.session.add(new_h)
                    db.session.commit()
                    
                    # Отправляем письмо
                    msg = Message("LifePill: Пора принять лекарство!", recipients=[rem.email])
                    msg.body = f"Напоминание: {rem.med_name}. Отметьте прием в приложении."
                    mail.send(msg)
                    print(f"Письмо отправлено для {user.username} ({rem.med_name})")
                    
                    if rem.frequency == 'daily': rem.day_sent = True
                    else: rem.sent = True
                    db.session.commit()
            except Exception as e:
                print(f"Ошибка при обработке {user.username}: {e}")

# ==========================================
# 🌐 РОУТЫ (СТРАНИЦЫ САЙТА)
# ==========================================

@app.route('/')
def index():
    if 'user_id' in session:
        user_reminders = Reminder.query.filter_by(user_id=session['user_id']).all()
        return render_template('index.html', reminders=user_reminders)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed_pw = generate_password_hash(request.form['password'])
        new_user = User(
            username=request.form['username'],
            email=request.form['email'],
            password=hashed_pw,
            timezone=request.form.get('timezone', 'Europe/Moscow')
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Успешная регистрация!')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id
            return redirect(url_for('index'))
        flash('Неверное имя пользователя или пароль')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/add_reminder', methods=['POST'])
def add_reminder():
    if 'user_id' not in session: return redirect(url_for('login'))
    new_rem = Reminder(
        med_name=request.form['med_name'],
        time_str=request.form['time'],
        email=User.query.get(session['user_id']).email,
        user_id=session['user_id']
    )
    db.session.add(new_rem)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/history')
def history():
    if 'user_id' not in session: return redirect(url_for('login'))
    user_history = History.query.filter_by(user_id=session['user_id']).all()
    return render_template('history.html', history=user_history)

# СЕКРЕТНЫЙ РОУТ ДЛЯ CRON-JOB.ORG
@app.route('/cron-check-secret-777')
def cron_trigger():
    check_all_reminders()
    return "OK", 200

# Инициализация БД
with app.app_context():
    db.create_all()

if __name__ == '__main__':

    app.run(debug=True)
