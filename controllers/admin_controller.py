from flask_sqlalchemy import SQLAlchemy
from flask import Flask, Blueprint,render_template, request, redirect, url_for, session, flash
from datetime import datetime,date, timedelta 
from models import User, Dept, Appointments, db, Treatments,DoctorAvailability
from sqlalchemy.orm import aliased



admin_routes = Blueprint('admin', __name__)


# Dashboard Loard
@admin_routes.route('/dashboard',methods = ["POST","GET"])
def admin_dashboard():
    q = request.args.get("q", "").strip() 

    # doctors and patients data get spereated hers
    doctors_q = User.query.filter_by(role="doctor")
    patients_q =  User.query.filter_by(role="patient")

    if  q:
        like = f"%{q}%"
        doctors_q = doctors_q.filter((User.username.ilike(like)) | (User.email_id.ilike(like)))
        patients_q = patients_q.filter((User.username.ilike(like)) | (User.email_id.ilike(like)))

    doctors = doctors_q.order_by(User.username).all()
    patients = patients_q.order_by(User.username).all()

    # create aapointment slot list here 
    appointments =  []

    Patient = aliased(User)
    Doctor  = aliased(User)

    appt_rows = (
        db.session.query(Appointments.id.label("id"),Appointments.date.label("date"), Appointments.time.label("time"), Patient.user_id.label("patient_id"),Patient.username.label("patient_name"),
            Patient.department_id.label("patient_dept_id"),Appointments.doctor_id.label("doctor_id"), Doctor.username.label("doctor_name"),Doctor.department_id.label("docotor_dept_id"),
            Dept.dept_name.label("doctor_dept")
        ).join(Patient, Patient.user_id == Appointments.user_id).join(Doctor, Doctor.user_id == Appointments.doctor_id)             
        .join(Dept, Dept.id == Doctor.department_id, isouter=True).filter(Appointments.status == "booked").order_by(Appointments.date.asc(), Appointments.time.asc()).limit(10).all())

    dept_map ={}
    dept_rows =   Dept.query.all()
    for d in dept_rows:
        dept_map[d.id] =d.dept_name

    # Here appionments solt is added 
    for r in appt_rows:
        appointments.append({"id": r.id,"date": r.date,"time": r.time,"patient_name": r.patient_name,"doctor_name": r.doctor_name,"department": dept_map.get(r.docotor_dept_id, "-"),"patient_id": r.patient_id})

    return render_template("admin_dash.html", q=q,doctors=doctors,patients=patients,  appointments=appointments )





# Edit Doctor
@admin_routes.route('/create_doctor', methods=["GET", "POST"])
def create_doctor():
    

    if request.method == "POST":
        name = request.form['username']
        email_id = request.form['email_id']
        password = request.form['password']
        selected_dept = request.form.get('department_id')
        new_dept_name = request.form.get('new_department', '').strip()
        new_dept_description = request.form.get('new_department_description', '').strip()

        if new_dept_name:
            print(new_dept_name) 
            
            is_exist = Dept.query.filter_by(dept_name=new_dept_name).first()
            if is_exist:
                department_id = is_exist.id
            else:
                new_dept = Dept(dept_name=new_dept_name, description=new_dept_description)
                db.session.add(new_dept)
                db.session.commit()
                department_id = new_dept.id
        else:
            department_id = int(selected_dept) if selected_dept else None

        existing_doctor = User.query.filter_by(email_id=email_id, username=name).first()
        if existing_doctor:
            flash("Doctor ALerady Exists", "warning")
            return redirect(url_for('admin.admin_dashboard'))

        # New Doctor creaded here
        new_doc = User(username=name,
                        email_id=email_id,password=password,  
                        role="doctor",department_id=department_id )
        db.session.add(new_doc)
        db.session.commit()
        return redirect(url_for('admin.admin_dashboard'))



    departments = Dept.query.order_by(Dept.dept_name).all()
    return render_template("create_doctor.html", departments=departments)


# Delete User By User Id

@admin_routes.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    user = User.query.get(user_id)

    if user.role == "doctor":
        Appointments.query.filter_by(doctor_id=user.user_id, status='booked').update({'status': 'cancelled'}, synchronize_session=False)
        DoctorAvailability.query.filter_by(doctor_id=user.user_id).delete(synchronize_session=False)

    if user.role == "patient":
        Appointments.query.filter_by(user_id=user.user_id, status='booked').update({'status': 'cancelled'}, synchronize_session=False)

    db.session.delete(user)
    db.session.commit()
    flash("User Deleted Successfully", "success")
    return redirect(url_for('admin.admin_dashboard'))


@admin_routes.route('/edit_patient/<int:user_id>', methods=["GET", "POST"])
def edit_patient(user_id):
    user = User.query.get(user_id)
    if request.method == "POST":
        name = request.form["username"].strip()
        email_id = request.form["email_id"].strip()
        contact_no = request.form["contact_no"].strip()
        password = request.form["password"].strip()

        
        # Check duplicate email (except current user)
        if email_id != user.email_id and User.query.filter_by(email_id=email_id).first():
            flash("Email is already used by another user","warning")
            return redirect(url_for("admin.edit_patient", user_id=user_id))

        # Update fields
        user.username = name
        user.email_id = email_id
        user.contact_no = contact_no

        if password:   # update only if user typed it
            user.password = password

        db.session.commit()
        if session.get("role") == "admin":
            return redirect(url_for("admin.admin_dashboard"))
        else:
            return redirect(url_for("patient.patient_dashboard"))
    
    return render_template("edit_patient.html", user=user)




# Edit Doctor 
@admin_routes.route('/edit_doctor/<int:user_id>', methods=["GET", "POST"])
def edit_doctor(user_id):
    user = User.query.get(user_id)

    if not user:
        flash("Doctor not found", "danger")
        return redirect(url_for('admin.admin_dashboard'))

    if request.method == "POST":
        name = request.form["username"].strip()
        email_id = request.form["email_id"].strip()
        password = request.form["password"].strip()
        department_id = request.form["department"].strip()
        qualifications = request.form["qualifications"].strip()
        contact_no = request.form["contact_no"].strip()
        years_experience = request.form["years_experience"].strip()

        new_dept_name = request.form.get('new_department', '').strip()

        if (new_dept_name != None):  
            # check if dept already exists
            existing_dept = Dept.query.filter_by(dept_name=new_dept_name).first()
            if (existing_dept !=None):
                department_id = existing_dept.id
            else:
                new_dept =  Dept(dept_name= new_dept_name, description= "")
                db.session.add( new_dept)
                db.session.commit()
                department_id =  new_dept.id
        dept = Dept.query.filter_by( id=department_id).first()

        # Check duplicate email
        if email_id != user.email_id and User.query.filter_by( email_id =email_id).first():
            flash("Email Already Exists", "warning")
            return redirect(url_for("admin.edit_doctor", user_id=  user_id))

        user.username = name
        user.email_id = email_id
        user.department =  dept
        user.qualifications =qualifications
        user.years_experience = years_experience
        user.contact_no = contact_no

        if password:  
            user.password =password

        db.session.commit()
        return redirect( url_for("admin.admin_dashboard") )
    


    departments = Dept.query.order_by(Dept.dept_name).all()
    return render_template( "edit_doctor.html", user=user, departments=departments)  




@admin_routes.route('/blacklist/<int:user_id>', methods=[ 'POST'])
def blacklist(user_id):

    user = User.query.get(user_id)
    if (user == None ):
        return redirect(url_for('admin.admin_dashboard'))

    user.blacklist = not user.blacklist
    db.session.commit()
    return redirect( url_for('admin.admin_dashboard'))


# Admin Historyy 

@admin_routes.route('/history/')
def admin_history():
    if( session.get('role') != 'admin'):
        return redirect(url_for('auth.login'))
    

    Doctor  = aliased(User)
    admin_id = session['id']
    patient = User.query.get_or_404(admin_id)


    history_rows = (
        db.session.query(
            Appointments.id.label("appt_id"),Appointments.date,Appointments.time,  Appointments.status,Treatments.dignosis,Treatments.treatment,Treatments.prescription, User.username.label("patient_name"),Dept.dept_name.label("department_name"), Doctor.username.label("doctor_name")).outerjoin(Treatments, Treatments.id == Appointments.treatment_id).join(User, User.user_id == Appointments.user_id).join(Doctor, Doctor.user_id == Appointments.doctor_id).outerjoin(Dept, Dept.id == Doctor.department_id).order_by(Appointments.id.asc()).all()
            )

    # print(history_rows)
    return render_template("history.html", patient=patient, history=history_rows)

