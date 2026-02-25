from datetime import datetime
from flask import Blueprint, current_app, render_template
from flask_login import current_user, login_required

page_bp = Blueprint("pages", __name__)

@page_bp.get("/")
def home():
    return render_template("index.html")

# gets all entries in the db for the given month/year for the current user
# and gives data to template
@page_bp.get("/calendarview/<int:year>/<int:month>")
#@login_required
def calendar_view(year, month):
    db = current_app.mongo_db
    user_id = 1 # placeholder for when we have auth, replace with current_user.id
    start = datetime(year, month, 1)
    end = datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)

    query = {
        'user_id': user_id,
        'date': {
            '$gte': start,
            '$lt': end
        }
    }
    entries = db.mood_entries.find(query).sort('date', 1)

    return render_template("calendarview.html", entries = entries, year=year, month=month)