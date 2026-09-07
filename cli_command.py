import os
import click
from flask.cli import with_appcontext
from models import get_db, init_db, DB_PATH

@click.command('reset-db')
@with_appcontext
def reset_db():
    """Reset the database (deletes the sqlite file and re-seeds)."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
    from seed import seed_data
    seed_data()
    click.echo('Database reset and seeded.')

@click.command('list-users')
@with_appcontext
def list_users():
    """List all users."""
    conn = get_db()
    users = conn.execute("SELECT * FROM user").fetchall()
    conn.close()
    for u in users:
        click.echo(f"{u['id']}: {u['username']} ({u['role']}) — {u['full_name']}")