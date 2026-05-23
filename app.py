from config import Config
from routes import *
from models.models import *
from werkzeug.security import generate_password_hash
from datetime import timedelta

app.config.from_object(Config)


db.init_app(app)

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=60)
print(app.config["SQLALCHEMY_DATABASE_URI"])
@app.before_request
def make_session_permanent():
    session.permanent = True 


with app.app_context():
    db.drop_all()
    db.create_all()
    existing_admin = Admin.query.filter_by(adm_username=app.config['ADMIN_USERNAME']).first()
    if not existing_admin:
        password =  app.config['ADMIN_PASSWORD']
        passhash=generate_password_hash(password)
        admin = Admin(adm_username=app.config['ADMIN_USERNAME'],adm_passhash=passhash)
        db.session.add(admin)
        db.session.commit()
if __name__ == '__main__':
    app.run(port=8080)
