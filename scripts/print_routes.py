from importlib import import_module
import sys
import os

def load_app():
    """
    Import and return a Flask app instance.
    Tries app:app then main:app as fallback.
    """
    try:
        # Add current directory to Python path
        sys.path.insert(0, os.getcwd())
        
        # Try importing from app module
        try:
            mod = import_module("app")
            if hasattr(mod, "app"):
                return getattr(mod, "app")
        except ImportError:
            pass
            
        # Try importing from main module 
        try:
            mod = import_module("main")
            if hasattr(mod, "app"):
                return getattr(mod, "app")
        except ImportError:
            pass
            
        # If neither works, raise error
        raise ImportError("Could not find Flask app in 'app' or 'main' modules")
        
    except Exception as e:
        raise SystemExit(f"Could not import Flask app: {e}")

def main():
    try:
        app = load_app()
        if app is None:
            raise SystemExit("Flask app is None")
            
        with app.app_context():
            for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
                methods = ",".join(sorted(m for m in rule.methods if m not in ("HEAD","OPTIONS")))
                print(f"{rule.endpoint}|{methods}|{rule.rule}")
    except Exception as e:
        raise SystemExit(f"Error listing routes: {e}")

if __name__ == "__main__":
    main()