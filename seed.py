from models import get_db
from utils import hash_password
from datetime import date, timedelta

def seed_data():
    conn = get_db()
    c = conn.cursor()
    
    if c.execute("SELECT COUNT(*) FROM user").fetchone()[0] > 0:
        conn.close()
        return

    c.execute("INSERT INTO user (username,password,role,full_name,email,phone) VALUES (?,?,?,?,?,?)",
        ('landlord', hash_password('admin123'), 'landlord', 'Maria Santos', 'maria@apartments.ph', '09171234567'))
    c.execute("INSERT INTO user (username,password,role,full_name,email,phone) VALUES (?,?,?,?,?,?)",
        ('tenant1', hash_password('tenant123'), 'tenant', 'Juan dela Cruz', 'juan@email.com', '09181234567'))
    c.execute("INSERT INTO user (username,password,role,full_name,email,phone) VALUES (?,?,?,?,?,?)",
        ('tenant2', hash_password('tenant123'), 'tenant', 'Ana Reyes', 'ana@email.com', '09191234567'))

    t1_id = c.execute("SELECT id FROM user WHERE username='tenant1'").fetchone()[0]
    t2_id = c.execute("SELECT id FROM user WHERE username='tenant2'").fetchone()[0]

    from datetime import date as _d
    occ_start = _d.today().replace(day=1).isoformat()
    units = [
        ('101', 1, 'Studio', 8500, 'Comfortable Studio unit on floor 1.', 'WiFi, AC, Water', 1, t1_id, occ_start, 5),
        ('102', 1, '1 Bedroom', 12000, 'Spacious 1 Bedroom on floor 1.', 'WiFi, AC, Water, Parking', 0, None, None, 1),
        ('103', 1, '2 Bedroom', 18000, 'Large 2 Bedroom on floor 1.', 'WiFi, AC, Water, Parking, Balcony', 1, t2_id, occ_start, 5),
        ('201', 2, 'Studio', 9000, 'Comfortable Studio on floor 2.', 'WiFi, AC, Water', 0, None, None, 1),
        ('202', 2, '1 Bedroom', 13000, 'Bright 1 Bedroom on floor 2.', 'WiFi, AC, Water, Parking', 0, None, None, 1),
        ('203', 2, '2 Bedroom', 19000, 'Premium 2 Bedroom on floor 2.', 'WiFi, AC, Water, Parking, Balcony', 0, None, None, 1),
        ('301', 3, 'Studio', 9500, 'Top floor Studio.', 'WiFi, AC, Water', 0, None, None, 1),
        ('302', 3, '1 Bedroom', 14000, 'Corner 1 Bedroom with city view.', 'WiFi, AC, Water, Parking, City View', 0, None, None, 1),
    ]
    for u in units:
        c.execute("INSERT INTO unit (unit_number,floor,unit_type,monthly_rent,description,amenities,is_occupied,tenant_id,occupancy_start,monthly_due_day) VALUES (?,?,?,?,?,?,?,?,?,?)", u)

    u101 = c.execute("SELECT id FROM unit WHERE unit_number='101'").fetchone()[0]
    u103 = c.execute("SELECT id FROM unit WHERE unit_number='103'").fetchone()[0]
    today = date.today()

    past_due = (date(today.year, today.month, 5) - timedelta(days=30)).isoformat()
    paid_on = (date(today.year, today.month, 5) - timedelta(days=32)).isoformat()
    c.execute("INSERT INTO rent_record (unit_id,tenant_id,amount,due_date,paid_date,is_paid,month_year) VALUES (?,?,?,?,?,?,?)",
        (u101, t1_id, 8500, past_due, paid_on, 1, (date.today() - timedelta(days=30)).strftime('%B %Y')))

    curr_due = date(today.year, today.month, min(today.day + 3, 28)).isoformat()
    c.execute("INSERT INTO rent_record (unit_id,tenant_id,amount,due_date,is_paid,month_year) VALUES (?,?,?,?,?,?)",
        (u101, t1_id, 8500, curr_due, 0, today.strftime('%B %Y')))

    overdue = (today - timedelta(days=5)).isoformat()
    c.execute("INSERT INTO rent_record (unit_id,tenant_id,amount,due_date,is_paid,month_year) VALUES (?,?,?,?,?,?)",
        (u103, t2_id, 18000, overdue, 0, today.strftime('%B %Y')))

    conn.commit()
    conn.close()