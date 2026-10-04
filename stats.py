"""All OneGood analytics. Pure functions: a list of dates in, insights out."""
from calendar import monthrange, month_name, day_name
from collections import Counter
from datetime import date, timedelta


def streaks(dates, today=None):
    today = today or date.today()
    days = sorted(set(dates))
    longest = run = 0
    prev = None
    for d in days:
        run = run + 1 if prev and d - prev == timedelta(days=1) else 1
        longest, prev = max(longest, run), d
    have = set(days)
    d = today if today in have else today - timedelta(days=1)  # today may still be open
    current = 0
    while d in have:
        current, d = current + 1, d - timedelta(days=1)
    return current, longest


def monthly(dates, year):
    counts = Counter(d.month for d in dates if d.year == year)
    return [{"name": month_name[m][:3], "count": counts[m],
             "days": monthrange(year, m)[1],
             "pct": round(100 * counts[m] / monthrange(year, m)[1])} for m in range(1, 13)]


def badges(dates):
    days = sorted(set(dates))
    _, best = streaks(days)
    per_month = Counter((d.year, d.month) for d in days)
    perfect = any(c == monthrange(y, m)[1] for (y, m), c in per_month.items())
    comeback = any((b - a).days > 7 for a, b in zip(days, days[1:]))
    return [
        {"name": "First Step", "hint": "Log your first good thing", "got": len(days) >= 1},
        {"name": "Week Strong", "hint": "7-day streak", "got": best >= 7},
        {"name": "Fortnight", "hint": "14-day streak", "got": best >= 14},
        {"name": "Habit Formed", "hint": "30-day streak", "got": best >= 30},
        {"name": "Perfect Month", "hint": "Log every day of a month", "got": perfect},
        {"name": "Comeback", "hint": "Return after a week away", "got": comeback},
        {"name": "Century", "hint": "100 good things", "got": len(days) >= 100},
    ]


def yearly(dates, year):
    ys = sorted(d for d in dates if d.year == year)
    if not ys:
        return None
    months = monthly(ys, year)
    best = max(months, key=lambda m: m["count"])
    weekday = Counter(d.weekday() for d in ys).most_common(1)[0][0]
    return {"total": len(ys), "active_months": sum(1 for m in months if m["count"]),
            "best_month": best["name"], "best_count": best["count"],
            "longest": streaks(ys, today=ys[-1])[1], "weekday": day_name[weekday],
            "first": ys[0], "last": ys[-1]}


if __name__ == "__main__":
    print("-" * 45)
    print(" OneGood Stats & Analytics Test")
    print("-" * 45)
    sample_dates = [
        date.today() - timedelta(days=d) for d in (0, 1, 2, 3, 5, 6, 7)
    ]
    cur, lon = streaks(sample_dates)
    print(f"Sample entries count : {len(sample_dates)}")
    print(f"Current streak       : {cur} day(s)")
    print(f"Longest streak       : {lon} day(s)")
    unlocked = [b["name"] for b in badges(sample_dates) if b["got"]]
    print(f"Badges earned        : {', '.join(unlocked) if unlocked else 'None'}")
    y_summary = yearly(sample_dates, date.today().year)
    if y_summary:
        print(f"Summary for {date.today().year}     : {y_summary['total']} items, best month: {y_summary['best_month']}")
    print("-" * 45)

