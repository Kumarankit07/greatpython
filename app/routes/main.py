import json
from flask import Blueprint, render_template, request, jsonify
from flask_login import current_user, login_required
from app import db
from app.models import User, Prediction

main_bp = Blueprint('main', __name__)

# ── Chatbot knowledge base ────────────────────────────────────────────────────
CHAT_KB = {
    'stroke': {
        'keywords': ['stroke','facial droop','arm weakness','speech','slurred','vision loss','sudden headache'],
        'response': '🔴 **Stroke Warning Signs (FAST):**\n• **F**ace drooping\n• **A**rm weakness\n• **S**peech difficulty\n• **T**ime to call 108\n\nStroke is a medical emergency. Every minute of delay causes brain damage. Call **108** immediately and go to the nearest hospital with a CT scanner.'
    },
    'epilepsy': {
        'keywords': ['epilepsy','seizure','convulsion','fits','jerking','unconscious','aura'],
        'response': '⚡ **Epilepsy First Aid:**\n• Stay calm — do NOT hold the person down\n• Clear the area of sharp objects\n• Turn them on their side (recovery position)\n• Time the seizure — if >5 min, call 108\n• Do NOT put anything in their mouth\n\nIf this is the first seizure, visit a neurologist for EEG evaluation.'
    },
    'meningitis': {
        'keywords': ['meningitis','neck stiff','stiff neck','rash','photophobia','light sensitivity','headache fever'],
        'response': '🦠 **Meningitis Warning Signs:**\n• Severe headache + stiff neck + fever = EMERGENCY\n• Purple/red skin rash (non-blanching)\n• Sensitivity to light\n• Confusion or altered consciousness\n\nBacterial meningitis is life-threatening. Do NOT wait — go to emergency immediately. IV antibiotics must start within hours.'
    },
    'encephalitis': {
        'keywords': ['encephalitis','brain swelling','confusion','altered','behaviour change','hallucination'],
        'response': '🌡️ **Encephalitis Signs:**\n• High fever + severe headache\n• Confusion or personality changes\n• Seizures\n• Difficulty speaking or moving\n\nEncephalitis is brain inflammation (usually viral). It requires hospital admission for antiviral treatment and monitoring. Call 108 if these symptoms appear suddenly.'
    },
    'asha': {
        'keywords': ['asha','asha worker','how to use','screening','community','village'],
        'response': '👩‍⚕️ **ASHA Worker Guide:**\n1. Register as ASHA Worker on this platform\n2. Use the Symptom Checker to screen patients in your village\n3. For HIGH risk → arrange emergency referral & call 108\n4. For MEDIUM risk → escort patient to PHC within 24 hours\n5. For LOW risk → advise home rest, schedule follow-up\n\nUse the Simulation panel to practice decision-making in different bandwidth scenarios.'
    },
    'bandwidth': {
        'keywords': ['offline','bandwidth','slow internet','no internet','connection','kbps'],
        'response': '📡 **Low-Bandwidth Mode:**\n• This platform works at 10 kbps (rural GPRS speed)\n• Select "Offline (Cached)" in the bandwidth setting for zero-network use\n• ML models are pre-loaded — no internet needed for prediction\n• Simulation can run fully offline to test different scenarios'
    },
    'emergency': {
        'keywords': ['emergency','ambulance','108','hospital','urgent','critical'],
        'response': '🚨 **Emergency Contacts (India):**\n• **108** — Free ambulance service (all states)\n• **102** — Free ambulance for pregnant women\n• **1800-180-1104** — National Health Helpline\n\nFor neurological emergencies: request a hospital with a **CT scanner** and **neurologist** on call. Describe FAST symptoms to the dispatcher.'
    },
    'accuracy': {
        'keywords': ['accuracy','model','how accurate','reliable','correct','prediction','result'],
        'response': '🎯 **Model Accuracy:**\n• Stroke: 84.3% accuracy, F1=71.8%\n• Epilepsy: 85.5% accuracy, F1=83.1%\n• Meningitis: 82.4% accuracy, F1=82.3%\n• Encephalitis: 94.0% accuracy, F1=96.2%\n\n⚠️ This is a screening/research tool — NOT a medical diagnosis. Always confirm with a doctor.'
    }
}

def _chatbot_reply(msg: str) -> str:
    msg_lower = msg.lower()
    best_match = None
    best_score = 0
    for topic, data in CHAT_KB.items():
        score = sum(1 for kw in data['keywords'] if kw in msg_lower)
        if score > best_score:
            best_score = score
            best_match = data['response']

    if best_match and best_score > 0:
        return best_match

    # Greetings
    if any(w in msg_lower for w in ['hi','hello','hey','namaste','help']):
        return '👋 **Hello! I\'m NeuroBot.**\n\nI can help you with:\n• 🔴 Stroke symptoms & first aid\n• ⚡ Epilepsy & seizure management\n• 🦠 Meningitis warning signs\n• 🌡️ Encephalitis information\n• 👩‍⚕️ ASHA worker guidance\n• 📡 Offline/low-bandwidth tips\n• 🚨 Emergency contacts\n\nWhat would you like to know?'

    return '🤔 I\'m not sure about that. Try asking about **stroke**, **epilepsy**, **meningitis**, **encephalitis**, **emergency numbers**, or **how to use this platform** as an ASHA worker.'


@main_bp.route('/')
def home():
    return render_template('home.html')

@main_bp.route('/about')
def about():
    return render_template('about.html')

@main_bp.route('/diseases')
def diseases():
    return render_template('diseases.html')

@main_bp.route('/profile')
@login_required
def profile():
    preds = Prediction.query.filter_by(user_id=current_user.id).order_by(Prediction.created_at.desc()).limit(5).all()
    total = Prediction.query.filter_by(user_id=current_user.id).count()
    high  = Prediction.query.filter_by(user_id=current_user.id, risk_level='High').count()
    return render_template('profile.html', predictions=preds, total=total, high_risk=high)

@main_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    from flask import flash, redirect, url_for
    current_user.name     = request.form.get('name', current_user.name)
    current_user.phone    = request.form.get('phone', current_user.phone)
    current_user.village  = request.form.get('village', current_user.village)
    current_user.district = request.form.get('district', current_user.district)
    current_user.state    = request.form.get('state', current_user.state)
    db.session.commit()
    flash('Profile updated successfully!', 'success')
    from flask import redirect, url_for
    return redirect(url_for('main.profile'))

@main_bp.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json(force=True)
    msg  = data.get('message', '').strip()
    if not msg:
        return jsonify({'reply': 'Please type a message.'})
    reply = _chatbot_reply(msg)
    return jsonify({'reply': reply})

