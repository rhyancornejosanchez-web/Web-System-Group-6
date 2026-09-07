from datetime import date
import hashlib

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def check_password(pw, hashed):
    return hash_password(pw) == hashed

def get_rent_status(due_date_str, is_paid):
    if is_paid:
        return 'paid'
    due = date.fromisoformat(due_date_str)
    today = date.today()
    diff = (due - today).days
    if diff < 0:
        return 'overdue'
    elif diff <= 5:
        return 'due_soon'
    else:
        return 'upcoming'

def get_rent_status_label(status):
    labels = {
        'paid': ('Paid', 'success'),
        'overdue': ('OVERDUE', 'danger'),
        'due_soon': ('Due Soon', 'warning'),
        'upcoming': ('Upcoming', 'info'),
    }
    return labels.get(status, ('Unknown', 'secondary'))

def days_until_due(due_date_str):
    due = date.fromisoformat(due_date_str)
    return (due - date.today()).days
