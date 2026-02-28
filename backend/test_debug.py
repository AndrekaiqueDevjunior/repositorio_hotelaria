#!/usr/bin/env python3

try:
    from app.main import app
    print("✅ Import successful")
    print(f"App type: {type(app)}")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
