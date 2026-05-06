from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='patient')  # 'patient' or 'asha'
    village = db.Column(db.String(100))
    district = db.Column(db.String(100))
    state = db.Column(db.String(100), default='Uttar Pradesh')
    phone = db.Column(db.String(15))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active_user = db.Column(db.Boolean, default=True)

    # Relationships
    predictions = db.relationship('Prediction', backref='user', lazy='dynamic')
    simulations = db.relationship('SimulationRun', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'


class Prediction(db.Model):
    __tablename__ = 'predictions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Patient Demographics (for ASHA workers)
    patient_name = db.Column(db.String(100))
    patient_aadhaar = db.Column(db.String(12))
    
    # Input features
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    hypertension = db.Column(db.Integer, default=0)
    heart_disease = db.Column(db.Integer, default=0)
    ever_married = db.Column(db.String(5))
    avg_glucose_level = db.Column(db.Float, default=100.0)
    bmi = db.Column(db.Float, default=22.0)
    smoking_status = db.Column(db.String(30))
    symptoms_json = db.Column(db.Text)  # JSON of symptom checkboxes
    duration_hours = db.Column(db.Integer, default=0)
    
    # Output
    disease = db.Column(db.String(50))
    risk_level = db.Column(db.String(20))  # Low / Medium / High
    probability = db.Column(db.Float)
    recommendation = db.Column(db.String(100))
    model_latency_ms = db.Column(db.Float)
    bandwidth_simulated = db.Column(db.String(20))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Prediction {self.disease} {self.risk_level}>'


class SimulationRun(db.Model):
    __tablename__ = 'simulation_runs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Simulation parameters
    bandwidth = db.Column(db.String(20))
    model_size = db.Column(db.String(20))
    noise_level = db.Column(db.Float, default=0.0)
    missing_data_pct = db.Column(db.Float, default=0.0)
    num_patients = db.Column(db.Integer, default=50)
    
    # Results (JSON)
    results_json = db.Column(db.Text)
    
    # Summary metrics
    detection_rate = db.Column(db.Float)
    avg_time_to_care = db.Column(db.Float)
    accuracy = db.Column(db.Float)
    avg_latency_ms = db.Column(db.Float)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def seed_defaults():
    """Seed default ASHA and patient demo accounts."""
    if User.query.count() == 0:
        # Demo ASHA worker
        asha = User(
            name='Sunita Devi',
            email='asha@demo.com',
            role='asha',
            village='Rampur',
            district='Varanasi',
            state='Uttar Pradesh',
            phone='9876543210'
        )
        asha.set_password('asha1234')

        # Demo Patient
        patient = User(
            name='Rajesh Kumar',
            email='patient@demo.com',
            role='patient',
            village='Sitapur',
            district='Lucknow',
            state='Uttar Pradesh',
            phone='9123456789'
        )
        patient.set_password('patient1234')

        db.session.add_all([asha, patient])
        db.session.commit()
