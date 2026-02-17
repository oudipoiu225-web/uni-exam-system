import os
from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "secret_key_for_session" # برای امنیت ورود کاربران

# اتصال به دیتابیس جدیدت
MONGO_URI = "mongodb+srv://kimarka54_db_user:ceH1JU7iQrRKD6gx@cluster0.9kfmbzs.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client.get_database("exam_system")
questions_coll = db.get_collection("questions")
users_coll = db.get_collection("students")

@app.route('/')
def home():
    # اگر کاربر قبلاً وارد شده، بره به صفحه آزمون
    if 'student_id' in session:
        return redirect(url_for('exam'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    student_id = request.form.get('student_id')
    # اینجا می‌تونی چک کنی که آیا این کد توی دیتابیس هست یا نه
    # فعلاً برای تست، هر کدی بزنه قبول می‌کنیم
    if student_id:
        session['student_id'] = student_id
        return redirect(url_for('exam'))
    return redirect(url_for('home'))

@app.route('/exam')
def exam():
    if 'student_id' not in session:
        return redirect(url_for('home'))
    
    # گرفتن تمام سوالات از دیتابیس
    all_questions = list(questions_coll.find())
    return render_template('exam.html', questions=all_questions)

@app.route('/logout')
def logout():
    session.pop('student_id', None)
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
