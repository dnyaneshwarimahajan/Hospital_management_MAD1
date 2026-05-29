from flask import Blueprint, flash, render_template, redirect, url_for, request, session
from models import User, Dept, Appointments, db, Treatments,DoctorAvailability



auth_routes = Blueprint('auth', __name__)



@auth_routes.route('/login',methods = ["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        # print(username)
        # print(password)

        user =  User.query.filter_by(username =username).first()

        if not user:
            print("This is invalid user")
            return redirect(url_for('auth.login'))
        # Check Password
        if user.password != password:
            flash("Invalid Password","danger")
            return redirect(url_for('auth.login'))
        
        if user.blacklist == True:
            flash("You are blacklisted contact adminstrator", "Danger")
            return redirect(url_for('auth.login'))
        
        if user and user.role == "patient":
            session['name'] = user.username
            session['id'] = user.user_id
            session['role'] = user.role
            return redirect(url_for('patient.patient_dashboard'))
        
        if user and user.role == "doctor":
            session['name'] = user.username
            session['id'] = user.user_id
            session['role'] = user.role
            return redirect(url_for('doctor.doctor_dashboard'))
        
        if user and user.role == "admin":
            session['name'] = user.username
            session['id'] = user.user_id
            session['role'] = user.role
            return redirect(url_for('admin.admin_dashboard'))
        
        
        return redirect(url_for('register'))   
        
   
    return render_template("login.html")


@auth_routes.route('/register', methods = ["POST","GET"])
def register():
    if request.method == "POST":
        print("Register POST hit!") 
        name = request.form['username']
        email_id =   request.form["email_id"]
        password =request.form["password"]
        contact_no = request.form["contact_no"]

        existing_user = User.query.filter_by( email_id=email_id,username = name).first()
        if existing_user:
            return redirect(url_for('auth.login' ))
        

        new_register = User(username = name,email_id = email_id,password =password, contact_no = contact_no,role ="patient")
        db.session.add(new_register)
        db.session.commit()
        return redirect(url_for('auth.login') )
    return render_template("register.html")



@auth_routes.route('/logout')
def logout():
    session.pop('name',None)
    session.pop('id',None)
    session.pop('role',None)
    return redirect(url_for('index') )