from flask_sqlalchemy import SQLAlchemy
from flask import Blueprint,render_template, request, redirect, url_for, session, flash
from datetime import date, timedelta 
from models import User, Dept, Appointments, db, Treatments,DoctorAvailability




patient_routes = Blueprint('patient', __name__)

@patient_routes.route("/dashboard")
def patient_dashboard():
    patient_id = session['id']

    departments = Dept.query.order_by(Dept.dept_name).all()

    appointments = (
        db.session.query(Appointments.id, Appointments.date, Appointments.time, User.username.label("doctor_name"),Dept.dept_name.label("department")
        ).join(User, User.user_id == Appointments.doctor_id).join(Dept, Dept.id == User.department_id, isouter=True)
        .filter(Appointments.user_id == patient_id).filter(Appointments.status == "booked").order_by(Appointments.date.asc(), Appointments.time.asc()).all()
    )
    return render_template("patient_dash.html",departments=departments,appointments=appointments)

#This is history for patients only
@patient_routes.route('/history')
def patient_history():
    if session.get('role') != 'patient':
        return redirect(url_for('login'))
    

    patient_id = session['id']
    patient = User.query.get_or_404(patient_id)
    
    history_rows = (
        db.session.query(Appointments.id.label("appt_id"),  Appointments.date, Appointments.time,Appointments.status,Treatments.dignosis,Treatments.treatment,Treatments.prescription,User.username.label("doctor_name"), Dept.dept_name.label("department_name"),Appointments.user_id.label('patient_id') )
        .outerjoin(Treatments, Treatments.id == Appointments.treatment_id).join(User, User.user_id == Appointments.doctor_id)                      
        .outerjoin(Dept, Dept.id == User.department_id).filter(Appointments.user_id == patient_id).order_by(Appointments.id.asc()).all()
    )

    print(history_rows)

    return render_template("history.html", patient=patient, history=history_rows)



# Patient Booking Chart Here
@patient_routes.route('/booking_chart/<int:doctor_id>')
def patient_booking_chart(doctor_id):
    if session.get('role') != 'patient':
        return redirect(url_for('auth.login'))

    patient_id = session['id']
    doctor = User.query.filter_by(user_id=doctor_id, role='doctor').first()
    dept_redirect = url_for('department_detail', dept_id=doctor.department_id)

    today = date.today()

    next7 = []

    # All next 7 days date list 
    for i in range(7): 
        next7.append( (today + timedelta(days=i)).isoformat())

    # availability grid
    rows = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == doctor_id,
        DoctorAvailability.date.in_(next7)
    ).all()
    row_map = {r.date: r for r in rows}

    grid = []
    for d in next7:
        r = row_map.get(d)
        grid.append({
            'date': d,
            'slot1': bool(r and r.slot_1),
            'slot2': bool(r and r.slot_2)
        })

    booked = set()
    appts = Appointments.query.filter(Appointments.doctor_id == doctor_id,  Appointments.status == 'booked',Appointments.date.in_(next7)).all()


    for a in appts:
        booked.add((a.date, a.time))   # time stores 'slot1' or 'slot2'

    patient_has_booking = bool(Appointments.query.filter_by(user_id=patient_id, status='booked').first())

    SLOT_LABELS = {
        'slot1': "08:00 - 12:00 am",
        'slot2': "04:00 - 9:00 pm"
    }

    return render_template(
        "slot_booking_chart.html",doctor=doctor, grid=grid,booked=booked,slot_labels=SLOT_LABELS,dept_redirect=dept_redirect, patient_has_booking=patient_has_booking
    )



# Patient book shlot 
@patient_routes.route('/book_slot', methods=['POST'])
def patient_book_slot():
    patient_id = session.get('id')
    doctor_id = request.form.get('doctor_id')
    date = request.form.get('date')
    slot = request.form.get('slot')

    # To redirect to patient_dash or doct dash
    def redirect_page(did):
        if not did:
            return redirect(url_for('patient_dash'))
        doc = User.query.filter_by(user_id=did, role='doctor').first()
        if ( doc !=None and doc.department_id!= None):
            return redirect(url_for('department_detail', dept_id=doc.department_id) )
        else:
            return redirect(url_for('patient_dash') )
        



    if (not doctor_id or not date or slot not in ("slot1", "slot2") ):
        if (doctor_id != None ):
            return redirect(url_for('patient.patient_booking_chart', doctor_id=doctor_id))

        else:
            return redirect(url_for('patient_dash'))


    # THis is block 2 or more booking of petient
    appt_booked =  Appointments.query.filter_by(user_id=patient_id, status="booked").first()
    if (appt_booked !=None):
        return redirect_page(doctor_id)

    # check slot availabitilh
    is_available = Appointments.query.filter_by(doctor_id=doctor_id, date=date, time=slot, status="booked").first()
    if (is_available != None ):
        flash(" Sorry that slot was already booked.", "warning")
        return redirect_page(doctor_id)

    # create appointment
    appt = Appointments(user_id=patient_id, doctor_id=doctor_id, date=date, time=slot, status="booked")
    db.session.add(appt)
    db.session.commit()

    flash("Appointment booked successfully.", "success")
    return redirect(url_for('patient.patient_dashboard'))


# Canclel Appointment Here

@patient_routes.route('/cancel_appointment/<int:appt_id>', methods=['POST'])
def cancel_appointment(appt_id):
    patient_id = session['id']

    appointment = Appointments.query.filter_by(id=appt_id, user_id=patient_id, status="booked").first()

    if (appointment == None):
        return redirect(url_for('patient.patient_dashboard'))

    doctor = User.query.get(appointment.doctor_id)
    if doctor and doctor.department_id:
        dept_id = doctor.department_id
    else:
        dept_id = None
    appointment.status = "cancelled"
    db.session.commit()

    return redirect(url_for('patient.patient_dashboard', dept_id=dept_id))


# patient Edit Profile Here
@patient_routes.route('/edit_profile', methods=['GET'])
def edit_profile():
    uid = session['id']
    if not uid:
        return redirect(url_for('auth.login'))
    return redirect(url_for('admin.edit_patient', user_id=uid))
