from datetime import datetime
from flask import Blueprint, current_app, redirect, request, url_for
from flask_login import current_user, login_required

entry_bp = Blueprint("entry", __name__)

@entry_bp.post("/add")
# @login_required
def add_entry():
    db = current_app.mongo_db
    user_id = 1 # placeholder for when we make auth, replace with current_user.id
    date = datetime.now()
    mood_value = int(request.form["mood_value"])
    note = request.form["note"]

    doc = {
        "user_id": user_id,
        "date": date,
        "mood_value": mood_value,
        "note": note
    }
    db.mood_entries.insert_one(doc)
    
    return redirect(url_for("pages.calendarview", year=date.year, month=date.month))
    