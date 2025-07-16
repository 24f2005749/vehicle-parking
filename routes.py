from flask import Flask,render_template,request,redirect,flash,url_for,session
from models.models import *
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

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
    name = session["name"] if "name" in session else session["username"]
    return render_template("home.html",name=name)
    


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
            return redirect("/")
        
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
        return redirect("/login")
    else:
        return render_template("auth/register.html")

@app.route("/book")
@login_required
def book():
    render_template("book.html")


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

       
        return render_template("admin/admin-dashboard.html", lots=lots, spots=spots)

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

