from functools import wraps
from flask import session, jsonify, redirect, url_for, request

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Não autenticado. Faça login primeiro.'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function