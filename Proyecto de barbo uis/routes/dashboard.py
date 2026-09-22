from flask import Blueprint, render_template
from flask_login import login_required

# Dashboard blueprint

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def dashboard():
    # Here we could fetch summary data for the dashboard
    # For now, we just render the template
    return render_template('dashboard.html')
