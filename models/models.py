from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone, timedelta
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3

db = SQLAlchemy()


IST = timezone(timedelta(hours=5, minutes=30))

def ist_now():
    return datetime.now(IST).replace(tzinfo=None)  

@event.listens_for(Engine, "connect")
def enforce_foreign_keys(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

class User(db.Model):
    u_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    passhash = db.Column(db.String(20), nullable=False)
    u_name = db.Column(db.String(20), nullable=False)
    u_add = db.Column(db.String(80), nullable=False)
    u_pin = db.Column(db.Integer, nullable=False)

class Admin(db.Model):
    adm_id = db.Column(db.Integer, primary_key=True)
    adm_username = db.Column(db.String(20), unique=True, nullable=False)
    adm_passhash = db.Column(db.String(20), nullable=False)
    adm_name = db.Column(db.String(20))

class ParkingLot(db.Model):
    pl_id = db.Column(db.Integer, primary_key=True)
    pl_location = db.Column(db.String(30), nullable=False)
    pl_add = db.Column(db.String(80), nullable=False)
    pl_pin = db.Column(db.Integer, nullable=False)
    pl_price = db.Column(db.Integer, nullable=False)
    pl_spots = db.Column(db.Integer, nullable=False)
    spots = db.relationship('ParkingSpot', backref='lot', cascade='all, delete', passive_deletes=True)

class ParkingSpot(db.Model):
    ps_id = db.Column(db.Integer, primary_key=True)
    pl_id = db.Column(db.Integer, db.ForeignKey('parking_lot.pl_id', ondelete='CASCADE'), nullable=False)
    ps_customerid = db.Column(db.Integer)
    ps_vehiclenum = db.Column(db.String(20))
    ps_status = db.Column(db.Boolean, default=False)
    ps_datetime = db.Column(db.DateTime, default=ist_now)
    ps_endtime = db.Column(db.DateTime, nullable=True)

class Reservation(db.Model):
    r_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.u_id'), nullable=False)

    lot_name = db.Column(db.Integer)     
    spot_number = db.Column(db.Integer)
    lot_price = db.Column(db.Integer)
    lot_location = db.Column(db.String(100))

    ps_id = db.Column(db.Integer, db.ForeignKey('parking_spot.ps_id',ondelete="SET NULL"), nullable=True)
    ps = db.relationship('ParkingSpot', backref='reservation', lazy=True)
    vehicle_number = db.Column(db.String(20))
    start_time = db.Column(db.DateTime, nullable=False, default=ist_now)
    end_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.Boolean(20), default=True)
    created_at = db.Column(db.DateTime, default=ist_now)