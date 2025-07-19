from flask import Flask,render_template,request,redirect,flash,url_for,session
from models.models import *
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import timedelta

app = Flask(__name__)

#! decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to gain access', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

    
def admin_required(f):
    @wraps(f)
    def decorated_function(*args,**kwargs):
        if 'username' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        admin = Admin.query.filter_by(adm_username=session['username']).first()
        if not admin:
            flash('Admin access required.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

#! User routes
@app.route("/")
@login_required
def home():
    name = session.get("name") if "name" in session else session.get("username")
    username = session.get("username")
    user = User.query.filter_by(username=username).first()
    bookings=[]
    if user:
        bookings=Reservation.query.filter_by(user_id=user.u_id)
    return render_template("home.html",name=name,bookings=bookings)
    


@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        username= request.form.get("username")
        password= request.form.get("password")

        #checking in admin model first
        admin=Admin.query.filter_by(adm_username=username).first()

        if admin and check_password_hash(admin.adm_passhash, password):
            session["username"]=admin.adm_username
            if admin.adm_name:
                session["name"] = admin.adm_name
            flash("Logged in Successfully","success")
            return redirect(url_for("admin"))
        
        #checking for users then
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.passhash,password):
            session['username'] = user.username
            session['name'] = user.u_name
            flash("Logged in","success")
            return redirect(url_for("home"))
        
        flash('Invalid credentials', 'danger')
        return redirect(url_for("login"))
    else:
        return render_template("auth/login.html")

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

@app.route("/register",methods=["GET","POST"])
def register():
    if request.method=="POST":
        username=request.form.get("username")
        password=request.form.get("password")
        u_name=request.form.get("name")
        u_add=request.form.get("address")
        u_pin=request.form.get("pincode")
        passhash=generate_password_hash(password)

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already taken","danger")
            return redirect(url_for('register'))

        new_user = User(username=username,
                        passhash=passhash,
                        u_name=u_name,
                        u_add=u_add,
                        u_pin=u_pin
                        )
        db.session.add(new_user)
        db.session.commit()
        flash("User created successfully","success")
        return redirect(url_for("login"))
    else:
        return render_template("auth/register.html")

@app.route("/book", methods=["GET", "POST"])
def book():
    lots = []
    searched = False

    if request.method == "POST":
        pincode = request.form.get("pincode")
        lots = ParkingLot.query.filter_by(pl_pin=pincode).all()
        searched = True
    
    for lot in lots:
        free_spot = ParkingSpot.query.filter_by(pl_id=lot.pl_id, ps_status=False).first()
        lot.free_spot = free_spot 

    username=session.get("username")
    user=User.query.filter_by(username=username).first()
    customer_id=user.u_id
    return render_template("book.html", lots=lots, searched=searched,customer_id=customer_id)

@app.route("/book/<int:pl_id>", methods=["POST"])
@login_required
def book_now(pl_id):
    vehicle = request.form.get("vehicle")
    duration = request.form.get("duration")
    spot_id = request.form.get("spot_id")  
    
    username = session.get("username")
    user = User.query.filter_by(username=username).first()
    if not user:
        flash("User not found", "danger")
        return redirect(url_for("book"))

    spot = ParkingSpot.query.filter_by(ps_id=spot_id, pl_id=pl_id, ps_status=False).first()
    if not spot:
        flash("No spot is available at the lot right now", "warning")
        return redirect(url_for("book"))
    
    end_time = ist_now() + timedelta(hours=int(duration))

    spot.ps_status = True
    spot.ps_customerid = user.u_id
    spot.ps_vehiclenum = vehicle
    spot.ps_endtime = end_time
    spot.ps_datetime = ist_now()

    
    reservation = Reservation(
        user_id=user.u_id,
        ps_id=spot.ps_id,
        start_time=ist_now(),
        end_time=end_time,
        status=True
    )

    db.session.add(reservation)
    db.session.commit()

    flash(f"Spot {spot.ps_id} successfully booked!", "success")
    return redirect(url_for("book"))

@app.route("/release/<int:r_id>", methods=["POST"])
@login_required
def release(r_id):
    reservation=Reservation.query.filter_by(r_id=r_id).first()

    reservation.endtime=ist_now()
    reservation.status=False

    spot=ParkingSpot.query.filter_by(ps_id=reservation.ps_id).first()

    spot.ps_status = False
    spot.ps_customerid = None
    spot.ps_vehiclenum = None
    spot.ps_endtime = None
    spot.ps_datetime = None

    db.session.commit()
    return redirect(url_for("home"))

#! Admin routes

@app.route("/admin",methods=["GET","POST"])
@admin_required
def admin():
    if request.method=="POST":
        pl_location = request.form.get("location")
        pl_add = request.form.get("address")
        pl_pin = int(request.form.get("pincode"))
        pl_price = int(request.form.get("price"))
        pl_spots = int(request.form.get("numspots"))

        parkinglot=ParkingLot(pl_location=pl_location,pl_add=pl_add,pl_pin=pl_pin,pl_price=pl_price,pl_spots=pl_spots)
        db.session.add(parkinglot)
        db.session.flush()

        for i in range(pl_spots):
            spot=ParkingSpot(pl_id=parkinglot.pl_id)
            db.session.add(spot)

        db.session.commit()
        return redirect(url_for("admin"))
    else:
        lots = ParkingLot.query.all()              
        spots = ParkingSpot.query.all()
        lot_prices = {lot.pl_id: lot.pl_price for lot in lots}

        
        return render_template("admin/admin-dashboard.html", lots=lots, spots=spots, lot_prices=lot_prices)

@app.route("/admin/summary")
@admin_required
def adminSummary():
    return render_template("admin/summary.html")

@app.route("/admin/users")
@admin_required
def viewUsers():
    users=User.query.all()
    return render_template("admin/users.html",users=users)

@app.route("/admin/edit/<int:pl_id>",methods=["POST"])
@admin_required
def editLot(pl_id):
    lot = ParkingLot.query.filter_by(pl_id=pl_id).first()
    if not lot:
        flash("Parking lot not found.", "danger")
        return redirect(url_for("admin"))
    
    lot.pl_location = request.form.get("location")
    lot.pl_add = request.form.get("address")
    lot.pl_pin = int(request.form.get("pincode"))
    lot.pl_price = int(request.form.get("price"))
    lot.pl_spots = int(request.form.get("numspots"))

    db.session.commit()

    flash("Parking lot updated successfully.", "success")
    return redirect(url_for("admin"))

@app.route("/admin/delete/<int:pl_id>", methods=["POST"])
@admin_required
def deleteLot(pl_id):
    lot = ParkingLot.query.get_or_404(pl_id)
    db.session.delete(lot)
    db.session.commit()
    return redirect(url_for("admin"))

