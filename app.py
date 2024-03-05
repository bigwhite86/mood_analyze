from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask import send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource,Api
from flask_cors import CORS
from datetime import datetime
import os
import csv
from colorpredict import ColorPredictor  # 導入顏色預測類

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
color_predictor = ColorPredictor()  
db = SQLAlchemy(app)

# 定義 User 模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
class AnalyzeResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    csv_filename = db.Column(db.String(255), nullable=False)
    red = db.Column(db.Float, nullable=True)
    yellow = db.Column(db.Float, nullable=True)
    blue = db.Column(db.Float, nullable=True)
    green = db.Column(db.Float, nullable=True)
  
uploads_folder = 'uploads'
if not os.path.exists(uploads_folder):
    os.makedirs(uploads_folder)

def save_text_file(username, content):
    filename = f"{username}_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
    filepath = os.path.join(uploads_folder, filename)
    with open(filepath, 'w') as file:
        file.write(content)

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    user = User.query.filter_by(username=username, password=password).first()

    if user:
        session['user_id'] = user.id  # 在 session 中保存登入狀態
        return redirect(url_for('member'))
    else:
        return render_template('index.html', login_failed=True)  # 傳遞 login_failed 參數給模板
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if not existing_user:
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            session['user_id'] = new_user.id
            return redirect(url_for('index'))
        else:
            return render_template('register.html', username_exists=True)
    return render_template('register.html')

@app.route('/member', methods=['GET', 'POST'])
def member():
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        username = user.username
        calendar_dates = []
        for file in os.listdir(uploads_folder):
            if file.startswith(username):
                date_str = file.split('_')[1].split('.')[0]
                date = datetime.strptime(date_str, '%Y%m%d%H%M%S')
                calendar_dates.append(date.strftime('%Y-%m-%d'))
        return render_template('member.html', username=username, calendar_dates=calendar_dates)
    else:
        return redirect(url_for('index'))
@app.route('/analyze_csv', methods=['POST'])
def analyze_csv():
    csv_filename = request.form.get('csv_filename')
    file_path = os.path.join(uploads_folder, csv_filename)

    if os.path.exists(file_path):
        texts = []
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)
            for row in reader:
                if row and len(row) > 1:
                    texts.append(row[1])

        color_predictor = ColorPredictor()
        color_probabilities_list = color_predictor.predict_colors(texts)

        # 獲取目前登入的會員ID
        user_id = session.get('user_id')

        # 將分析結果存入資料庫
        if user_id:
            for color_probabilities in color_probabilities_list:
                analysis = AnalyzeResult(
                    user_id=user_id,
                    csv_filename=csv_filename,
                    red=color_probabilities['紅色機率'],
                    yellow=color_probabilities['黃色機率'],
                    blue=color_probabilities['藍色機率'],
                    green=color_probabilities['綠色機率']
                )
                db.session.add(analysis)
            db.session.commit()

            return render_template('predict.html', color_probabilities_list=color_probabilities_list)
        else:
            return redirect(url_for('index'))
    else:
        return redirect(url_for('member', error='File not found'))



@app.route('/history')
def history():
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        username = user.username
        history_files = []
        for file in os.listdir(uploads_folder):
            if file.startswith(username):
                history_files.append(file)
        return render_template('history.html', username=username, history_files=history_files)
    else:
        return redirect(url_for('index'))

@app.route('/save_text', methods=['POST'])
def save_text():
    text_content = request.form['textContent']
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        username = user.username
        current_datetime = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"{username}_{current_datetime}.csv"
        filepath = os.path.join(uploads_folder, filename)
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Timestamp', 'Text Content']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow({'Timestamp': current_datetime, 'Text Content': text_content})
        return jsonify({'message': 'Text saved successfully!', 'filename': filename})
    else:
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(uploads_folder, filename, as_attachment=True)

@app.route('/edit_file/<filename>', methods=['GET', 'POST'])
def edit_file(filename):
    filepath = os.path.join(uploads_folder, filename)
    if request.method == 'GET':
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                file_content = file.read()
            return render_template('edit_file.html', filename=filename, file_content=file_content)
        except Exception as e:
            return f"Error reading file: {e}"
    elif request.method == 'POST':
        modified_content = request.form['modified_content']
        try:
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(modified_content)
            return redirect(url_for('history'))
        except Exception as e:
            return f"Error writing file: {e}"

@app.route('/detail')
def detail():
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        username = user.username
        user_detail = {'username': username}
        return render_template('detail.html', user_detail=user_detail)
    else:
        return redirect(url_for('index'))

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logout successful'})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5050)