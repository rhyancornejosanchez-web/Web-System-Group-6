import click
from flask.cli import with_appcontext
from models import get_db, init_db

@click.command('reset-db')
@with_appcontext
def reset_db():
    """Reset the database (drops all tables, recreates them, and re-seeds)."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SET FOREIGN_KEY_CHECKS=0")
    for table in ('rent_record', 'message', 'notification', 'unit', 'user'):
        c.execute(f"DROP TABLE IF EXISTS {table}")
    c.execute("SET FOREIGN_KEY_CHECKS=1")
    conn.commit()
    conn.close()

    init_db()
    from seed import seed_data
    seed_data()
    click.echo('Database reset and seeded.')

@click.command('list-users')
@with_appcontext
def list_users():
    """List all users."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM user")
    users = c.fetchall()
    conn.close()
    for u in users:
        click.echo(f"{u['id']}: {u['username']} ({u['role']}, {u.get('status','approved')}) — {u['full_name']}")