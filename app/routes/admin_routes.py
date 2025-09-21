# app/routes/admin_routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.security import check_password_hash
from functools import wraps
from app.models import User, Payment, Withdrawal, TriviaAnswer, WhatsAppPost, Spin, db
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


# ---------------- Admin Dashboard ----------------
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
        datetime=datetime
    )


# ---------------- View & Edit Single User ----------------
@admin_bp.route('/user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_user_view(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        # Update balances from form safely
        user.referral_balance = request.form.get('referral_balance', type=float) or 0
        user.trivia_balance = request.form.get('trivia_balance', type=float) or 0
        user.youtube_balance = request.form.get('youtube_balance', type=float) or 0
        user.whatsapp_balance = request.form.get('whatsapp_balance', type=float) or 0

        db.session.commit()
        flash(f"{user.username}'s wallet updated successfully.", "success")
        return redirect(url_for('admin_bp.admin_user_view', user_id=user.id))

    # ---------------- Wallet Calculations ----------------
    active_referrals = [r for r in user.referrals if r.status == 'active']
    referral_earnings_dynamic = len(active_referrals) * 70  # Adjust referral logic

    trivia_earnings_dynamic = sum([t.earned for t in getattr(user, 'trivia_answers', [])])
    spin_stakes = sum([s.stake for s in getattr(user, 'spins', [])])
    spin_wins = sum([s.reward for s in getattr(user, 'spins', []) if s.reward and s.reward > 0])

    whatsapp_earnings_dynamic = sum([w.total_earned for w in getattr(user, 'whatsapp_posts', [])])

    total_approved_withdrawals = sum([w.amount for w in user.withdrawals if w.status == 'approved'])

    # Safe balance defaults
    referral_balance = user.referral_balance or 0
    trivia_balance = user.trivia_balance or 0
    youtube_balance = user.youtube_balance or 0
    whatsapp_balance = user.whatsapp_balance or 0

    total_wallet = (
        referral_balance + trivia_balance + youtube_balance + whatsapp_balance +
        referral_earnings_dynamic + trivia_earnings_dynamic + spin_wins + whatsapp_earnings_dynamic
    )
    withdrawable_balance = max(total_wallet - total_approved_withdrawals - spin_stakes, 0)

    withdrawals = Withdrawal.query.filter_by(user_id=user.id).order_by(Withdrawal.id.desc()).all()
    payments = Payment.query.filter_by(user_id=user.id).order_by(Payment.id.desc()).all()

    return render_template(
        'admin_user_view.html',
        user=user,
        referral_count=len(active_referrals),
        referral_earnings_dynamic=referral_earnings_dynamic,
        trivia_earnings_dynamic=trivia_earnings_dynamic,
        whatsapp_earnings_dynamic=whatsapp_earnings_dynamic,
        spin_stakes=spin_stakes,
        spin_wins=spin_wins,
        total_withdrawn=total_approved_withdrawals + spin_stakes,
        total_wallet=total_wallet,
        withdrawable_balance=withdrawable_balance,
        withdrawals=withdrawals,
        payments=payments
    )


# ---------------- Approve / Decline Payments ----------------
@admin_bp.route('/payment/approve/<int:payment_id>')
@login_required
@admin_required
def approve_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    payment.status = 'approved'
    if payment.user.status != 'active':
        payment.user.status = 'active'
    db.session.commit()
    flash(f"Payment {payment.id} approved.", "success")
    return redirect(url_for('admin_bp.admin_dashboard'))


@admin_bp.route('/payment/decline/<int:payment_id>')
@login_required
@admin_required
def decline_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    payment.status = 'declined'
    # Reset user status back to "new" so they can repay
    if payment.user:
        payment.user.status = "new"
    db.session.commit()
    flash(f"Payment {payment.id} declined, user reset to NEW.", "warning")
    return redirect(url_for('admin_bp.admin_dashboard'))


# ---------------- Approve / Decline Withdrawals ----------------
@admin_bp.route('/withdrawal/approve/<int:withdrawal_id>')
@login_required
@admin_required
def approve_withdrawal(withdrawal_id):
    withdrawal = Withdrawal.query.get_or_404(withdrawal_id)
    withdrawal.status = 'approved'
    db.session.commit()
    flash(f"Withdrawal {withdrawal.id} approved.", "success")
    return redirect(url_for('admin_bp.admin_dashboard'))


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
