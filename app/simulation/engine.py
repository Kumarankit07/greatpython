"""
Discrete-Event Simulation Engine
Simulates the ASHA → PHC → Referral healthcare journey under
various bandwidth, noise, and missing-data constraints.
"""
import time
import random
import json
import numpy as np
from app.ml.engine import predict, rule_based_predict, DISEASE_CONFIGS

# ─── Bandwidth latency model (ms overhead per prediction) ────────────────────
BANDWIDTH_LATENCY = {
    'offline':  0,      # cached — no network
    '10kbps':   4500,   # very slow rural link
    '50kbps':   800,
    '100kbps':  300,
    '1mbps':    50
}

MODEL_SIZE_OVERHEAD = {   # extra ms per inference for larger models
    'small':    0,
    'medium':   15,
    'large':    60
}

DISEASES = ['stroke', 'epilepsy', 'meningitis', 'encephalitis']


# ─── Synthetic patient generator ─────────────────────────────────────────────

def _random_patient(disease, noise_level=0.0, missing_pct=0.0):
    age    = int(np.random.randint(10, 80))
    gender = int(np.random.choice([0, 1]))
    cfg    = DISEASE_CONFIGS[disease]
    features = cfg['features']

    # Base symptom likelihood depends on disease
    SYMPTOM_PRIORS = {
        'stroke':       {'slurred_speech':0.6,'weakness':0.7,'vision_issues':0.5,
                         'hypertension':0.5,'heart_disease':0.3,'ever_married':0.6,
                         'avg_glucose_level':140,'bmi':27,'smoking_status':1},
        'epilepsy':     {'seizure_history':0.7,'loss_of_consciousness':0.6,
                         'jerking_movements':0.65,'aura':0.45,'postictal_confusion':0.5,
                         'family_history':0.3,'eeg_abnormal':0.6,'duration_minutes':8},
        'meningitis':   {'fever':0.85,'headache':0.8,'neck_stiffness':0.7,
                         'photophobia':0.6,'vomiting':0.65,'rash':0.35,
                         'altered_consciousness':0.45,'kernig_sign':0.4,'temperature':39.5},
        'encephalitis': {'fever':0.85,'headache':0.75,'seizures':0.5,
                         'altered_consciousness':0.65,'neck_stiffness':0.4,
                         'vomiting':0.55,'photophobia':0.5,'confusion':0.6,
                         'duration_days':5,'temperature':39.2}
    }
    priors = SYMPTOM_PRIORS.get(disease, {})

    patient = {'age': age, 'gender': gender}
    for feat in features:
        if feat in ('age', 'gender'):
            continue
        prior = priors.get(feat, 0.5)
        if isinstance(prior, float) and prior <= 1.0:
            val = int(np.random.random() < prior)
        else:
            val = float(prior) + np.random.normal(0, prior * 0.1)

        # Add noise
        if noise_level > 0 and isinstance(val, int) and np.random.random() < noise_level:
            val = 1 - val  # flip boolean symptom

        # Simulate missing data
        if missing_pct > 0 and np.random.random() < missing_pct:
            val = 0  # treat missing as absent

        patient[feat] = val

    # Ground truth label (heuristic)
    pos_features = sum(
        1 for k,v in patient.items()
        if isinstance(v, int) and v == 1 and k not in ('age','gender')
    )
    threshold = len([f for f in features if f not in ('age','gender')]) * 0.45
    true_label = int(pos_features >= threshold)

    return patient, true_label


# ─── Simulation runner ────────────────────────────────────────────────────────

def run_simulation(params: dict) -> dict:
    """
    params keys:
      bandwidth         : '10kbps' | '50kbps' | '100kbps' | 'offline'
      model_size        : 'small' | 'medium'
      noise_level       : 0.0 – 0.4
      missing_data_pct  : 0.0 – 0.5
      num_patients      : int (10 – 200)
    """
    bandwidth       = params.get('bandwidth', '50kbps')
    model_size      = params.get('model_size', 'small')
    noise_level     = float(params.get('noise_level', 0.0))
    missing_pct     = float(params.get('missing_data_pct', 0.0))
    num_patients    = int(params.get('num_patients', 50))

    bw_overhead  = BANDWIDTH_LATENCY.get(bandwidth, 800)
    ms_overhead  = MODEL_SIZE_OVERHEAD.get(model_size, 0)
    use_cache    = (bandwidth == 'offline')

    results      = []
    tp = fp = tn = fn = 0
    latencies    = []
    times_to_care= []

    # Cached result for offline mode
    _cached = {}

    for i in range(num_patients):
        disease   = random.choice(DISEASES)
        patient, true_label = _random_patient(disease, noise_level, missing_pct)

        t_start = time.perf_counter()

        if use_cache and disease in _cached:
            pred = _cached[disease].copy()
            pred['latency_ms'] = 0.3
        else:
            try:
                pred = predict(disease, patient)
            except Exception:
                pred = rule_based_predict(patient)
            if use_cache:
                _cached[disease] = pred.copy()

        model_latency  = pred['latency_ms'] + ms_overhead
        network_latency= 0 if use_cache else bw_overhead
        total_latency  = model_latency + network_latency
        latencies.append(total_latency)

        pred_label = 1 if pred['risk_level'] in ('Medium', 'High') else 0

        if true_label == 1 and pred_label == 1: tp += 1
        elif true_label == 0 and pred_label == 1: fp += 1
        elif true_label == 1 and pred_label == 0: fn += 1
        else: tn += 1

        # Time-to-care simulation (hours)
        if pred['risk_level'] == 'High':
            referral_step  = 'Emergency'
            time_to_care   = round(random.uniform(0.5, 2.0), 1)
        elif pred['risk_level'] == 'Medium':
            referral_step  = 'PHC'
            time_to_care   = round(random.uniform(2, 8), 1)
        else:
            referral_step  = 'Home'
            time_to_care   = round(random.uniform(12, 48), 1)
        times_to_care.append(time_to_care)

        results.append({
            'patient_id':    i + 1,
            'disease':       disease,
            'true_label':    true_label,
            'predicted_risk': pred['risk_level'],
            'probability':   pred['probability'],
            'referral':      referral_step,
            'latency_ms':    round(total_latency, 1),
            'time_to_care_h': time_to_care
        })

    total  = tp + fp + tn + fn
    accuracy       = round((tp + tn) / total, 4) if total else 0
    precision      = round(tp / (tp + fp), 4) if (tp + fp) else 0
    recall         = round(tp / (tp + fn), 4) if (tp + fn) else 0
    f1             = round(2 * precision * recall / (precision + recall), 4) if (precision + recall) else 0
    detection_rate = round(tp / (tp + fn), 4) if (tp + fn) else 0
    avg_latency    = round(np.mean(latencies), 1)
    avg_time_care  = round(np.mean(times_to_care), 1)
    bandwidth_kb   = round(num_patients * (1.2 if model_size == 'small' else 3.5), 1)

    return {
        'params': params,
        'summary': {
            'accuracy':       accuracy,
            'precision':      precision,
            'recall':         recall,
            'f1':             f1,
            'detection_rate': detection_rate,
            'avg_latency_ms': avg_latency,
            'avg_time_to_care_h': avg_time_care,
            'bandwidth_kb_used': bandwidth_kb,
            'true_positives': tp,
            'false_positives': fp,
            'true_negatives': tn,
            'false_negatives': fn,
            'num_patients':   num_patients
        },
        'per_patient': results
    }
