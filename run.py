"""
run.py - Safe launcher for the RAG Assistant.
Run with: python run.py
"""
import sys
import os
from pathlib import Path

ROOT = Path(__file__).parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

# 1. Python version
if sys.version_info < (3, 9):
    print(f"ERROR: Python 3.9+ required. You have {sys.version}")
    sys.exit(1)
print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}")

# 2. Required packages
missing = []
for pkg, import_name in [
    ("flask",        "flask"),
    ("flask-cors",   "flask_cors"),
    ("waitress",     "waitress"),
    ("anthropic",    "anthropic"),
    ("dotenv",       "dotenv"),
    ("httpx",        "httpx"),
]:
    try:
        __import__(import_name)
        print(f"✓ {pkg}")
    except ImportError:
        missing.append(pkg)
        print(f"✗ {pkg} NOT INSTALLED")

if missing:
    print("\nERROR: Run this first:")
    print("  pip install -r requirements-windows.txt")
    sys.exit(1)

# 3. .env and API key
env_path = ROOT / ".env"
if not env_path.exists():
    print("\nERROR: .env file not found.")
    print("Fix:  copy .env.example .env   then add your ANTHROPIC_API_KEY")
    # sys.exit(1)

from dotenv import load_dotenv
load_dotenv(env_path)
api_key = os.getenv("ANTHROPIC_API_KEY", "")
if not api_key or "your_anthropic_api_key_here" in api_key:
    print("\nERROR: ANTHROPIC_API_KEY not set in .env")
    print("Get a free key at: https://console.anthropic.com")
    sys.exit(1)
print("✓ ANTHROPIC_API_KEY set")

# 4. docs.json
if not (ROOT / "docs.json").exists():
    print("\nERROR: docs.json not found")
    sys.exit(1)
print("✓ docs.json found")

# 5. Import app (triggers document indexing)
print("\nIndexing knowledge base...")
try:
    from app.main import app
    print("✓ App ready")
except Exception as e:
    import traceback
    print(f"\nERROR starting app: {e}")
    traceback.print_exc()
    sys.exit(1)

# 6. Launch with waitress (production WSGI server, pure Python)
port = int(os.getenv("APP_PORT", "8000"))
print()
print("=" * 50)
print(f"  RAG Assistant running on http://localhost:{port}")
print("  Press Ctrl+C to stop")
print("=" * 50)

from waitress import serve
serve(app, host="0.0.0.0", port=port, threads=4)