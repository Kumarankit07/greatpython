from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Prediction, SimulationRun
from app.ml.engine import get_metrics
import json

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


@dashboard_bp.route('/')
@login_required
def index():
    # User's recent predictions
    predictions = Prediction.query.filter_by(user_id=current_user.id)\
                                  .order_by(Prediction.created_at.desc()).limit(10).all()

    # User's simulation runs
    sim_runs = SimulationRun.query.filter_by(user_id=current_user.id)\
                                   .order_by(SimulationRun.created_at.desc()).limit(5).all()

    # ML model metrics
    metrics = get_metrics()

    # Aggregate stats for this user
    total_predictions = Prediction.query.filter_by(user_id=current_user.id).count()
    high_risk = Prediction.query.filter_by(user_id=current_user.id, risk_level='High').count()
    medium_risk = Prediction.query.filter_by(user_id=current_user.id, risk_level='Medium').count()
    low_risk = Prediction.query.filter_by(user_id=current_user.id, risk_level='Low').count()

    # Disease distribution
    disease_counts = {}
    all_preds = Prediction.query.filter_by(user_id=current_user.id).all()
    for p in all_preds:
        disease_counts[p.disease] = disease_counts.get(p.disease, 0) + 1

    # Chart data for recent simulations
    sim_chart = []
    for s in reversed(sim_runs):
        sim_chart.append({
            'bandwidth': s.bandwidth,
            'accuracy': s.accuracy,
            'latency': s.avg_latency_ms,
            'detection_rate': s.detection_rate,
            'label': s.created_at.strftime('%d %b')
        })

    return render_template('dashboard/index.html',
                           predictions=predictions,
                           sim_runs=sim_runs,
                           metrics=metrics,
                           total_predictions=total_predictions,
                           high_risk=high_risk,
                           medium_risk=medium_risk,
                           low_risk=low_risk,
                           disease_counts=disease_counts,
                           sim_chart=sim_chart)
