"""Ponto de entrada da aplicação. Uso: python run.py"""
from webapp import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8501, debug=False, threaded=True)
