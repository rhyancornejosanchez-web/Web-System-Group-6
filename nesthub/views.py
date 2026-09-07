from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import get_db
from utils import check_password, hash_password, get_rent_status, get_rent_status_label, days_until_due
from functools import wraps
from datetime import date, datetime

main_bp = Blueprint('main', __name__)

def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            uid = session.get('user_id')
            if not uid:
                flash('Please log in.', 'warning')
                return redirect(url_for('main.login'))
            if role and session.get('user_role') != role:
                flash('Access denied.', 'danger')
                return redirect(url_for('main.login'))
            return f(*args, **kwargs)
        return wrapped
    return decorator

def row_to_dict(row):
    return dict(row) if row else None

@main_bp.route('/')
def index():
    return redirect(url_for('main.login'))

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','')
        if not username or not password:
            flash('Username and password required.', 'danger')
            return render_template('login.html')
        conn = get_db()
        user = row_to_dict(conn.execute("SELECT * FROM user WHERE username=?", (username,)).fetchone())
        conn.close()
        if user and check_password(password, user['password']):
            session['user_id'] = user['id']
            session['user_role'] = user['role']
            session['user_name'] = user['full_name']
            flash(f"Welcome back, {user['full_name']}!", 'success')
            return redirect(url_for('main.landlord_dashboard') if user['role']=='landlord' else url_for('main.tenant_dashboard'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','')
        confirm  = request.form.get('confirm_password','')
        full_name= request.form.get('full_name','').strip()
        email    = request.form.get('email','').strip()
        phone    = request.form.get('phone','').strip()
        role     = request.form.get('role','tenant')
        if not username or not password or not full_name:
            flash('Username, full name, and password are required.', 'danger')
            return render_template('register.html')
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
        if role not in ('tenant', 'landlord'):
            role = 'tenant'
        conn = get_db()
        existing = conn.execute("SELECT id FROM user WHERE username=?", (username,)).fetchone()
        if existing:
            conn.close()
            flash('Username already taken.', 'danger')
            return render_template('register.html')
        conn.execute(
            "INSERT INTO user (username, password, role, full_name, email, phone) VALUES (?,?,?,?,?,?)",
            (username, hash_password(password), role, full_name, email, phone)
        )
        conn.commit()
        conn.close()
        flash('Account created! Please sign in.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html')

@main_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))

# ─── HELPERS ───────────────────────────────────────────────────────────────────

def get_unread_msgs(uid):
    conn = get_db()
    n = conn.execute("SELECT COUNT(*) FROM message WHERE receiver_id=? AND is_read=0", (uid,)).fetchone()[0]
    conn.close()
    return n

# ─── TENANT ROUTES ─────────────────────────────────────────────────────────────

@main_bp.route('/tenant/dashboard')
@login_required(role='tenant')
def tenant_dashboard():
    uid = session['user_id']
    conn = get_db()
    user = row_to_dict(conn.execute("SELECT * FROM user WHERE id=?", (uid,)).fetchone())
    unit = row_to_dict(conn.execute("SELECT * FROM unit WHERE tenant_id=?", (uid,)).fetchone())
    rent_records = []
    rent_alerts = []
    if unit:
        rent_records = [row_to_dict(r) for r in conn.execute(
            "SELECT * FROM rent_record WHERE unit_id=? AND tenant_id=? ORDER BY due_date DESC", (unit['id'], uid)).fetchall()]
        for rr in rent_records:
            status = get_rent_status(rr['due_date'], rr['is_paid'])
            if status in ('overdue','due_soon'):
                label, color = get_rent_status_label(status)
                rent_alerts.append({'record':rr,'status':status,'label':label,'color':color,'days':days_until_due(rr['due_date'])})
    unread_msgs = get_unread_msgs(uid)
    conn.close()
    return render_template('tenant_dashboard.html', user=user, unit=unit, rent_records=rent_records,
        rent_alerts=rent_alerts, unread_msgs=unread_msgs,
        get_rent_status=get_rent_status, get_rent_status_label=get_rent_status_label, days_until_due=days_until_due)

@main_bp.route('/tenant/units')
@login_required(role='tenant')
def tenant_units():
    uid = session['user_id']
    conn = get_db()
    user = row_to_dict(conn.execute("SELECT * FROM user WHERE id=?", (uid,)).fetchone())
    units = [row_to_dict(r) for r in conn.execute("SELECT * FROM unit ORDER BY floor, unit_number").fetchall()]
    floors = sorted(set(u['floor'] for u in units))
    unread_msgs = get_unread_msgs(uid)
    conn.close()
    return render_template('tenant_units.html', user=user, units=units, floors=floors, unread_msgs=unread_msgs)

@main_bp.route('/tenant/inquire/<int:unit_id>', methods=['GET','POST'])
@login_required(role='tenant')
def tenant_inquire(unit_id):
    uid = session['user_id']
    conn = get_db()
    user = row_to_dict(conn.execute("SELECT * FROM user WHERE id=?", (uid,)).fetchone())
    unit = row_to_dict(conn.execute("SELECT * FROM unit WHERE id=?", (unit_id,)).fetchone())
    if not unit:
        conn.close()
        return redirect(url_for('main.tenant_units'))
    if unit['is_occupied']:
        conn.close()
        flash('This unit is already occupied.', 'warning')
        return redirect(url_for('main.tenant_units'))
    landlord = row_to_dict(conn.execute("SELECT * FROM user WHERE role='landlord' LIMIT 1").fetchone())
    if request.method == 'POST':
        subject = request.form.get('subject','').strip()
        body = request.form.get('body','').strip()
        if subject and body:
            conn.execute("INSERT INTO message (sender_id,receiver_id,subject,body,message_type,unit_id) VALUES (?,?,?,?,?,?)",
                (uid, landlord['id'], subject, body, 'inquiry', unit_id))
            conn.commit()
            conn.close()
            flash('Your inquiry has been sent!', 'success')
            return redirect(url_for('main.tenant_units'))
        flash('Subject and message are required.', 'danger')
    unread_msgs = get_unread_msgs(uid)
    conn.close()
    return render_template('tenant_inquire.html', user=user, unit=unit, unread_msgs=unread_msgs)

@main_bp.route('/tenant/message', methods=['GET','POST'])
@login_required(role='tenant')
def tenant_message():
    uid = session['user_id']
    conn = get_db()
    user = row_to_dict(conn.execute("SELECT * FROM user WHERE id=?", (uid,)).fetchone())
    landlord = row_to_dict(conn.execute("SELECT * FROM user WHERE role='landlord' LIMIT 1").fetchone())
    if request.method == 'POST':
        subject = request.form.get('subject','').strip()
        body = request.form.get('body','').strip()
        if subject and body:
            conn.execute("INSERT INTO message (sender_id,receiver_id,subject,body,message_type) VALUES (?,?,?,?,?)",
                (uid, landlord['id'], subject, body, 'concern'))
            conn.commit()
            conn.close()
            flash('Message sent!', 'success')
            return redirect(url_for('main.tenant_messages'))
        flash('Subject and message required.', 'danger')
    unread_msgs = get_unread_msgs(uid)
    conn.close()
    return render_template('tenant_message.html', user=user, unread_msgs=unread_msgs)

@main_bp.route('/tenant/messages')
@login_required(role='tenant')
def tenant_messages():
    uid = session['user_id']
    conn = get_db()
    user = row_to_dict(conn.execute("SELECT * FROM user WHERE id=?", (uid,)).fetchone())
    messages = [row_to_dict(r) for r in conn.execute(
        """SELECT m.*, u.full_name as sender_name, un.unit_number as unit_number
           FROM message m JOIN user u ON u.id=m.sender_id
           LEFT JOIN unit un ON un.id=m.unit_id
           WHERE m.sender_id=? OR m.receiver_id=?
           ORDER BY m.created_at DESC""", (uid, uid)).fetchall()]
    # Mark messages received by this tenant as read
    conn.execute("UPDATE message SET is_read=1 WHERE receiver_id=?", (uid,))
    conn.commit()
    unread_msgs = 0
    conn.close()
    return render_template('tenant_messages.html', user=user, messages=messages, unread_msgs=unread_msgs)

# ─── LANDLORD ROUTES ────────────────────────────────────────────────────────────

@main_bp.route('/landlord/dashboard')
@login_required(role='landlord')
def landlord_dashboard():
    uid = session['user_id']
    conn = get_db()
    user = row_to_dict(conn.execute("SELECT * FROM user WHERE id=?", (uid,)).fetchone())
    units = [row_to_dict(r) for r in conn.execute("SELECT * FROM unit").fetchall()]
    occupied = sum(1 for u in units if u['is_occupied'])
    available = len(units) - occupied
    unread_msgs = get_unread_msgs(uid)
    overdue_rents = [row_to_dict(r) for r in conn.execute("SELECT * FROM rent_record WHERE is_paid=0").fetchall()]
    overdue_count = sum(1 for r in overdue_rents if get_rent_status(r['due_date'], r['is_paid']) == 'overdue')
    conn.close()
    return render_template('landlord_dashboard.html', user=user, units=units, occupied=occupied,
        available=available, unread_msgs=unread_msgs,
        overdue_count=overdue_count)

@main_bp.route('/landlord/units')
@login_required(role='landlord')
def landlord_units():
    uid = session['user_id']
    conn = get_db()
    user = row_to_dict(conn.execute("SELECT * FROM user WHERE id=?", (uid,)).fetchone())
    units = [row_to_dict(r) for r in conn.execute(
        "SELECT u.*, t.full_name as tenant_name FROM unit u LEFT JOIN user t ON t.id=u.tenant_id ORDER BY u.floor, u.unit_number").fetchall()]
    unread_msgs = get_unread_msgs(uid)
    # Tenants without a unit assigned (for occupy modal)
    tenants_list = [row_to_dict(r) for r in conn.execute(
        "SELECT id, username, full_name FROM user WHERE role='tenant'").fetchall()]
    import json
    tenants_json = json.dumps(tenants_list)
    conn.close()
    return render_template('landlord_unit.html', user=user, units=units, unread_msgs=unread_msgs, tenants_json=tenants_json)

@main_bp.route('/landlord/units/add', methods=['GET','POST'])
@login_required(role='landlord')
def landlord_add_unit():
    uid = session['user_id']
    conn = get_db()
    user = row_to_dict(conn.execute("SELECT * FROM user WHERE id=?", (uid,)).fetchone())
    if request.method == 'POST':
        un = request.form.get('unit_number','').strip()
        floor = request.form.get('floor','')
        ut = request.form.get('unit_type','').strip()
        rent = request.form.get('monthly_rent','')
        desc = request.form.get('description','').strip()
        amen = request.form.get('amenities','').strip()
        try:
            existing = conn.execute("SELECT id FROM unit WHERE unit_number=?", (un,)).fetchone()
            if existing:
                flash('Unit number already exists.', 'danger')
            else:
                conn.execute("INSERT INTO unit (unit_number,floor,unit_type,monthly_rent,description,amenities) VALUES (?,?,?,?,?,?)",
                    (un, int(floor), ut, float(rent), desc, amen))
                conn.commit()
                conn.close()
                flash(f'Unit {un} added!', 'success')
                return redirect(url_for('main.landlord_units'))
        except (ValueError, TypeError):
            flash('Invalid floor or rent value.', 'danger')
    unread_msgs = get_unread_msgs(uid)
    conn.close()
    return render_template('landlord_unit_form.html', user=user, unit=None, unread_msgs=unread_msgs)

@main_bp.route('/landlord/units/edit/<int:unit_id>', methods=['GET','POST'])
@login_required(role='landlord')
def landlord_edit_unit(unit_id):
    uid = session['user_id']
    conn = get_db()
    user = row_to_dict(conn.execute("SELECT * FROM user WHERE id=?", (uid,)).fetchone())
    unit = row_to_dict(conn.execute("SELECT * FROM unit WHERE id=?", (unit_id,)).fetchone())
    if not unit:
        conn.close()
        return redirect(url_for('main.landlord_units'))
    if request.method == 'POST':
        un = request.form.get('unit_number','').strip()
        floor = request.form.get('floor','')
        ut = request.form.get('unit_type','').strip()
        rent = request.form.get('monthly_rent','')
        desc = request.form.get('description','').strip()
        amen = request.form.get('amenities','').strip()
        try:
            conn.execute("UPDATE unit SET unit_number=?,floor=?,unit_type=?,monthly_rent=?,description=?,amenities=? WHERE id=?",
                (un, int(floor), ut, float(rent), desc, amen, unit_id))
            conn.commit()
            conn.close()
            flash('Unit updated!', 'success')
            return redirect(url_for('main.landlord_units'))
        except (ValueError, TypeError):
            flash('Invalid floor or rent.', 'danger')
    unread_msgs = get_unread_msgs(uid)
    conn.close()
    return render_template('landlord_unit_form.html', user=user, unit=unit, unread_msgs=unread_msgs)

@main_bp.route('/landlord/units/delete/<int:unit_id>', methods=['POST'])
@login_required(role='landlord')
def landlord_delete_unit(unit_id):
    conn = get_db()
    unit = row_to_dict(conn.execute("SELECT * FROM unit WHERE id=?", (unit_id,)).fetchone())
    if unit and unit['is_occupied']:
        flash('Cannot delete an occupied unit.', 'danger')
    elif unit:
        conn.execute("UPDATE message SET unit_id=NULL WHERE unit_id=?", (unit_id,))
        conn.execute("DELETE FROM rent_record WHERE unit_id=?", (unit_id,))
        conn.execute("DELETE FROM unit WHERE id=?", (unit_id,))
        conn.commit()
        flash('Unit deleted.', 'success')
    conn.close()
    return redirect(url_for('main.landlord_units'))

@main_bp.route('/landlord/units/set_occupancy/<int:unit_id>', methods=['POST'])
@login_required(role='landlord')
def landlord_set_occupancy(unit_id):
    action = request.form.get('action')  # 'occupy' or 'vacate'
    conn = get_db()
    unit = row_to_dict(conn.execute("SELECT * FROM unit WHERE id=?", (unit_id,)).fetchone())
    if not unit:
        conn.close()
        flash('Unit not found.', 'danger')
        return redirect(url_for('main.landlord_units'))

    if action == 'occupy':
        tenant_id = request.form.get('tenant_id','').strip()
        occupancy_start = request.form.get('occupancy_start','').strip()
        due_day = request.form.get('monthly_due_day','1').strip()
        if not tenant_id or not occupancy_start:
            conn.close()
            flash('Tenant and start date are required.', 'danger')
            return redirect(url_for('main.landlord_units'))
        try:
            due_day_int = int(due_day)
            if due_day_int < 1 or due_day_int > 28:
                due_day_int = 1
        except ValueError:
            due_day_int = 1
        # Assign unit
        conn.execute(
            "UPDATE unit SET is_occupied=1, tenant_id=?, occupancy_start=?, monthly_due_day=? WHERE id=?",
            (tenant_id, occupancy_start, due_day_int, unit_id)
        )
        # Generate first rent record
        start = date.fromisoformat(occupancy_start)
        import calendar
        # Find the next due date after start
        max_day = calendar.monthrange(start.year, start.month)[1]
        actual_day = min(due_day_int, max_day)
        first_due = date(start.year, start.month, actual_day)
        if first_due < start:
            # Move to next month
            if start.month == 12:
                first_due = date(start.year + 1, 1, min(due_day_int, 28))
            else:
                max_day2 = calendar.monthrange(start.year, start.month+1)[1]
                first_due = date(start.year, start.month+1, min(due_day_int, max_day2))
        month_year = first_due.strftime('%B %Y')
        existing = conn.execute(
            "SELECT id FROM rent_record WHERE unit_id=? AND tenant_id=? AND month_year=?",
            (unit_id, tenant_id, month_year)
        ).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO rent_record (unit_id,tenant_id,amount,due_date,month_year) VALUES (?,?,?,?,?)",
                (unit_id, tenant_id, unit['monthly_rent'], str(first_due), month_year)
            )
        conn.commit()
        tenant_user = row_to_dict(conn.execute("SELECT full_name FROM user WHERE id=?", (tenant_id,)).fetchone())
        conn.close()
        tname = tenant_user['full_name'] if tenant_user else 'Tenant'
        flash(f"Unit {unit['unit_number']} is now occupied by {tname}. First due date: {first_due}.", 'success')
    elif action == 'vacate':
        conn.execute("UPDATE unit SET is_occupied=0, tenant_id=NULL, occupancy_start=NULL WHERE id=?", (unit_id,))
        conn.commit()
        conn.close()
        flash(f"Unit {unit['unit_number']} is now available.", 'success')
    else:
        conn.close()
    return redirect(url_for('main.landlord_units'))

@main_bp.route('/landlord/messages')
@login_required(role='landlord')
def landlord_messages():
    uid = session['user_id']
    conn = get_db()
    user = row_to_dict(conn.execute("SELECT * FROM user WHERE id=?", (uid,)).fetchone())
    messages = [row_to_dict(r) for r in conn.execute(
        """SELECT m.*, u.full_name as sender_name, un.unit_number as unit_number
           FROM message m JOIN user u ON u.id=m.sender_id
           LEFT JOIN unit un ON un.id=m.unit_id
           WHERE m.receiver_id=? ORDER BY m.created_at DESC""", (uid,)).fetchall()]
    conn.execute("UPDATE message SET is_read=1 WHERE receiver_id=?", (uid,))
    conn.commit()
    unread_msgs = 0
    conn.close()
    return render_template('landlord_messages.html', user=user, messages=messages, unread_msgs=unread_msgs)

@main_bp.route('/landlord/messages/reply/<int:msg_id>', methods=['POST'])
@login_required(role='landlord')
def landlord_reply(msg_id):
    uid = session['user_id']
    conn = get_db()
    original = row_to_dict(conn.execute("SELECT * FROM message WHERE id=?", (msg_id,)).fetchone())
    body = request.form.get('reply_body','').strip()
    if body and original:
        original_subject = original['subject']
        conn.execute("INSERT INTO message (sender_id,receiver_id,subject,body,message_type) VALUES (?,?,?,?,?)",
            (uid, original['sender_id'], f"Re: {original_subject}", body, 'general'))
        conn.commit()
        flash('Reply sent!', 'success')
    conn.close()
    return redirect(url_for('main.landlord_messages'))

@main_bp.route('/landlord/tenants')
@login_required(role='landlord')
def landlord_tenants():
    uid = session['user_id']
    conn = get_db()
    user = row_to_dict(conn.execute("SELECT * FROM user WHERE id=?", (uid,)).fetchone())
    tenants = [row_to_dict(r) for r in conn.execute(
        "SELECT u.*, un.id as unit_id, un.unit_number, un.unit_type, un.monthly_rent FROM user u LEFT JOIN unit un ON un.tenant_id=u.id WHERE u.role='tenant'").fetchall()]
    rent_statuses = {}
    for t in tenants:
        if t['unit_id']:
            rr = row_to_dict(conn.execute(
                "SELECT * FROM rent_record WHERE unit_id=? AND tenant_id=? ORDER BY due_date DESC LIMIT 1",
                (t['unit_id'], t['id'])).fetchone())
            if rr:
                status = get_rent_status(rr['due_date'], rr['is_paid'])
                label, color = get_rent_status_label(status)
                rent_statuses[t['id']] = {'status': status, 'label': label, 'color': color, 'record': rr}
    unread_msgs = get_unread_msgs(uid)
    conn.close()
    return render_template('landlord_tenants.html', user=user, tenants=tenants,
        rent_statuses=rent_statuses, unread_msgs=unread_msgs)
