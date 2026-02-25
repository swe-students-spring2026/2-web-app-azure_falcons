#!/usr/bin/env python3

"""
Mood Journal Flask Application
"""

import os
import calendar
from datetime import datetime, date
from flask import Flask, render_template, request, redirect, url_for, flash, session
import pymongo
from dotenv import load_dotenv

load_dotenv()

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
    
    # =============================================
    # MOCK DATA FOR DEVELOPMENT
    # =============================================
    MOCK_ENTRIES = {
        '2026-02-15': {'mood': 5, 'entry_id': 'mock1'},
        '2026-02-18': {'mood': 3, 'entry_id': 'mock2'},
        '2026-02-20': {'mood': 4, 'entry_id': 'mock3'},
        '2026-02-23': {'mood': 2, 'entry_id': 'mock4'},
        '2026-02-25': {'mood': 5, 'entry_id': 'mock5'},
    }
    
    MOCK_ENTRIES_DB = {
        'mock1': {
            '_id': 'mock1',
            'date': datetime(2026, 2, 15, 10, 30),
            'mood_value': 5,
            'entry_text': 'Had an amazing day! Everything went perfectly and I felt really productive.'
        },
        'mock2': {
            '_id': 'mock2',
            'date': datetime(2026, 2, 18, 14, 45),
            'mood_value': 3,
            'entry_text': 'Just a regular day, nothing special. Feeling neutral about everything.'
        },
        'mock3': {
            '_id': 'mock3',
            'date': datetime(2026, 2, 20, 9, 15),
            'mood_value': 4,
            'entry_text': 'Good progress on my projects today. Feeling optimistic about the week ahead.'
        },
        'mock4': {
            '_id': 'mock4',
            'date': datetime(2026, 2, 23, 16, 20),
            'mood_value': 2,
            'entry_text': 'Rough day. Had some setbacks and feeling a bit down. Need to rest.'
        },
        'mock5': {
            '_id': 'mock5',
            'date': datetime(2026, 2, 25, 11, 0),
            'mood_value': 5,
            'entry_text': 'Fantastic day! Celebrated some wins and feeling really grateful.'
        },
    }
    
    def build_calendar_matrix(year, month):
        """Build a calendar matrix with mock data"""
        cal = calendar.monthcalendar(year, month)
        today = date.today()
        
        matrix = []
        for week in cal:
            week_data = []
            for day in week:
                if day == 0:
                    week_data.append({'day': None})
                else:
                    date_str = f"{year}-{month:02d}-{day:02d}"
                    cell = {
                        'day': day,
                        'date_str': date_str,
                        'is_today': (year == today.year and month == today.month and day == today.day),
                        'mood': None,
                        'entry_id': None
                    }
                    
                    if date_str in MOCK_ENTRIES:
                        cell['mood'] = MOCK_ENTRIES[date_str]['mood']
                        cell['entry_id'] = MOCK_ENTRIES[date_str]['entry_id']
                    
                    week_data.append(cell)
            matrix.append(week_data)
        
        return matrix
    
    # =============================================
    # PAGE ROUTES
    # =============================================
    
    @app.route('/')
    def home():
        """Home page with calendar view"""
        year = int(request.args.get('year', datetime.now().year))
        month = int(request.args.get('month', datetime.now().month))
        
        if month == 1:
            prev_month, prev_year = 12, year - 1
        else:
            prev_month, prev_year = month - 1, year
        
        if month == 12:
            next_month, next_year = 1, year + 1
        else:
            next_month, next_year = month + 1, year
        
        calendar_matrix = build_calendar_matrix(year, month)
        month_name = calendar.month_name[month]
        
        return render_template('index.html',
                             calendar_matrix=calendar_matrix,
                             month_name=month_name,
                             year=year,
                             prev_month=prev_month,
                             prev_year=prev_year,
                             next_month=next_month,
                             next_year=next_year,
                             active_page='home')
    
    @app.route('/stats')
    def stats():
        """Analytics and stats page"""
        return render_template('dashboard.html',
                             total_entries=15,
                             entries_this_month=7,
                             average_mood=3.8,
                             current_streak=5,
                             mood_counts={1: 2, 2: 3, 3: 4, 4: 3, 5: 3},
                             active_page='stats')
    
    @app.route('/settings')
    def settings():
        """Settings page"""
        username = session.get('user', 'Guest')
        return render_template('settings.html', username=username, active_page='settings')
    
    # =============================================
    # ENTRY ROUTES
    # =============================================
    
    @app.route('/entries/add')
    def add_entry():
        """Show form to add a new entry"""
        selected_date = None
        if request.args.get('date'):
            try:
                selected_date = datetime.strptime(request.args.get('date'), '%Y-%m-%d')
            except:
                selected_date = datetime.now()
        else:
            selected_date = datetime.now()
        
        return render_template('entry_form.html', 
                             entry=None, 
                             selected_date=selected_date,
                             active_page='add')
    
    @app.route('/entries/create', methods=['POST'])
    def create_entry():
        """Create a new entry"""
        flash('Entry created successfully!', 'success')
        return redirect(url_for('home'))
    
    @app.route('/entries/<entry_id>')
    def view_entry(entry_id):
        """View a single entry"""
        entry = MOCK_ENTRIES_DB.get(entry_id)
        if not entry:
            flash('Entry not found', 'error')
            return redirect(url_for('home'))
        
        return render_template('entry_detail.html', entry=entry)
    
    @app.route('/entries/<entry_id>/edit')
    def edit_entry(entry_id):
        """Show form to edit an entry"""
        entry = MOCK_ENTRIES_DB.get(entry_id)
        if not entry:
            flash('Entry not found', 'error')
            return redirect(url_for('home'))
        
        return render_template('entry_form.html', entry=entry)
    
    @app.route('/entries/<entry_id>/edit', methods=['POST'])
    def update_entry(entry_id):
        """Update an entry"""
        flash('Entry updated successfully!', 'success')
        return redirect(url_for('view_entry', entry_id=entry_id))
    
    @app.route('/entries/<entry_id>/delete', methods=['POST'])
    def delete_entry(entry_id):
        """Delete an entry"""
        flash('Entry deleted successfully!', 'success')
        return redirect(url_for('home'))
    
    @app.route('/entries/search')
    def search_entries():
        """Search entries"""
        query = request.args.get('q', '')
        mood_filter = request.args.get('mood', type=int)
        
        results = []
        
        if query or mood_filter:
            for entry_id, entry in MOCK_ENTRIES_DB.items():
                if mood_filter and entry['mood_value'] != mood_filter:
                    continue
                
                if query and query.lower() not in entry['entry_text'].lower():
                    continue
                
                results.append(entry)
            
            results.sort(key=lambda x: x['date'], reverse=True)
        
        return render_template('search.html', 
                             results=results,
                             query=query,
                             mood_filter=mood_filter,
                             active_page='search')
    
    @app.route('/entries/export')
    def export_entries():
        """Export entries"""
        flash('Export functionality coming soon!', 'success')
        return redirect(url_for('settings'))
    
    # =============================================
    # AUTH ROUTES
    # =============================================
    
    @app.route('/auth/login')
    def login():
        """Show login form"""
        return render_template('login.html')
    
    @app.route('/auth/login', methods=['POST'])
    def login_post():
        """Handle login"""
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username and password:
            session['user'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Please enter username and password', 'error')
            return redirect(url_for('login'))
    
    @app.route('/auth/register')
    def register():
        """Show registration form"""
        return render_template('register.html')
    
    @app.route('/auth/register', methods=['POST'])
    def register_post():
        """Handle registration"""
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not password:
            flash('Please fill out all fields', 'error')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    @app.route('/auth/logout')
    def logout():
        """Handle logout"""
        session.pop('user', None)
        flash('Logged out successfully', 'success')
        return redirect(url_for('login'))
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
