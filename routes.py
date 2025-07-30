from flask import Flask,render_template,request,redirect,flash,url_for,session
from models.models import *
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import timedelta
from sqlalchemy.orm import joinedload
from collections import Counter, defaultdict

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
        bookings = Reservation.query.filter_by(user_id=user.u_id).options(joinedload(Reservation.ps).joinedload(ParkingSpot.lot)).all()
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
    spot_price = request.form.get("spot_price")
    
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

    lot=ParkingLot.query.filter_by(pl_id=pl_id).first()
    reservation = Reservation(
        user_id=user.u_id,
        ps_id=spot.ps_id,
        start_time=ist_now(),
        end_time=end_time,
        status=True,
        vehicle_number=vehicle,
        lot_name=spot.pl_id,       
        spot_number=spot.ps_id,
        lot_price=spot_price,
        lot_location=lot.pl_location
    )

    db.session.add(reservation)
    db.session.commit()

    flash(f"Spot {spot.ps_id} successfully booked!", "success")
    return redirect(url_for("book"))

@app.route("/release/<int:r_id>", methods=["POST"])
@login_required
def release(r_id):
    reservation=Reservation.query.filter_by(r_id=r_id).first()

    reservation.end_time=ist_now()
    reservation.status=False

    spot=ParkingSpot.query.filter_by(ps_id=reservation.ps_id).first()

    spot.ps_status = False
    spot.ps_customerid = None
    spot.ps_vehiclenum = None
    spot.ps_endtime = None
    spot.ps_datetime = None

    db.session.commit()
    return redirect(url_for("home"))

@app.route("/summary")
@login_required
def summary():
    username = session.get("username")
    user = User.query.filter_by(username=username).first()

    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("home"))

    user_id = user.u_id

    reservations = Reservation.query.filter_by(user_id=user_id).all()
    active_reservations = [r for r in reservations if r.status]
    total_reservations = len(reservations)
    total_active = len(active_reservations)

    total_price_spent = 0
    total_hours_parked = 0.0

    for res in reservations:
        if res.end_time and res.start_time:
            duration = (res.end_time - res.start_time).total_seconds() / 3600
        elif res.start_time:
            duration = (datetime.now() - res.start_time).total_seconds() / 3600
        else:
            duration = 0

        if res.ps and res.ps.lot:
            price = res.ps.lot.pl_price
            total_price_spent += price * duration
        total_hours_parked += duration

    today = datetime.now().date()
    week_ago = today - timedelta(days=6)
    past_week_reservations = Reservation.query.filter(
        Reservation.user_id == user_id,
        Reservation.start_time >= week_ago
    ).all()

    hours_by_day = defaultdict(float)
    for res in past_week_reservations:
        start = res.start_time
        end = res.end_time or datetime.now()
        hours = (end - start).total_seconds() / 3600
        day = start.strftime('%a')
        hours_by_day[day] += hours

    week_days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    chart_labels = week_days
    chart_data = [round(hours_by_day.get(day, 0), 2) for day in week_days]

    return render_template("summary.html",
                           name=session.get('name'),
                           chart_labels=chart_labels,
                           chart_data=chart_data,
                           total_reservations=total_reservations,
                           active_reservations=total_active,
                           total_price_spent=round(total_price_spent, 2),
                           total_hours_parked=round(total_hours_parked, 2))


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
        
        avail = {lot.pl_id: 0 for lot in lots}
        for spot in spots:
            if not spot.ps_status:
                avail[spot.pl_id] += 1

        
        return render_template("admin/admin-dashboard.html", lots=lots, spots=spots, lot_prices=lot_prices,avail=avail)

@app.route("/admin/users")
@admin_required
def viewUsers():
    users=User.query.all()
    return render_template("admin/users.html",users=users)

@app.route("/admin/edit/<int:pl_id>", methods=["POST"])
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
    
    new_total_spots = int(request.form.get("numspots"))
    current_spots = ParkingSpot.query.filter_by(pl_id=pl_id).all()
    current_count = len(current_spots)

    if new_total_spots > current_count:
        for i in range(new_total_spots - current_count):
            new_spot = ParkingSpot(pl_id=pl_id)
            db.session.add(new_spot)
    

    elif new_total_spots < current_count:

        removable_spots = ParkingSpot.query.filter(
            ParkingSpot.pl_id == pl_id,
            ~ParkingSpot.reservation.any(Reservation.status == True)
        ).order_by(ParkingSpot.ps_id.desc()).all()

        spots_to_remove = removable_spots[: current_count - new_total_spots]

        if len(spots_to_remove) < (current_count - new_total_spots):
            flash("Cannot delete spots: Some are reserved", "danger")
            return redirect(url_for("admin"))

        for spot in spots_to_remove:
            db.session.delete(spot)

    lot.pl_spots = new_total_spots

    db.session.commit()
    flash("Parking lot updated successfully.", "success")
    return redirect(url_for("admin"))
@app.route("/admin/delete/<int:pl_id>", methods=["POST"])
@admin_required
def deleteLot(pl_id):

    lot = ParkingLot.query.get_or_404(pl_id)
    spots = ParkingSpot.query.filter_by(pl_id=pl_id).all()
    spot_ids = [spot.ps_id for spot in spots]
    active_res = Reservation.query.filter(
        Reservation.ps_id.in_(spot_ids),
        Reservation.status == True 
    ).first()

    if active_res:
        flash("Cannot delete lot: one or more spots are currently reserved.", "danger")
        return redirect(url_for("admin"))

    db.session.delete(lot)
    db.session.commit()
    return redirect(url_for("admin"))

@app.route("/admin/summary")
@admin_required
def adminSummary():
    total_reservations = Reservation.query.count()
    active_reservations = Reservation.query.filter_by(status=True).count()
    total_users = User.query.count()
    total_lots = ParkingLot.query.count()

    today = datetime.now().date()
    week = today - timedelta(days=6)

    reservations = Reservation.query.filter(Reservation.created_at >= week).all()

    counts = Counter(res.created_at.strftime('%a') for res in reservations)

    week_days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    chart_labels = week_days
    chart_data = [counts.get(day, 0) for day in week_days]

    return render_template("admin/summary.html",
                           total_reservations=total_reservations,
                           active_reservations=active_reservations,
                           total_users=total_users,
                           total_lots=total_lots,
                           chart_labels=chart_labels,
                           chart_data=chart_data)