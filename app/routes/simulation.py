import json
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import SimulationRun
from app.simulation.engine import run_simulation

simulation_bp = Blueprint('simulation', __name__, url_prefix='/simulation')


@simulation_bp.route('/')
@login_required
def panel():
    runs = SimulationRun.query.filter_by(user_id=current_user.id)\
                               .order_by(SimulationRun.created_at.desc()).limit(10).all()
    return render_template('simulation/panel.html', runs=runs)


@simulation_bp.route('/run', methods=['POST'])
@login_required
def run():
    params = {
        'bandwidth':         request.form.get('bandwidth', '50kbps'),
        'model_size':        request.form.get('model_size', 'small'),
        'noise_level':       float(request.form.get('noise_level', 0.0)),
        'missing_data_pct':  float(request.form.get('missing_data_pct', 0.0)),
        'num_patients':      int(request.form.get('num_patients', 50)),
    }

    try:
        results = run_simulation(params)
        summary = results['summary']

        run_record = SimulationRun(
            user_id=current_user.id,
            bandwidth=params['bandwidth'],
            model_size=params['model_size'],
            noise_level=params['noise_level'],
            missing_data_pct=params['missing_data_pct'],
            num_patients=params['num_patients'],
            results_json=json.dumps(results['per_patient']),
            detection_rate=summary['detection_rate'],
            avg_time_to_care=summary['avg_time_to_care_h'],
            accuracy=summary['accuracy'],
            avg_latency_ms=summary['avg_latency_ms']
        )
        db.session.add(run_record)
        db.session.commit()

        return render_template('simulation/results.html',
                               params=params,
                               summary=summary,
                               per_patient=results['per_patient'][:20])

    except Exception as e:
        flash(f'Simulation error: {str(e)}', 'danger')
        return redirect(url_for('simulation.panel'))


@simulation_bp.route('/api/run', methods=['POST'])
@login_required
def api_run():
    params = request.get_json(force=True)
    try:
        results = run_simulation(params)
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
