#!/usr/bin/env python3

"""
Azure Mood Flask Application
"""

import os
import calendar
from datetime import datetime, date, timezone
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
import pymongo
from dotenv import load_dotenv
from bson.objectid import ObjectId
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Load config from environment variables
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-change-me')
    app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
    app.config['MONGO_DBNAME'] = os.getenv('MONGO_DBNAME', 'mood_journal')
    
    # Connect to MongoDB
    cxn = pymongo.MongoClient(app.config['MONGO_URI'])
    db = cxn[app.config['MONGO_DBNAME']]
    
    try:
        cxn.admin.command('ping')
        print(' *', 'Connected to MongoDB!')
    except Exception as e:
        print(' * MongoDB connection error:', e)

    login_manager = LoginManager()
    login_manager.login_view = 'login' 
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        user_data = db.users.find_one({"_id": ObjectId(user_id)})
        return User(user_data) if user_data else None
    
    
    def build_calendar_matrix(year, month):
        """Build a calendar matrix"""
        cal = calendar.monthcalendar(year, month)
        today = date.today()
        
        user_id = current_user.id if current_user.is_authenticated else 'test_user'

        start = datetime(year, month, 1, tzinfo=timezone.utc)
        end = datetime(year, month, calendar.monthrange(year, month)[1], 23, 59, 59, tzinfo=timezone.utc)

        try: 
            raw_entries = list(db.mood_entries.find({'user_id': user_id, 'date': {'$gte': start, '$lte': end}})) 
        except Exception as e:
            app.logger.exception("Failed to get user entries for calendar view. Error:", e)
            raw_entries = []

        entries_dict = {}
        for entry in raw_entries:
            date_key = entry["date"].strftime("%Y-%m-%d")
            entries_dict[date_key] = {
                "mood": entry["mood_value"], 
                "entry_id": str(entry["_id"])
            }

        matrix = []
        for week in cal:
            week_data = []
            for day in week:
                if day == 0:
                    week_data.append({'day': None})
                else:
                    current_date = date(year, month, day)
                    date_str = f"{year}-{month:02d}-{day:02d}"
                    cell = {
                        'day': day,
                        'date_str': date_str,
                        'is_today': (current_date == today),
                        'has_link': (current_date <= today),
                        'mood': None,
                        'entry_id': None
                    }
                    if date_str in entries_dict:
                        cell['mood'] = entries_dict[date_str]['mood']
                        cell['entry_id'] = str(entries_dict[date_str]['entry_id'])
                    week_data.append(cell)
            matrix.append(week_data)
        return matrix
    
    # ASSETS ROUTE (for local fonts)
    
    @app.route('/assets/<path:filename>')
    def serve_assets(filename):
        """Serve files from the assets folder"""
        return send_from_directory('assets', filename)
    
    # PAGE ROUTES
    
    @app.route('/')
    @login_required
    def home():
        year = int(request.args.get('year', datetime.now().year))
        month = int(request.args.get('month', datetime.now().month))
        
        prev_month, prev_year = (12, year - 1) if month == 1 else (month - 1, year)
        next_month, next_year = (1, year + 1) if month == 12 else (month + 1, year)
        
        calendar_matrix = build_calendar_matrix(year, month)
        return render_template('index.html', calendar_matrix=calendar_matrix, 
                             month_name=calendar.month_name[month], year=year,
                             prev_month=prev_month, prev_year=prev_year,
                             next_month=next_month, next_year=next_year, active_page='home')
    
    @app.route('/stats')
    @login_required
    def stats():
        year, month = datetime.now().year, datetime.now().month
        user_id = current_user.id
        start = datetime(year, month, 1, tzinfo=timezone.utc)
        end = datetime(year, month, calendar.monthrange(year, month)[1], 23, 59, 59, tzinfo=timezone.utc)

        try: 
            entries = list(db.mood_entries.find({"user_id": user_id, "date": {"$gte": start, "$lte": end}})) 
            total_entries = db.mood_entries.count_documents({"user_id": user_id})
            entries_this_month = len(entries)
            mood_counts = {1:0, 2:0, 3:0, 4:0, 5:0}
            total = 0
            for entry in entries:
                total += entry["mood_value"]
                mood_counts[entry["mood_value"]] += 1

            average_mood = total / entries_this_month if entries_this_month > 0 else None
            
            return render_template('dashboard.html', total_entries=total_entries,
                                entries_this_month=entries_this_month, average_mood=average_mood,
                                current_streak=5, mood_counts=mood_counts, active_page='stats')
        except Exception as e:
            app.logger.exception("Failed to retrieve stats.")
            return redirect(url_for('home'))

    @app.route('/settings')
    @login_required
    def settings():
        return render_template('settings.html', username=current_user.username, active_page='settings')
    
    # ENTRY ROUTES

    
    @app.route('/entries/add')
    @login_required
    def add_entry():
        date_str = request.args.get('date')
        selected_date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.now()
        
        # Check if an entry already exists for this date
        start_of_day = selected_date.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
        end_of_day = selected_date.replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=timezone.utc)
        
        existing_entry = db.mood_entries.find_one({
            "user_id": current_user.id,
            "date": {"$gte": start_of_day, "$lte": end_of_day}
        })
        
        if existing_entry:
            return redirect(url_for('edit_entry', entry_id=str(existing_entry['_id'])))
        
        return render_template('entry_form.html', entry=None, selected_date=selected_date, active_page='add')
    
    @app.route('/entries/create', methods=['POST'])
    @login_required
    def create_entry():
        try:
            mood_value = request.form.get('mood_value', type=int)
            entry_text = request.form.get('entry_text')
            date_str = request.form.get('entry_date')

            entry_date = datetime.strptime(date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc) if date_str else datetime.now(timezone.utc)

            db.mood_entries.insert_one({
                "user_id": current_user.id,
                "mood_value": mood_value,
                "entry_text": entry_text,
                "date": entry_date,
                "created_at": datetime.now(timezone.utc)
            })
        except Exception as e:
            app.logger.exception("Failed to create mood entry.")

        return redirect(url_for('home'))
    
    @app.route('/entries/<entry_id>')
    @login_required
    def view_entry(entry_id):
        entry = db.mood_entries.find_one({"_id": ObjectId(entry_id), "user_id": current_user.id})
        if not entry:
            flash('Entry not found', 'error')
            return redirect(url_for('home'))
        return render_template('entry_detail.html', entry=entry)
    
    @app.route('/entries/<entry_id>/edit')
    @login_required
    def edit_entry(entry_id):
        entry = db.mood_entries.find_one({"_id": ObjectId(entry_id), "user_id": current_user.id})
        if not entry:
            flash('Entry not found', 'error')
            return redirect(url_for('home'))
        return render_template('entry_form.html', entry=entry)
    
    @app.route('/entries/<entry_id>/edit', methods=['POST'])
    @login_required
    def update_entry(entry_id):
        try:
            mood_value = request.form.get('mood_value', type=int)
            entry_text = request.form.get('entry_text')
            
            db.mood_entries.update_one(
                {"_id": ObjectId(entry_id), "user_id": current_user.id},
                {"$set": {
                    "mood_value": mood_value,
                    "entry_text": entry_text,
                    "updated_at": datetime.now(timezone.utc)
                }}
            )
            flash('Entry updated successfully!', 'success')
        except Exception as e:
            app.logger.exception("Failed to update mood entry.")
            flash('Failed to update entry', 'error')
        return redirect(url_for('view_entry', entry_id=entry_id))
    
    @app.route('/entries/<entry_id>/delete', methods=['POST'])
    @login_required
    def delete_entry(entry_id):
        db.mood_entries.delete_one({"_id": ObjectId(entry_id), "user_id": current_user.id})
        flash('Entry deleted successfully!', 'success')
        return redirect(url_for('home'))
    
    @app.route('/entries/search')
    @login_required
    def search_entries():
        query = request.args.get('q', '')
        mood_filter = request.args.get('mood', type=int)
        filter_query = {"user_id": current_user.id}

        if mood_filter: filter_query["mood_value"] = mood_filter
        if query: filter_query["entry_text"] = {"$regex": query, "$options": "i"}
                
        results = list(db.mood_entries.find(filter_query).sort("date", -1))
        return render_template('search.html', results=results, query=query, 
                             mood_filter=mood_filter, active_page='search')
    
    @app.route('/entries/export')
    @login_required
    def export_entries():
        flash('Export functionality coming soon!', 'success')
        return redirect(url_for('settings'))
    
    # AUTH ROUTES

    
    @app.route('/auth/login')
    def login():
        return render_template('login.html')
    
    @app.route('/auth/login', methods=['POST'])
    def login_post():
        # get username and password
        username = request.form.get('username')
        password = request.form.get('password')
        
        user_data = db.users.find_one({"username": username})
        
        # check hash
        if user_data and check_password_hash(user_data['password'], password):
            user_obj = User(user_data)
            login_user(user_obj)
            return redirect(url_for('home'))
        
        flash('Invalid username or password', 'error')
        return redirect(url_for('login'))
    
    @app.route('/auth/register')
    def register():
        return render_template('register.html')
    
    @app.route('/auth/register', methods=['POST'])
    def register_post():
        # get username and password
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))

        if db.users.find_one({"username": username}):
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
        
        # hash password
        hashed_pw = generate_password_hash(password)
        db.users.insert_one({"username": username, "password": hashed_pw})
        return redirect(url_for('login'))
    
    @app.route('/auth/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)