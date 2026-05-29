# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime  # Add this import
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()



#----------------------------Model---------------------------------------#


class User(db.Model):
    __tablename__ = "users"
    user_id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    username = db.Column(db.String(120), nullable = False)
    email_id = db.Column(db.String(50), unique = True, nullable = False)
    password = db.Column(db.String(10), nullable = False)
    role = db.Column(db.String(20), nullable = False)    #admin, doctor, patient
    contact_no = db.Column(db.String(30), nullable = True)
    created_at = db.Column(db.DateTime, default = datetime.utcnow)
    blacklist = db.Column(db.Boolean, default = False)   
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable = True)

    department = db.relationship("Dept", back_populates = "doctors")
    #availability = db.relationship("DoctorAvailability", backref="doctor")


    # add to User model
    qualifications = db.Column(db.String(200), nullable=True)
    specialty = db.Column(db.String(100), nullable=True)
    years_experience = db.Column(db.Integer, nullable=True)
    years_specialist = db.Column(db.Integer, nullable=True)
    bio = db.Column(db.Text, nullable=True) 
    photo_url = db.Column(db.String(200), nullable=True)



class Dept(db.Model):
    __tablename__ = "departments"
    id = db.Column(db.Integer, primary_key = True)   # dept_name = db.Coumn(db.String(30), nullable = False)
    dept_name = db.Column(db.String(30), nullable = False)
    description = db.Column(db.String(100), nullable = True)

    doctors = db.relationship("User", back_populates = 'department')

class Appointments(db.Model):

    __tablename__ = "appointment"
    id = db.Column(db.Integer, primary_key = True)
    status = db.Column(db.String(20), default = 'booked')
    doctor_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable = False)
    date = db.Column(db.String(20))
    time = db.Column(db.String(20))

    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    treatment_id = db.Column(db.Integer, db.ForeignKey("treatment.id"), unique = True)

class Treatments(db.Model):

    __tablename__ = "treatment"
    id = db.Column(db.Integer, primary_key = True)
    dignosis = db.Column(db.String(50), nullable = False)
    treatment = db.Column(db.String(100), nullable = False)
    prescription = db.Column(db.String(200), nullable = True)

class DoctorAvailability(db.Model):
    __tablename__ = "doctor_availability"

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)

    date = db.Column(db.String(20), nullable=False)      # e.g. "2025-02-12"
    slot_1 = db.Column(db.Boolean, nullable=True)     
    slot_2 = db.Column(db.Boolean, nullable=True)     
    doctor = db.relationship("User", backref="availability")


#-------------------------------------------------------Model----------------------------#