# app/routes/admin_routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.security import check_password_hash
from functools import wraps
from app.models import User, Payment, Withdrawal, db
from datetime import datetime

admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin')

# ---------------- Admin required decorator ----------------
def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Admin access required.", "danger")
            return redirect(url_for('admin_bp.admin_login'))
        return f(*args, **kwargs)
    return wrapper

# ---------------- Admin Login ----------------
@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_bp.admin_dashboard'))
        else:
            flash("You are not an admin.", "danger")
            return redirect(url_for('user.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if not user:
            flash("User not found.", "danger")
        elif not user.is_admin:
            flash("You are not authorized as admin.", "danger")
        elif not check_password_hash(user.password, password):
            flash("Incorrect password.", "danger")
        else:
            login_user(user)
            flash(f"Welcome Admin {user.username}!", "success")
            return redirect(url_for('admin_bp.admin_dashboard'))

    return render_template('admin_login.html')



@admin_bp.route('/dashboard')
@login_required
@admin_required
def admin_dashboard():
    users = User.query.all()
    pending_payments = Payment.query.filter_by(status='pending').order_by(Payment.id.desc()).all()
    pending_withdrawals = Withdrawal.query.filter_by(status='pending').order_by(Withdrawal.id.desc()).all()
    total_earnings = sum(p.amount for p in Payment.query.filter_by(status='approved').all())
    total_withdrawn = sum(w.amount for w in Withdrawal.query.filter_by(status='approved').all())

    return render_template(
        'admin_dashboard.html',
        users=users,
        pending_payments=pending_payments,
        pending_withdrawals=pending_withdrawals,
        total_users=len(users),
        total_earnings=total_earnings,
        total_withdrawn=total_withdrawn,
        datetime=datetime  # <-- pass datetime here
    )


# ---------------- View Single User ----------------
@admin_bp.route('/user/<int:user_id>', methods=['GET'])
@login_required
@admin_required
def admin_user_view(user_id):
    user = User.query.get_or_404(user_id)

    referral_count = user.referrals.count()
    referral_earnings = referral_count * 70
    trivia_earnings = sum(q.earned for q in getattr(user, 'trivia_answers', []))
    spin_stakes = sum(s.stake for s in getattr(user, 'spins', []))
    spin_wins = sum(s.reward for s in getattr(user, 'spins', []) if s.reward > 0)
    total_approved_withdrawals = sum(w.amount for w in user.withdrawals if w.status == 'approved')

    withdrawable_balance = referral_earnings + trivia_earnings + spin_wins - total_approved_withdrawals - spin_stakes
    withdrawable_balance = max(withdrawable_balance, 0)

    withdrawals = Withdrawal.query.filter_by(user_id=user.id).order_by(Withdrawal.id.desc()).all()
    payments = Payment.query.filter_by(user_id=user.id).order_by(Payment.id.desc()).all()

    total_earnings = referral_earnings + trivia_earnings + spin_wins
    total_withdrawn = total_approved_withdrawals + spin_stakes

    return render_template(
        'admin_user_view.html',
        user=user,
        referral_earnings=referral_earnings,
        referral_count=referral_count,
        trivia_earnings=trivia_earnings,
        withdrawable_balance=withdrawable_balance,
        withdrawals=withdrawals,
        payments=payments,
        total_earnings=total_earnings,
        total_withdrawn=total_withdrawn
    )

# ---------------- Approve Payment ----------------
@admin_bp.route('/payment/approve/<int:payment_id>')
@login_required
@admin_required
def approve_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    payment.status = 'approved'
    user = payment.user
    if user.status != 'active':
        user.status = 'active'
    db.session.commit()
    flash(f"Payment {payment.id} approved. User '{user.username}' is now active.", "success")
    return redirect(url_for('admin_bp.admin_dashboard'))

# ---------------- Decline Payment ----------------
@admin_bp.route('/payment/decline/<int:payment_id>')
@login_required
@admin_required
def decline_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    payment.status = 'declined'
    db.session.commit()
    flash(f"Payment {payment.id} declined.", "warning")
    return redirect(url_for('admin_bp.admin_dashboard'))

# ---------------- Approve Withdrawal ----------------
@admin_bp.route('/withdrawal/approve/<int:withdrawal_id>')
@login_required
@admin_required
def approve_withdrawal(withdrawal_id):
    withdrawal = Withdrawal.query.get_or_404(withdrawal_id)
    withdrawal.status = 'approved'
    db.session.commit()
    flash(f"Withdrawal {withdrawal.id} approved.", "success")
    return redirect(url_for('admin_bp.admin_dashboard'))

# ---------------- Decline Withdrawal ----------------
@admin_bp.route('/withdrawal/decline/<int:withdrawal_id>')
@login_required
@admin_required
def decline_withdrawal(withdrawal_id):
    withdrawal = Withdrawal.query.get_or_404(withdrawal_id)
    withdrawal.status = 'declined'
    db.session.commit()
    flash(f"Withdrawal {withdrawal.id} declined.", "warning")
    return redirect(url_for('admin_bp.admin_dashboard'))

# ---------------- Admin Logout ----------------
@admin_bp.route('/logout')
@login_required
@admin_required
def admin_logout():
    logout_user()
    flash("Logged out successfully.", "success")
    return redirect(url_for('admin_bp.admin_login'))
