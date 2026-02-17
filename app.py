import os
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_very_secret_key_for_a_secure_exam_system"

# --- اتصال به دیتابیس MongoDB ---
# اطمینان حاصل کنید که اطلاعات اتصال شما صحیح است
MONGO_URI = "mongodb+srv://kimarka54_db_user:ceH1JU7iQrRKD6gx@cluster0.9kfmbzs.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client.get_database("exam_system_pro") # یک دیتابیس جدید برای نسخه پیشرفته
users_coll = db.get_collection("users")
exams_coll = db.get_collection("exams")
questions_coll = db.get_collection("questions")
results_coll = db.get_collection("results")

# --- Decorators برای کنترل دسترسی ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("برای دسترسی به این صفحه باید وارد شوید.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("برای دسترسی به این صفحه باید به عنوان ادمین وارد شوید.", "warning")
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash("شما دسترسی ادمین ندارید.", "danger")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# --- قالب‌های HTML (برای سادگی در خود کد قرار داده شده) ---
def render(template_name, **context):
    templates = {
        "layout.html": """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>سیستم آزمون آنلاین</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.rtl.min.css">
    <style> 
        @import url('https://fonts.googleapis.com/css2?family=Vazirmatn&display=swap');
        body { font-family: 'Vazirmatn', sans-serif; } 
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">آزمون آنلاین</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    {% if 'user_id' in session %}
                        {% if session['role'] == 'admin' %}
                            <li class="nav-item"><a class="nav-link" href="/admin">پنل ادمین</a></li>
                        {% endif %}
                        <li class="nav-item"><a class="nav-link" href="/dashboard">داشبورد</a></li>
                        <li class="nav-item"><a class="nav-link" href="/logout">خروج</a></li>
                    {% else %}
                        <li class="nav-item"><a class="nav-link" href="/login">ورود</a></li>
                        <li class="nav-item"><a class="nav-link" href="/register">ثبت نام</a></li>
                    {% endif %}
                </ul>
            </div>
        </div>
    </nav>
    <div class="container mt-4">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        {% block content %}{% endblock %}
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
        """,
        "register.html": """
{% extends "layout.html" %}
{% block content %}
<h2>ثبت نام</h2>
<form method="post">
    <div class="mb-3">
        <label>نام کامل:</label>
        <input type="text" name="full_name" class="form-control" required>
    </div>
    <div class="mb-3">
        <label>نام کاربری:</label>
        <input type="text" name="username" class="form-control" required>
    </div>
    <div class="mb-3">
        <label>رمز عبور:</label>
        <input type="password" name="password" class="form-control" required>
    </div>
    <div class="mb-3">
        <label>نقش:</label>
        <select name="role" class="form-select">
            <option value="student">دانشجو</option>
            <option value="admin">ادمین</option>
        </select>
    </div>
    <button type="submit" class="btn btn-primary">ثبت نام</button>
</form>
{% endblock %}
        """,
        "login.html": """
{% extends "layout.html" %}
{% block content %}
<h2>ورود</h2>
<form method="post">
    <div class="mb-3">
        <label>نام کاربری:</label>
        <input type="text" name="username" class="form-control" required>
    </div>
    <div class="mb-3">
        <label>رمز عبور:</label>
        <input type="password" name="password" class="form-control" required>
    </div>
    <button type="submit" class="btn btn-success">ورود</button>
</form>
{% endblock %}
        """,
        "dashboard.html": """
{% extends "layout.html" %}
{% block content %}
<h2>داشبورد کاربر</h2>
<p>سلام {{ session['full_name'] }}! به سامانه آزمون خوش آمدید.</p>
<hr>
<h3>آزمون‌های موجود</h3>
<div class="list-group">
    {% for exam in exams %}
    <a href="/exam/{{ exam._id }}" class="list-group-item list-group-item-action">
        {{ exam.title }} <small class="text-muted">({{ exam.description }})</small>
    </a>
    {% else %}
    <p>در حال حاضر آزمونی برای شرکت وجود ندارد.</p>
    {% endfor %}
</div>
<hr>
<h3>نتایج آزمون‌های شما</h3>
<ul class="list-group">
    {% for result in results %}
    <li class="list-group-item d-flex justify-content-between align-items-center">
        <span>آزمون: <strong>{{ result.exam_title }}</strong> | نمره: {{ result.score }} از {{ result.total }}</span>
        <span class="badge bg-secondary rounded-pill">{{ result.submitted_at.strftime('%Y-%m-%d %H:%M') }}</span>
    </li>
    {% else %}
    <li class="list-group-item">شما تا به حال در هیچ آزمونی شرکت نکرده‌اید.</li>
    {% endfor %}
</ul>
{% endblock %}
        """,
        "exam.html": """
{% extends "layout.html" %}
{% block content %}
<h2>{{ exam.title }}</h2>
<p>{{ exam.description }}</p>
<form method="post" action="/submit/{{ exam._id }}">
    {% for q in questions %}
    <div class="card my-3">
        <div class="card-header">سوال {{ loop.index }}</div>
        <div class="card-body">
            <p class="card-text">{{ q.text }}</p>
            {% for option in q.options %}
            <div class="form-check">
                <input class="form-check-input" type="radio" name="q_{{ q._id }}" id="q_{{ q._id }}_{{ loop.index0 }}" value="{{ loop.index0 }}" required>
                <label class="form-check-label" for="q_{{ q._id }}_{{ loop.index0 }}">{{ option }}</label>
            </div>
            {% endfor %}
        </div>
    </div>
    {% else %}
    <p>سوالی برای این آزمون وجود ندارد.</p>
    {% endfor %}
    <button type="submit" class="btn btn-primary mt-3">ثبت نهایی آزمون</button>
</form>
{% endblock %}
        """,
        "result.html": """
{% extends "layout.html" %}
{% block content %}
<div class="text-center">
    <h2>آزمون با موفقیت ثبت شد.</h2>
    <h4>نمره شما: {{ result.score }} از {{ result.total }}</h4>
    <a href="/dashboard" class="btn btn-info mt-3">بازگشت به داشبورد</a>
</div>
{% endblock %}
        """,
        "admin/dashboard.html": """
{% extends "layout.html" %}
{% block content %}
<h2>پنل مدیریت</h2>
<p>از اینجا می‌توانید آزمون‌ها، سوالات و کاربران را مدیریت کنید.</p>
<div class="d-grid gap-2">
    <a href="/admin/exams" class="btn btn-primary">مدیریت آزمون‌ها</a>
</div>
{% endblock %}
""",
        "admin/exam_management.html": """
{% extends "layout.html" %}
{% block content %}
<h2>مدیریت آزمون‌ها</h2>
<a href="/admin/exam/new" class="btn btn-success mb-3">ایجاد آزمون جدید</a>
<div class="table-responsive">
<table class="table table-striped">
    <thead>
        <tr>
            <th>عنوان آزمون</th>
            <th>توضیحات</th>
            <th>عملیات</th>
        </tr>
    </thead>
    <tbody>
        {% for exam in exams %}
        <tr>
            <td>{{ exam.title }}</td>
            <td>{{ exam.description }}</td>
            <td>
                <a href="/admin/exam/{{ exam._id }}/questions" class="btn btn-sm btn-info">سوالات</a>
                <a href="/admin/exam/{{ exam._id }}/edit" class="btn btn-sm btn-warning">ویرایش</a>
                <a href="/admin/exam/{{ exam._id }}/delete" class="btn btn-sm btn-danger" onclick="return confirm('آیا مطمئن هستید؟ با حذف آزمون، تمام سوالات و نتایج آن نیز حذف می‌شوند.')">حذف</a>
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>
</div>
{% endblock %}
""",
        "admin/exam_form.html": """
{% extends "layout.html" %}
{% block content %}
<h2>{{ 'ویرایش' if exam else 'ایجاد' }} آزمون</h2>
<form method="post">
    <div class="mb-3">
        <label>عنوان آزمون:</label>
        <input type="text" name="title" class="form-control" value="{{ exam.title if exam else '' }}" required>
    </div>
    <div class="mb-3">
        <label>توضیحات:</label>
        <textarea name="description" class="form-control">{{ exam.description if exam else '' }}</textarea>
    </div>
    <button type="submit" class="btn btn-primary">ذخیره</button>
</form>
{% endblock %}
""",
        "admin/question_management.html": """
{% extends "layout.html" %}
{% block content %}
<h2>مدیریت سوالات آزمون: {{ exam.title }}</h2>
<a href="/admin/exam/{{ exam._id }}/import" class="btn btn-success mb-3">افزودن گروهی سوال</a>
<hr>
{% for q in questions %}
<div class="card my-2">
    <div class="card-body">
        <div class="d-flex justify-content-between">
            <p><strong>سوال {{ loop.index }}:</strong> {{ q.text }}</p>
            <a href="/admin/question/{{ q._id }}/delete" class="btn-close" aria-label="Close" onclick="return confirm('آیا از حذف این سوال مطمئن هستید؟')"></a>
        </div>
        <ol type="1">
            {% for opt in q.options %}
            <li {% if loop.index0 == q.correct_index %}class="text-success fw-bold"{% endif %}>{{ opt }}</li>
            {% endfor %}
        </ol>
    </div>
</div>
{% else %}
<div class="alert alert-warning">هنوز سوالی برای این آزمون ثبت نشده است.</div>
{% endfor %}
{% endblock %}
""",
        "admin/import_form.html": """
{% extends "layout.html" %}
{% block content %}
<div style="direction: rtl; text-align: right; font-family: 'Vazirmatn', sans-serif;">
    <h2>افزودن گروهی سوال به آزمون: {{ exam.title }}</h2>
    <form method="post">
        <p>سوالات را با فرمت زیر وارد کنید (هر سوال در یک خط):</p>
        <div class="alert alert-info"><code>متن سوال * گزینه اول * گزینه دوم * گزینه سوم * گزینه چهارم * شماره گزینه درست (از 0 تا 3)</code></div>
        <textarea name="raw_questions" rows="10" class="form-control text-start" placeholder="مثال: پایتخت ایران کجاست؟ * اصفهان * شیراز * تهران * تبریز * 2"></textarea><br>
        <button type="submit" class="btn btn-primary">آپلود سوالات</button>
        <a href="/admin/exam/{{ exam._id }}/questions" class="btn btn-secondary">بازگشت</a>
    </form>
</div>
{% endblock %}
"""
    }
    # This simulates Jinja2's extends and block features in a simplified way
    base = templates['layout.html']
    if template_name != 'layout.html':
        page_content = templates[template_name]
        page_content = page_content.replace('{% extends "layout.html" %}', '')
        base = base.replace('{% block content %}{% endblock %}', page_content)

    return render_template_string(base, **context)

# --- مسیرهای اصلی و احراز هویت ---
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        role = request.form.get('role', 'student')

        if users_coll.find_one({'username': username}):
            flash("این نام کاربری قبلا استفاده شده است.", "danger")
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        users_coll.insert_one({
            'username': username,
            'password': hashed_password,
            'full_name': full_name,
            'role': role
        })
        flash("ثبت نام با موفقیت انجام شد. لطفا وارد شوید.", "success")
        return redirect(url_for('login'))
    return render("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = users_coll.find_one({'username': username})

        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session['role'] = user['role']
            flash("شما با موفقیت وارد شدید.", "success")
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        else:
            flash("نام کاربری یا رمز عبور اشتباه است.", "danger")
    return render("login.html")

@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash("شما با موفقیت خارج شدید.", "info")
    return redirect(url_for('login'))

# --- پنل کاربری ---
@app.route('/dashboard')
@login_required
def dashboard():
    all_exams = list(exams_coll.find().sort('title', 1))
    
    user_results = list(results_coll.find({'user_id': ObjectId(session['user_id'])}).sort('submitted_at', -1))
    
    for result in user_results:
        exam = exams_coll.find_one({'_id': result['exam_id']})
        result['exam_title'] = exam['title'] if exam else "نامشخص"

    return render("dashboard.html", exams=all_exams, results=user_results)

@app.route('/exam/<exam_id>')
@login_required
def take_exam(exam_id):
    try:
        exam = exams_coll.find_one({'_id': ObjectId(exam_id)})
    except:
        flash("شناسه آزمون نامعتبر است.", "danger")
        return redirect(url_for('dashboard'))

    if not exam:
        flash("آزمون مورد نظر یافت نشد.", "danger")
        return redirect(url_for('dashboard'))
    
    existing_result = results_coll.find_one({'user_id': ObjectId(session['user_id']), 'exam_id': ObjectId(exam_id)})
    if existing_result:
        flash("شما قبلا در این آزمون شرکت کرده‌اید.", "warning")
        return redirect(url_for('dashboard'))

    questions = list(questions_coll.find({'exam_id': ObjectId(exam_id)}))
    return render("exam.html", exam=exam, questions=questions)

@app.route('/submit/<exam_id>', methods=['POST'])
@login_required
def submit_exam(exam_id):
    exam = exams_coll.find_one({'_id': ObjectId(exam_id)})
    if not exam:
        return redirect(url_for('dashboard'))

    score = 0
    all_questions = list(questions_coll.find({'exam_id': ObjectId(exam_id)}))
    
    for q in all_questions:
        user_answer = request.form.get(f"q_{q['_id']}")
        if user_answer is not None and int(user_answer) == q.get('correct_index'):
            score += 1
            
    result_doc = {
        "user_id": ObjectId(session['user_id']),
        "exam_id": ObjectId(exam_id),
        "score": score,
        "total": len(all_questions),
        "submitted_at": datetime.utcnow()
    }
    results_coll.insert_one(result_doc)
    return render("result.html", result=result_doc)

# --- پنل ادمین ---
@app.route('/admin')
@admin_required
def admin_dashboard():
    return render("admin/dashboard.html")

@app.route('/admin/exams')
@admin_required
def admin_exams():
    all_exams = list(exams_coll.find().sort('title', 1))
    return render("admin/exam_management.html", exams=all_exams)

@app.route('/admin/exam/new', methods=['GET', 'POST'])
@admin_required
def admin_new_exam():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        if title:
            exams_coll.insert_one({'title': title, 'description': description, 'created_at': datetime.utcnow()})
            flash("آزمون با موفقیت ایجاد شد.", "success")
            return redirect(url_for('admin_exams'))
        else:
            flash("عنوان آزمون نمی‌تواند خالی باشد.", "danger")
    return render("admin/exam_form.html", exam=None)

@app.route('/admin/exam/<exam_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_exam(exam_id):
    exam = exams_coll.find_one({'_id': ObjectId(exam_id)})
    if not exam:
        return redirect(url_for('admin_exams'))

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        if title:
            exams_coll.update_one({'_id': ObjectId(exam_id)}, {'$set': {'title': title, 'description': description}})
            flash("آزمون با موفقیت ویرایش شد.", "success")
            return redirect(url_for('admin_exams'))
        else:
            flash("عنوان آزمون نمی‌تواند خالی باشد.", "danger")
    
    return render("admin/exam_form.html", exam=exam)
    
@app.route('/admin/exam/<exam_id>/delete')
@admin_required
def admin_delete_exam(exam_id):
    exams_coll.delete_one({'_id': ObjectId(exam_id)})
    questions_coll.delete_many({'exam_id': ObjectId(exam_id)})
    results_coll.delete_many({'exam_id': ObjectId(exam_id)})
    flash("آزمون و تمام داده‌های مرتبط با آن حذف شد.", "success")
    return redirect(url_for('admin_exams'))

@app.route('/admin/exam/<exam_id>/questions')
@admin_required
def admin_exam_questions(exam_id):
    exam = exams_coll.find_one({'_id': ObjectId(exam_id)})
    if not exam:
        return redirect(url_for('admin_exams'))
    
    questions = list(questions_coll.find({'exam_id': ObjectId(exam_id)}))
    return render("admin/question_management.html", exam=exam, questions=questions)
    
@app.route('/admin/question/<question_id>/delete')
@admin_required
def admin_delete_question(question_id):
    question = questions_coll.find_one_and_delete({'_id': ObjectId(question_id)})
    if question:
        flash("سوال با موفقیت حذف شد.", "success")
        return redirect(url_for('admin_exam_questions', exam_id=question['exam_id']))
    return redirect(url_for('admin_exams'))


@app.route('/admin/exam/<exam_id>/import', methods=['GET', 'POST'])
@admin_required
def admin_import_questions(exam_id):
    exam = exams_coll.find_one({'_id': ObjectId(exam_id)})
    if not exam:
        return redirect(url_for('admin_exams'))

    if request.method == 'POST':
        raw_text = request.form.get('raw_questions')
        lines = raw_text.strip().split('\n')
        added_count = 0
        for i, line in enumerate(lines):
            try:
                if '*' in line:
                    parts = [p.strip() for p in line.split('*')]
                    if len(parts) == 6:
                        q_text, opt1, opt2, opt3, opt4, correct_idx_str = parts
                        options = [opt1, opt2, opt3, opt4]
                        correct_idx = int(correct_idx_str)
                        
                        if not (0 <= correct_idx <= 3):
                            raise ValueError("شماره گزینه صحیح باید بین 0 تا 3 باشد.")

                        questions_coll.insert_one({
                            "exam_id": ObjectId(exam_id),
                            "text": q_text,
                            "options": options,
                            "correct_index": correct_idx
                        })
                        added_count += 1
                    else:
                        raise ValueError("فرمت خط صحیح نیست (باید 6 بخش جدا شده با * داشته باشد).")
            except Exception as e:
                flash(f"خطا در پردازش خط شماره {i+1}: {e}", "danger")

        if added_count > 0:
            flash(f"تعداد {added_count} سوال با موفقیت اضافه شد!", "success")
        return redirect(url_for('admin_exam_questions', exam_id=exam_id))

    return render("admin/import_form.html", exam=exam)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # در حالت توسعه debug=True و در حالت نهایی آن را False قرار دهید
    app.run(host='0.0.0.0', port=port, debug=True)
