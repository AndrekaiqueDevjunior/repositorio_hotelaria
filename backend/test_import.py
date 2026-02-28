#!/usr/bin/env python3
"""Testar import do app.main"""
try:
    import app.main
    print("✅ Import OK!")
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()

