import os
from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = "my_super_secret_key_123" # برای مدیریت نشست‌های کاربر

# --- اتصال به دیتابیس MongoDB شما ---
MONGO_URI = "mongodb+srv://kimarka54_db_user:ceH1JU7iQrRKD6gx@cluster0.9kfmbzs.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client.get_database("exam_system")
questions_coll = db.get_collection("questions")
results_coll = db.get_collection("results")

# --- مسیر اصلی: صفحه ورود ---
@app.route('/')
def home():
    if 'student_id' in session:
        return redirect(url_for('exam'))
    return render_template('login.html')

# --- عملیات ورود ---
@app.route('/login', methods=['POST'])
def login():
    student_id = request.form.get('student_id')
    if student_id:
        session['student_id'] = student_id
        return redirect(url_for('exam'))
    return redirect(url_for('home'))

# --- صفحه آزمون ---
@app.route('/exam')
def exam():
    if 'student_id' not in session:
        return redirect(url_for('home'))
    
    # دریافت تمام سوالات از دیتابیس
    all_questions = list(questions_coll.find())
    return render_template('exam.html', questions=all_questions)

# --- ثبت و تصحیح آزمون ---
@app.route('/submit', methods=['POST'])
def submit():
    if 'student_id' not in session:
        return redirect(url_for('home'))
    
    score = 0
    student_id = session['student_id']
    all_questions = list(questions_coll.find())
    total_questions = len(all_questions)
    
    # بررسی جواب‌ها
    for q in all_questions:
        question_id = str(q['_id'])
        # دریافت جوابی که کاربر انتخاب کرده (ایندکس 0 تا 3)
        user_answer = request.form.get(f"q_{question_id}")
        
        if user_answer is not None:
            if int(user_answer) == q.get('correct_index'):
                score += 1
    
    # ذخیره نتیجه در دیتابیس برای شما (ادمین)
    results_coll.insert_one({
        "student_id": student_id,
        "score": score,
        "total": total_questions
    })
    
    return f"""
    <div style="direction: rtl; text-align: center; margin-top: 50px; font-family: Tahoma;">
        <h2>آزمون با موفقیت ثبت شد.</h2>
        <p>نمره شما: {score} از {total_questions}</p>
        <a href='/logout'>خروج از سامانه</a>
    </div>
    """

# --- پنل ادمین برای وارد کردن سوالات ---
@app.route('/admin_panel', methods=['GET', 'POST'])
def admin_panel():
    if request.method == 'POST':
        raw_text = request.form.get('raw_questions')
        # فرمت: سوال * گزینه1 * گزینه2 * گزینه3 * گزینه4 * ایندکس جواب درست
        lines = raw_text.strip().split('\n')
        added_count = 0
        
        for line in lines:
            if '*' in line:
                parts = line.split('*')
                if len(parts) >= 6:
                    q_text = parts[0].strip()
                    options = [p.strip() for p in parts[1:5]]
                    correct_idx = int(parts[5].strip())
                    
                    questions_coll.insert_one({
                        "text": q_text,
                        "options": options,
                        "correct_index": correct_idx
                    })
                    added_count += 1
        
        return f"تعداد {added_count} سوال با موفقیت اضافه شد! <a href='/admin_panel'>بازگشت</a>"
    
    return '''
    <div style="direction: rtl; text-align: center; font-family: Tahoma;">
        <h2>پنل افزودن سوالات</h2>
        <form method="post">
            <p>سوالات را با فرمت زیر وارد کنید (هر سوال در یک خط):</p>
            <code>متن سوال * گزینه1 * گزینه2 * گزینه3 * گزینه4 * عدد گزینه درست(0-3)</code><br><br>
            <textarea name="raw_questions" rows="10" cols="70" placeholder="مثال: پایتون چیست؟ * زبان * میوه * ماشین * کتاب * 0"></textarea><br><br>
            <button type="submit">آپلود سوالات</button>
        </form>
    </div>
    '''

# --- خروج از حساب ---
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
