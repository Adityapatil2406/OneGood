import os
from datetime import date, datetime, timedelta

import mysql.connector
from flask import Flask, redirect, render_template, request, url_for

from jinja2 import ChoiceLoader, FileSystemLoader

import stats

# Look for templates in either templates/ or current directory
base_dir = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
app.jinja_loader = ChoiceLoader([
    FileSystemLoader(os.path.join(base_dir, "templates")),
    FileSystemLoader(base_dir),
])


def init_db():
    """Ensure database and tables are created before queries run."""
    try:
        con = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
        )
        cur = con.cursor()
        db_name = os.getenv("DB_NAME", "onegood")
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4;")
        cur.execute(f"USE {db_name};")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS entries (
          id         INT AUTO_INCREMENT PRIMARY KEY,
          entry_date DATE NOT NULL UNIQUE,
          note       VARCHAR(280) NOT NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        con.commit()
        con.close()
    except Exception as e:
        print(f"[Warning] DB initialization check: {e}")


def db():
    db_name = os.getenv("DB_NAME", "onegood")
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"), user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""), database=db_name)
    except mysql.connector.Error as err:
        if err.errno == 1049:  # Unknown database error
            init_db()
            return mysql.connector.connect(
                host=os.getenv("DB_HOST", "localhost"), user=os.getenv("DB_USER", "root"),
                password=os.getenv("DB_PASSWORD", ""), database=db_name)
        raise


@app.route("/")
def index():
    today = date.today()
    year = request.args.get("year", today.year, type=int)
    con = db()
    cur = con.cursor()
    cur.execute("SELECT entry_date, note, created_at FROM entries ORDER BY entry_date")
    rows = cur.fetchall()
    con.close()

    notes = {r[0]: r[1] for r in rows}
    entry_times = {r[0]: r[2] for r in rows}
    dates = list(notes)
    current, longest = stats.streaks(dates, today)

    start = date(year, 1, 1)
    ndays = (date(year + 1, 1, 1) - start).days
    grid = [{
        "d": d,
        "note": notes.get(d),
        "time": entry_times.get(d).strftime("%I:%M %p") if entry_times.get(d) else None,
        "future": d > today
    } for d in (start + timedelta(days=i) for i in range(ndays))]

    today_time = entry_times.get(today).strftime("%I:%M %p") if entry_times.get(today) else None

    return render_template(
        "index.html", year=year, today=today, today_note=notes.get(today),
        today_time=today_time,
        current=current, longest=longest, total=len(dates),
        grid=grid, offset=start.weekday(), months=stats.monthly(dates, year),
        badges=stats.badges(dates), summary=stats.yearly(dates, year),
        recent=sorted(rows, key=lambda r: (r[0], r[2] or datetime.min), reverse=True)[:7],
        years=sorted({d.year for d in dates} | {today.year}, reverse=True))


@app.post("/add")
def add():
    note = request.form.get("note", "").strip()[:280]
    entry_date_str = request.form.get("entry_date", "").strip()
    target_date = date.today()
    if entry_date_str:
        try:
            parsed = date.fromisoformat(entry_date_str)
            if parsed <= date.today():
                target_date = parsed
        except ValueError:
            pass

    if note:
        entry_timestamp = datetime.combine(target_date, datetime.now().time())
        con = db()
        cur = con.cursor()
        cur.execute(
            "INSERT INTO entries (entry_date, note, created_at) VALUES (%s, %s, %s) "
            "ON DUPLICATE KEY UPDATE note = VALUES(note), created_at = VALUES(created_at)",
            (target_date, note, entry_timestamp),
        )
        con.commit()
        con.close()
    return redirect(url_for("index", year=target_date.year, saved=1))


@app.post("/delete")
def delete():
    entry_date_str = request.form.get("entry_date", "").strip()
    target_year = date.today().year
    if entry_date_str:
        try:
            target_date = date.fromisoformat(entry_date_str)
            target_year = target_date.year
            con = db()
            cur = con.cursor()
            cur.execute("DELETE FROM entries WHERE entry_date = %s", (target_date,))
            con.commit()
            con.close()
        except ValueError:
            pass
    return redirect(url_for("index", year=target_year))


@app.get("/random")
def random_entry():
    con = db()
    cur = con.cursor()
    cur.execute("SELECT entry_date, note, created_at FROM entries ORDER BY RAND() LIMIT 1")
    row = cur.fetchone()
    con.close()
    if row:
        time_str = f" at {row[2].strftime('%I:%M %p')}" if row[2] else ""
        return {"found": True, "date": f"{row[0].strftime('%d %b %Y')}{time_str}", "note": row[1]}
    return {"found": False}




if __name__ == "__main__":
    init_db()
    print("Serving OneGood at http://127.0.0.1:5000 (Press CTRL+C to quit)")
    app.run(debug=True)
