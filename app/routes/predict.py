import json
import csv
from io import StringIO
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, Response
from flask_login import login_required, current_user
from app import db
from app.models import Prediction
from app.ml.engine import predict, rule_based_predict, get_metrics, DISEASE_CONFIGS

predict_bp = Blueprint('predict', __name__, url_prefix='/predict')

# ─── Symptom definitions per disease ─────────────────────────────────────────
SYMPTOM_LABELS = {
    'stroke': [
        ('slurred_speech',      'Slurred / Difficult Speech'),
        ('weakness',            'Sudden Arm/Leg Weakness'),
        ('vision_issues',       'Vision Problems'),
        ('hypertension',        'High Blood Pressure (known)'),
        ('heart_disease',       'Heart Disease (known)'),
        ('ever_married',        'Married'),
    ],
    'epilepsy': [
        ('seizure_history',         'History of Seizures'),
        ('loss_of_consciousness',   'Loss of Consciousness'),
        ('jerking_movements',       'Jerking / Convulsive Movements'),
        ('aura',                    'Aura / Warning Before Episode'),
        ('postictal_confusion',     'Confusion After Episode'),
        ('family_history',          'Family History of Epilepsy'),
    ],
    'meningitis': [
        ('fever',               'High Fever'),
        ('headache',            'Severe Headache'),
        ('neck_stiffness',      'Neck Stiffness'),
        ('photophobia',         'Sensitivity to Light'),
        ('vomiting',            'Vomiting / Nausea'),
        ('rash',                'Skin Rash'),
        ('altered_consciousness','Altered Consciousness'),
        ('kernig_sign',         'Kernig\'s Sign (leg pain on extension)'),
    ],
    'encephalitis': [
        ('fever',               'High Fever'),
        ('headache',            'Severe Headache'),
        ('seizures',            'Seizures'),
        ('altered_consciousness','Altered Consciousness'),
        ('neck_stiffness',      'Neck Stiffness'),
        ('vomiting',            'Vomiting'),
        ('photophobia',         'Sensitivity to Light'),
        ('confusion',           'Confusion / Disorientation'),
    ]
}


@predict_bp.route('/', methods=['GET'])
@login_required
def checker():
    return render_template('predict/checker.html', symptom_labels=SYMPTOM_LABELS)


@predict_bp.route('/run', methods=['POST'])
@login_required
def run_prediction():
    try:
        # Common fields
        age    = int(request.form.get('age', 30))
        gender = 1 if request.form.get('gender') == 'Male' else 0
        ever_married = 1 if request.form.get('ever_married') == 'Yes' else 0
        hypertension = 1 if 'hypertension' in request.form else 0
        heart_disease = 1 if 'heart_disease' in request.form else 0
        avg_glucose_level = float(request.form.get('avg_glucose_level', 100))
        bmi = float(request.form.get('bmi', 22))
        smoking_status = int(request.form.get('smoking_status', 0))
        duration_hours = int(request.form.get('duration_hours', 0))
        bandwidth = request.form.get('bandwidth', '50kbps')
        
        patient_name = request.form.get('patient_name')
        patient_aadhaar = request.form.get('patient_aadhaar')

        # Determine disease (form has disease selector)
        disease = request.form.get('disease', 'stroke')

        # Collect symptom checkboxes
        symptoms_raw = {}
        labels = SYMPTOM_LABELS.get(disease, [])
        for key, _ in labels:
            symptoms_raw[key] = 1 if key in request.form else 0

        # Build full input dict
        input_dict = {
            'age': age, 'gender': gender,
            'ever_married': ever_married,
            'hypertension': hypertension,
            'heart_disease': heart_disease,
            'avg_glucose_level': avg_glucose_level,
            'bmi': bmi,
            'smoking_status': smoking_status,
            'duration_hours': duration_hours,
            'duration_minutes': duration_hours * 60,
            'duration_days': max(1, duration_hours // 24),
            'temperature': float(request.form.get('temperature', 37.5)),
            **symptoms_raw
        }

        result = predict(disease, input_dict)

        # Persist to DB
        pred_record = Prediction(
            user_id=current_user.id,
            age=age, gender='Male' if gender else 'Female',
            hypertension=hypertension, heart_disease=heart_disease,
            ever_married='Yes' if ever_married else 'No',
            avg_glucose_level=avg_glucose_level, bmi=bmi,
            smoking_status=str(smoking_status),
            symptoms_json=json.dumps(symptoms_raw),
            duration_hours=duration_hours,
            disease=result['disease'],
            risk_level=result['risk_level'],
            probability=result['probability'],
            recommendation=result['recommendation'],
            model_latency_ms=result['latency_ms'],
            bandwidth_simulated=bandwidth,
            patient_name=patient_name,
            patient_aadhaar=patient_aadhaar
        )
        db.session.add(pred_record)
        db.session.commit()

        return render_template('predict/result.html',
                               result=result,
                               input_data=input_dict,
                               symptoms=symptoms_raw,
                               symptom_labels=dict(labels),
                               disease=disease)

    except Exception as e:
        flash(f'Prediction error: {str(e)}. Using rule-based fallback.', 'warning')
        fallback = rule_based_predict(input_dict if 'input_dict' in locals() else {})
        
        # Save fallback to DB
        try:
            pred_record = Prediction(
                user_id=current_user.id,
                age=input_dict.get('age', 0) if 'input_dict' in locals() else 0,
                gender='Male' if ('input_dict' in locals() and input_dict.get('gender') == 1) else 'Female',
                disease=fallback['disease'],
                risk_level=fallback['risk_level'],
                probability=fallback['probability'],
                recommendation=fallback['recommendation'],
                model_latency_ms=fallback['latency_ms'],
                bandwidth_simulated=request.form.get('bandwidth', '50kbps'),
                patient_name=request.form.get('patient_name'),
                patient_aadhaar=request.form.get('patient_aadhaar')
            )
            db.session.add(pred_record)
            db.session.commit()
        except Exception as db_err:
            print("DB Save Error in Fallback:", db_err)

        return render_template('predict/result.html', result=fallback,
                               input_data={}, symptoms={}, symptom_labels={},
                               disease=fallback['disease'])


@predict_bp.route('/history')
@login_required
def history():
    preds = Prediction.query.filter_by(user_id=current_user.id)\
                            .order_by(Prediction.created_at.desc()).limit(50).all()
    return render_template('predict/history.html', predictions=preds)


@predict_bp.route('/api/history/<aadhaar>', methods=['GET'])
@login_required
def get_patient_history(aadhaar):
    preds = Prediction.query.filter_by(patient_aadhaar=aadhaar, user_id=current_user.id).order_by(Prediction.created_at.desc()).all()
    if not preds:
        return jsonify({'found': False})
    
    data = []
    for p in preds:
        data.append({
            'disease': p.disease,
            'date': p.created_at.strftime('%Y-%m-%d'),
            'risk': p.risk_level
        })
    return jsonify({'found': True, 'predictions': data})


@predict_bp.route('/export/<aadhaar>', methods=['GET'])
@login_required
def export_patient_history(aadhaar):
    preds = Prediction.query.filter_by(patient_aadhaar=aadhaar, user_id=current_user.id).order_by(Prediction.created_at.desc()).all()
    
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Date', 'Patient Name', 'Aadhaar', 'Predicted Disease', 'Risk Level', 'Recommendation', 'Model Latency (ms)'])
    for p in preds:
        # Prevent Excel from turning 12 digit Aadhaar into scientific notation
        safe_aadhaar = f'="{p.patient_aadhaar}"' if p.patient_aadhaar else ''
        cw.writerow([
            p.created_at.strftime('%Y-%m-%d %H:%M'),
            p.patient_name or 'N/A',
            safe_aadhaar,
            p.disease,
            p.risk_level,
            p.recommendation,
            p.model_latency_ms
        ])
    
    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=patient_history_{aadhaar}.csv"}
    )

@predict_bp.route('/export_all', methods=['GET'])
@login_required
def export_all_history():
    preds = Prediction.query.filter_by(user_id=current_user.id).order_by(Prediction.created_at.desc()).all()
    
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Date', 'Patient Name', 'Aadhaar', 'Predicted Disease', 'Risk Level', 'Recommendation', 'Model Latency (ms)'])
    for p in preds:
        safe_aadhaar = f'="{p.patient_aadhaar}"' if p.patient_aadhaar else ''
        cw.writerow([
            p.created_at.strftime('%Y-%m-%d %H:%M'),
            p.patient_name or 'N/A',
            safe_aadhaar,
            p.disease,
            p.risk_level,
            p.recommendation,
            p.model_latency_ms
        ])
    
    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=all_patients_history.csv"}
    )


@predict_bp.route('/api/predict', methods=['POST'])
@login_required
def api_predict():
    """JSON API endpoint for lightweight frontend use."""
    data = request.get_json(force=True)
    disease = data.pop('disease', 'stroke')
    try:
        result = predict(disease, data)
    except Exception:
        result = rule_based_predict(data)
    return jsonify(result)
