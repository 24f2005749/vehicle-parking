from flask_sqlalchemy import SQLAlchemy
from datetime import datetime,timezone

db=SQLAlchemy()

class User(db.Model):
    u_id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(20),unique=True,nullable=False)
    passhash = db.Column(db.String(20),nullable=False)
    u_name=db.Column(db.String(20),nullable=False)
    u_add=db.Column(db.String(80),nullable=False)
    u_pin=db.Column(db.Integer,nullable=False)

class Admin(db.Model):
    adm_id=db.Column(db.Integer,primary_key=True)
    adm_username=db.Column(db.String(20),unique=True,nullable=False)
    adm_passhash=db.Column(db.String(20),nullable=False)
    adm_name=db.Column(db.String(20))

class ParkingLot(db.Model):
    pl_id=db.Column(db.Integer,primary_key=True)
    pl_location=db.Column(db.String(30),nullable=False)
    pl_add=db.Column(db.String(80),nullable=False)
    pl_pin=db.Column(db.Integer,nullable=False)
    pl_price=db.Column(db.Integer,nullable=False)
    pl_spots=db.Column(db.Integer,nullable=False)
    spots = db.relationship('ParkingSpot', backref='lot', cascade='all, delete', passive_deletes=True)

#! cascading isnt working fix it
class ParkingSpot(db.Model):
    ps_id=db.Column(db.Integer,primary_key=True)
    pl_id=db.Column(db.Integer, db.ForeignKey('parking_lot.pl_id',ondelete='CASCADE'), nullable=False)
    ps_customerid=db.Column(db.Integer)
    ps_vehiclenum=db.Column(db.String(20))
    ps_status=db.Column(db.Boolean,default=False)
    ps_datetime=db.Column(db.DateTime)



class Reservation(db.Model):
    r_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.u_id', ondelete='CASCADE'), nullable=False)
    ps_id = db.Column(db.Integer, db.ForeignKey('parking_spot.ps_id', ondelete='CASCADE'), nullable=False)
    start_time = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    end_time = db.Column(db.DateTime(timezone=True), nullable=True)
    status = db.Column(db.String(20), default="active")
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


