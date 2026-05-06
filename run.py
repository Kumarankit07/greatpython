"""
run.py — Application entry point.
Run with:  python run.py
"""
import os
from app import create_app

app = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n{'='*55}")
    print("  NeuroCare AI -- Symptom Checker Platform")
    print(f"  Running at: http://127.0.0.1:{port}")
    print(f"  Demo ASHA:    asha@demo.com  / asha1234")
    print(f"  Demo Patient: patient@demo.com / patient1234")
    print(f"{'='*55}\n")
    app.run(host='0.0.0.0', port=port, debug=True)
