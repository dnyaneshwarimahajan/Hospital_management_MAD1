from flask_sqlalchemy import SQLAlchemy
from flask import Flask, Blueprint,render_template, request, redirect, url_for, session, flash
from datetime import datetime,date, timedelta 
from models import User, Dept, Appointments, db, Treatments,DoctorAvailability
from sqlalchemy.orm import aliased


doctor_routes = Blueprint('doctor', __name__)



@doctor_routes.route('/dashboard')
def doctor_dashboard():

    doctor_id = session['id']
    doctor = User.query.get_or_404(doctor_id)

    # To get upcommeng appt query
    upcoming =(
        db.session.query(
            Appointments.id.label('id'),Appointments.date.label('date'),Appointments.time.label('time'),  User.user_id.label('patient_id'),
            User.username.label('patient_name'), Appointments.treatment_id.label('treatment_id')
        ).join(User , User.user_id ==Appointments.user_id).filter( Appointments.doctor_id ==doctor_id , Appointments.status =='booked').order_by( Appointments.date.asc(), Appointments.time.asc() ).all()
        )
    # assigned patients
    assigned = (User.query.filter_by(role='patient').join(Appointments ,Appointments.user_id ==User.user_id ).filter(Appointments. doctor_id == doctor_id).group_by( User.user_id).all())

    return render_template('doc_dash.html', doctor=doctor, upcoming_appointments=upcoming,assigned_patients=assigned)



# Update appointment with treatment detai
@doctor_routes.route('/appointment/<int:appt_id>/update', methods=['GET','POST'])
def update_appointment(appt_id):

    appt1 = Appointments.query.get_or_404(appt_id)

    if( request.method == 'GET'):
        patient = User.query.get(appt1.user_id)
        return render_template('update_appointment.html', appt=appt1, patient=patient)

    diagnosis =request.form.get('diagnosis','').strip()
    prescription = request.form.get('prescription','').strip()    
    treatment= request.form.get('treatment','').strip()


    if (diagnosis== '' or diagnosis == None):
        flash("Please provide diagnosis. ", "warning")
        return redirect(url_for('doctor.update_appointment', appt_id=appt_id))

    new_t = Treatments(dignosis=diagnosis, prescription=prescription, treatment=treatment)
    db.session.add(new_t)
    db.session.commit()

    # link treatment to appointment
    appt1.treatment_id = new_t.id
    db.session.commit()
    flash("Patient history updated. ", "success")
    return redirect(url_for('doctor.doctor_dashboard'))





# Complete appointment

@doctor_routes.route('/complete_appointment/<int:appt_id>', methods=['POST'])
def complete_appointment(appt_id):
    doctor_id =session['id']
    appt = Appointments.query.filter_by(id=appt_id, doctor_id=doctor_id).first()

    if (appt == None):
        flash("Appointment not found.", "warning")
        return redirect(url_for('doctor.doctor_dashboard'))
    
    # Mark appoimntment completed here 
    appt.status = 'completed'

    db.session.commit()

    flash("Appointment marked complete.", "success")
    return redirect(url_for('doctor.doctor_dashboard'))

@doctor_routes.route('/cancel_appointment/<int:appt_id>', methods=['POST'])
def cancel_appointment(appt_id):

    doctor_id = session['id'] 
    appt = Appointments.query.filter_by(id=appt_id, doctor_id=doctor_id, status="booked").first()

    if (appt == None):
        flash("Appointment not found or you don't have permission to cancel it.", "warning")
        return redirect(url_for('doctor.doctor_dashboard'))

    # mark cancelled
    appt.status = "cancelled"
    db.session.commit()

    flash("Appointment cancelled successfully.", "success")
    return redirect(url_for('doctor.doctor_dashboard'))




# Here Availability of Doctor will be set
@doctor_routes.route('/availability', methods=['GET','POST'])
def set_availability():
    today = date.today()
    # Get Next 7 days
    next7 = []
    for i in range(7):
        next7.append( (today + timedelta(days=i)).isoformat())

    doctor_id = session['id']
    if( request.method == 'POST'):
        selected = request.form.getlist('selected')  # "YYYY-MM-DD|slot1"

        sel_map = {}
        for s in selected:
            if '|' not in s: continue
            d, slot = s.split('|',1)
            sel_map.setdefault(d, set()).add(slot)

        for d in next7:
            row = DoctorAvailability.query.filter_by(doctor_id=doctor_id, date=d).first()

            if( not row):
                if (d not in sel_map) : 
                    continue
                row = DoctorAvailability( doctor_id=doctor_id,date=d)
                db.session.add(row)

            
            slot_here = sel_map.get(d, set())
            

            if ( "slot1" in slot_here): 
                row.slot_1 = not row.slot_1
            
            if( "slot2" in slot_here):
                row.slot_2 = not row.slot_2
            # row.slot_1 = 'slot1' in sel_map.get(d, set())
            
         
        db.session.commit()
        flash("Availability saved.", "success")
        return redirect(url_for('doctor.set_availability', doctor_id=doctor_id))

    # GET: prepare grid
    rows = DoctorAvailability.query.filter(  DoctorAvailability.doctor_id==doctor_id, DoctorAvailability.date.in_(next7) ).all()
    row_map = {r.date: r for r in rows}
    grid = []
    grid2 =[]
    
    # hERE IS THE pROBLEM
    for d in next7:
        r = row_map.get(d)
        grid.append({'date': d, 'slot1':r.slot_1 if r else False, 'slot2': r.slot_2 if r else False})
    doctor = User.query.get_or_404(doctor_id)

    return render_template('availability.html', doctor=doctor, grid=grid)


# Doctor Profile View
@doctor_routes.route("/doctor_profile/<int:doctor_id>")
def view_doctor(doctor_id):

    doctor = User.query.filter_by(user_id=doctor_id, role='doctor').first()


    return render_template(
        "doctor_profile.html", doctor=doctor,
    )




# History For Doctor and Patient

@doctor_routes.route('/doctor/history')
def doctor_history():
    if session.get('role') != 'doctor':
        return redirect(url_for('login'))

    doctor_id = session['id']
    patient = User.query.get_or_404(doctor_id)
    

    history_rows = (
        db.session.query(Appointments.id.label("appt_id"),Appointments.date, Appointments.time,Appointments.status, Treatments.dignosis, Treatments.treatment, Treatments.prescription,    User.username.label("patient_name"),   Dept.dept_name.label("department_name"))
        .outerjoin(Treatments, Treatments.id == Appointments.treatment_id).join(User, User.user_id == Appointments.user_id).outerjoin(Dept, Dept.id == User.department_id).filter(Appointments.doctor_id == doctor_id).order_by(Appointments.id.asc()).all())


    return render_template("history.html", patient=patient, history=history_rows)



