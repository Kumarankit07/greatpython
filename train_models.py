"""
train_models.py — Run this once to train and save all ML models.
Usage: python train_models.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

# Generate encephalitis CSV first
from app.data.encephalitis_data import generate_encephalitis_csv
generate_encephalitis_csv()

# Train all models
from app.ml.engine import train_all_models
metrics = train_all_models()

print("\n=== Training Complete ===")
for disease, m in metrics.items():
    print(f"  {disease:15s}  acc={m['accuracy']:.3f}  f1={m['f1']:.3f}  prec={m['precision']:.3f}  rec={m['recall']:.3f}")
print("Models saved to: app/ml/models/")
