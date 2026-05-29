from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template
from models import User, Dept, Appointments, db, Treatments,DoctorAvailability
from sqlalchemy.orm import aliased
from controllers.auth_controller import auth_routes
from controllers.patient_controller import patient_routes
from controllers.doctor_controller import doctor_routes
from controllers.admin_controller import admin_routes
import os

app = Flask(__name__)

# Base Directory
base_dir = os.path.abspath(os.path.dirname(__file__))
instance_dir = os.path.join(base_dir, "instance")
# If Instance folder doesn't exist, create it
if not os.path.exists(instance_dir):
    os.makedirs(instance_dir)
    print("✓ 'instance' folder created")


app.config['SECRET_KEY'] = 'MediManagement'
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(instance_dir, 'hospital_management.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Here we are initializing the database with the Flask app
db.init_app(app)



@app.route('/')
def base():
    return render_template("base.html")

@app.route('/index')
def index():
    return render_template("index.html")

#authentication Blueprint
app.register_blueprint(auth_routes, url_prefix='/auth')

# Patient Blueprint
app.register_blueprint(patient_routes, url_prefix='/patient')

# Doctor Blueprint
app.register_blueprint(doctor_routes, url_prefix='/doctor')

# Admin Blueprint
app.register_blueprint(admin_routes, url_prefix='/admin_dash')


@app.route("/department/<int:dept_id>")
def department_detail(dept_id):

    dept = Dept.query.get_or_404(dept_id)

    # doctors in that particular deprtment
    doctors = User.query.filter_by(role="doctor", department_id=dept_id).order_by(User.username).all()

    # this is department_description
    department_description = dept.description 

    return render_template("department_detail.html",dept=dept,doctors=doctors, department_description=department_description
    )
@app.route('/history/<int:patient_id>')
def patient_history(patient_id):
    patient = User.query.get_or_404(patient_id)

    history_rows = (
        db.session.query(
            Appointments.id.label("appt_id"),
            Appointments.date,
            Appointments.time,
            Appointments.user_id.label("patient_id"),
            Appointments.status,
            Treatments.dignosis,
            Treatments.treatment,
            Treatments.prescription,
            User.username.label("doctor_name"),
            Dept.dept_name.label("department_name")
        )
        .outerjoin(Treatments, Treatments.id == Appointments.treatment_id)
        .join(User, User.user_id == Appointments.doctor_id)
        .outerjoin(Dept, Dept.id == User.department_id)
        .filter(Appointments.user_id == patient_id)
        .order_by(Appointments.id.asc())
        .all()
    )

    return render_template("history.html", patient=patient, history=history_rows)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        existing_admin = User.query.filter_by(username = "admin").first()

        if not existing_admin:
            admin_database = User(
                username= "admin",
                password= "admin123",
                email_id= "admin123@gmail.com",
                role= "admin"

            )
            db.session.add(admin_database)
            db.session.commit()
            

    app.run(debug = True)
