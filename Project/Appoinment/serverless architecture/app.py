from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'
app.config['SECRET_KEY'] = 'your_secret_key'

# Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'daminmain@gmail.com'  # Change to your email
app.config['MAIL_PASSWORD'] = 'kpqtxqskedcykwjz'   # Use an App Password
app.config['MAIL_DEFAULT_SENDER'] = 'your_email@gmail.com'

db = SQLAlchemy(app)
mail = Mail(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Database Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    age = db.Column(db.Integer)
    location = db.Column(db.String(100))

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    problem = db.Column(db.String(200))
    location = db.Column(db.String(100))
    history = db.Column(db.String(200))
    doctor_assigned = db.Column(db.String(100), default="Not Assigned")
    status = db.Column(db.String(50), default="Pending")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home Page
@app.route('/')
def index():
    return render_template('index.html')

# User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        age = request.form['age']
        location = request.form['location']
        
        user = User(name=name, email=email, password=password, age=age, location=location)
        db.session.add(user)
        db.session.commit()
        flash('Registration Successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    
    return render_template('login.html')

# User Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    appointments = Appointment.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', appointments=appointments)

# Book Appointment
@app.route('/book', methods=['GET', 'POST'])
@login_required
def book():
    if request.method == "POST":
        name = request.form['name']
        age = request.form['age']
        problem = request.form['problem']
        location = request.form['location']
        history = request.form['history']
        
        appointment = Appointment(user_id=current_user.id, name=name, age=age, problem=problem, location=location, history=history)
        db.session.add(appointment)
        db.session.commit()
        
        flash('Appointment booked successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('book.html')

# Admin Login
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        
        if username == "admin" and password == "admin123":
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid Admin Credentials', 'danger')
    
    return render_template('admin.html')

# Admin Dashboard
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin'))
    
    appointments = Appointment.query.all()
    return render_template('admin_dashboard.html', appointments=appointments)

# Assign Doctor
@app.route('/assign_doctor/<int:appointment_id>', methods=['POST'])
def assign_doctor(appointment_id):
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin'))

    doctor_name = request.form['doctor_name']
    appointment = Appointment.query.get(appointment_id)
    appointment.doctor_assigned = doctor_name
    appointment.status = "Scheduled"
    db.session.commit()
    
    # Send Email Confirmation
    user = User.query.get(appointment.user_id)
    msg = Message("Appointment Scheduled", recipients=[user.email])
    msg.body = f"Dear {user.name}, your appointment for {appointment.problem} has been scheduled with Dr. {doctor_name}."
    mail.send(msg)
    
    flash('Doctor Assigned and Email Sent!', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for('index'))

@app.route('/reschedule/<int:appointment_id>', methods=['POST'])
@login_required
def reschedule(appointment_id):
    new_date = request.form['new_date']
    appointment = Appointment.query.get(appointment_id)
    appointment.date = new_date
    db.session.commit()
    flash("Appointment rescheduled!", "success")
    return redirect(url_for('dashboard'))

@app.route('/cancel/<int:appointment_id>', methods=['POST'])
@login_required
def cancel(appointment_id):
    appointment = Appointment.query.get(appointment_id)
    db.session.delete(appointment)
    db.session.commit()
    flash("Appointment canceled!", "danger")
    return redirect(url_for('dashboard'))


from flask import send_file
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from datetime import datetime

@app.route('/generate_pdf/<int:appointment_id>')
def generate_pdf(appointment_id):
    appointment = Appointment.query.get(appointment_id)
    buffer = BytesIO()
    
    # Create the PDF document
    pdf = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    
    try:
        img = Image( width=100, height=100)
        elements.append(img)
    except:
        pass

    # Title and Hospital Info
    styles = getSampleStyleSheet()
    title = Paragraph("<b>XYZ Hospital</b>", styles['Title'])
    subtitle = Paragraph("<i>123 Health Street, City, Country | Contact: +123456789</i>", styles['Normal'])
    
    elements.append(title)
    elements.append(subtitle)
    elements.append(Spacer(1, 10))

    # Appointment Info
    appointment_info = [
        ["Patient Name:", appointment.name],
        ["Age:", appointment.age],
        ["Location:", appointment.location],
        ["Problem:", appointment.problem],
        ["Medical History:", appointment.history],
        ["Doctor Assigned:", appointment.doctor_assigned],
        ["Appointment Date:", datetime.now().strftime("%d-%m-%Y")],
    ]

    table = Table(appointment_info, colWidths=[150, 300])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))

    # Prescription Section
    elements.append(Paragraph("<b>Prescription & Notes:</b>", styles['Heading2']))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("● Take prescribed medication on time.", styles['Normal']))
    elements.append(Paragraph("● Follow up in 7 days if symptoms persist.", styles['Normal']))
    elements.append(Paragraph("● Maintain a healthy diet and drink plenty of water.", styles['Normal']))
    elements.append(Spacer(1, 20))

    # Doctor Signature
    elements.append(Paragraph("<b>Doctor's Signature:</b>", styles['Normal']))
    elements.append(Spacer(1, 30))

    # Footer
    footer = Paragraph("<i>Thank you for choosing XYZ Hospital. Wishing you a speedy recovery!</i>", styles['Normal'])
    elements.append(footer)

    # Build PDF
    pdf.build(elements)
    buffer.seek(0)
    
    return send_file(buffer, as_attachment=True, download_name=f"Prescription_{appointment.id}.pdf")



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
