# NeuroCare AI — AI-Powered Symptom Checker for Rural India

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Train ML models (run once)
python train_models.py

# 3. Launch the app
python run.py
```

Open http://127.0.0.1:5000

## Demo Credentials

| Role         | Email               | Password     |
|--------------|---------------------|--------------|
| Patient      | patient@demo.com    | patient1234  |
| ASHA Worker  | asha@demo.com       | asha1234     |

## Project Structure

```
developmet/
├── run.py                  # App entry point
├── train_models.py         # Train ML models (run once)
├── config.py               # Configuration
├── requirements.txt
├── app/
│   ├── __init__.py         # App factory
│   ├── models.py           # DB models (User, Prediction, SimulationRun)
│   ├── routes/
│   │   ├── auth.py         # Login / Register / Logout
│   │   ├── main.py         # Home / About
│   │   ├── predict.py      # Symptom checker + results
│   │   ├── simulation.py   # Simulation panel + runner
│   │   └── dashboard.py    # Analytics dashboard
│   ├── ml/
│   │   ├── engine.py       # Train, load, predict (LR + rule-based)
│   │   └── models/         # Saved .pkl files + metrics.json
│   ├── simulation/
│   │   └── engine.py       # Discrete-event simulation
│   ├── data/
│   │   ├── encephalitis_data.py   # Static dataset generator
│   │   └── encephalitis.csv       # Generated on first run
│   ├── static/
│   │   ├── css/main.css
│   │   └── js/main.js
│   └── templates/
│       ├── base.html
│       ├── home.html
│       ├── about.html
│       ├── auth/login.html, register.html
│       ├── predict/checker.html, result.html, history.html
│       ├── simulation/panel.html, results.html
│       └── dashboard/index.html
```

## Diseases Covered

| Disease      | Dataset Source       | Model               |
|--------------|----------------------|---------------------|
| Stroke       | Kaggle (fedesoriano) | Logistic Regression |
| Epilepsy     | Kaggle EEG dataset   | Logistic Regression |
| Meningitis   | Kaggle               | Logistic Regression |
| Encephalitis | Static CSV           | Logistic Regression |

## Simulation Parameters

- **Bandwidth**: Offline / 10kbps / 50kbps / 100kbps / 1Mbps
- **Model Size**: Small / Medium
- **Symptom Noise**: 0–40% random flip
- **Missing Data**: 0–50% missing features
- **Patients**: 10–200 synthetic profiles
