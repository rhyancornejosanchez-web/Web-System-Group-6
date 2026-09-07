import click
from flask.cli import with_appcontext
from models import db, User, Unit, RentRecord
from utils import hash_password
from datetime import date

@click.command('reset-db')
@with_appcontext
def reset_db():
    """Reset the database."""
    db.drop_all()
    db.create_all()
    from seed import seed_data
    seed_data()
    click.echo('Database reset and seeded.')

@click.command('list-users')
@with_appcontext
def list_users():
    """List all users."""
    users = User.query.all()
    for u in users:
        click.echo(f"{u.id}: {u.username} ({u.role}) — {u.full_name}")