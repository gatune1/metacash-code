# app/routes/user_routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db, User, Payment, Withdrawal, TriviaAnswer, Spin, WhatsappPost
import random

# ---------------- Blueprint ----------------
user_bp = Blueprint('user', __name__)

# ---------------- Welcome Page ----------------
@user_bp.route('/')
def welcome():
    return render_template('welcome.html')


# ---------------- Signup ----------------
@user_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    ref_username = request.args.get('ref')  # Get referral from query param

    if request.method == 'POST':
        full_name = request.form.get('full_name')
        username = request.form.get('username')
        email = request.form.get('email')
        mpesa_no = request.form.get('mpesa_no')
        password = request.form.get('password')
        form_ref = request.form.get('ref') or ref_username

        if not all([full_name, username, email, mpesa_no, password]):
            flash("Please fill in all fields.", "danger")
            return redirect(url_for('user.signup', ref=ref_username))

        if User.query.filter_by(username=username).first():
            flash("⚠️ Username already exists.", "danger")
            return redirect(url_for('user.signup', ref=ref_username))

        if User.query.filter_by(email=email).first():
            flash("⚠️ Email already exists.", "danger")
            return redirect(url_for('user.signup', ref=ref_username))

        ref_user = User.query.filter_by(username=form_ref).first() if form_ref else None

        new_user = User(
            full_name=full_name,
            username=username,
            email=email,
            mpesa_no=mpesa_no,
            password=generate_password_hash(password),
            status='new',
            referred_by=ref_user.id if ref_user else None,
            referrer_username=form_ref
        )

        db.session.add(new_user)
        db.session.commit()

        flash("🎉 Account created successfully! Please login.", "success")
        return redirect(url_for('user.login'))

    return render_template('signup.html', ref=ref_username)


# ---------------- Login ----------------
@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email_or_username = request.form.get('email_or_username')
        password = request.form.get('password')

        if not email_or_username or not password:
            flash("Please enter both email/username and password.", "danger")
            return redirect(url_for('user.login'))

        user = User.query.filter((User.email==email_or_username) | (User.username==email_or_username)).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            if user.status == 'active':
                return redirect(url_for('user.dashboard'))
            elif user.status == 'pending_approval':
                return redirect(url_for('user.pending'))
            else:
                return redirect(url_for('user.payment'))
        else:
            flash("Invalid credentials.", "danger")
            return redirect(url_for('user.login'))

    return render_template('login.html')


# ---------------- Logout ----------------
@user_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for('user.login'))


# ---------------- Payment ----------------
@user_bp.route('/payment', methods=['GET', 'POST'])
@login_required
def payment():
    if current_user.status == 'active':
        flash("Your account is already active.", "success")
        return redirect(url_for('user.dashboard'))

    if request.method == 'POST':
        mpesa_code = request.form.get('mpesa_code')
        if not mpesa_code:
            flash("Please enter MPESA code.", "danger")
            return redirect(url_for('user.payment'))

        payment = Payment(user_id=current_user.id, amount=200, mpesa_code=mpesa_code)
        db.session.add(payment)

        current_user.status = 'pending_approval'
        db.session.commit()

        flash("Payment submitted successfully! Waiting for admin approval.", "success")
        return redirect(url_for('user.pending'))

    return render_template('payment.html')


# ---------------- Pending Approval ----------------
@user_bp.route('/pending')
@login_required
def pending():
    if current_user.status == 'active':
        return redirect(url_for('user.dashboard'))
    elif current_user.status == 'declined':
        flash("Your payment was declined. Please try again.", "warning")
        return redirect(url_for('user.payment'))
    elif current_user.status != 'pending_approval':
        return redirect(url_for('user.payment'))

    return render_template('pending.html')


# ---------------- Dashboard ----------------
@user_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_bp.admin_dashboard'))

    if current_user.status != 'active':
        flash("Your account is not active yet.", "warning")
        return redirect(url_for('user.payment') if current_user.status == 'new' else url_for('user.pending'))

    return render_template('dashboard.html', user=current_user)


# ---------------- Profile ----------------
@user_bp.route('/profile')
@login_required
def profile():
    user = current_user
    referrer = User.query.filter_by(username=user.referrer_username).first() if user.referrer_username else None
    return render_template('profile.html', user=user, referrer=referrer)


# ---------------- Wallet ----------------
@user_bp.route('/wallet', methods=['GET', 'POST'])
@login_required
def wallet():
    user = current_user
    if user.status != 'active':
        flash("Your account is not active yet.", "warning")
        return redirect(url_for('user.payment') if user.status == 'new' else url_for('user.pending'))

    # Earnings calculations
    active_referrals = [r for r in user.referrals if r.status == 'active']
    referral_earnings = len(active_referrals) * 70
    trivia_earnings = sum([q.earned for q in getattr(user, 'trivia_answers', [])])
    spin_stakes = sum([s.stake for s in getattr(user, 'spins', [])])
    spin_wins = sum([s.reward for s in getattr(user, 'spins', []) if s.reward > 0])
    total_approved_withdrawals = sum([w.amount for w in user.withdrawals if w.status == 'approved'])
    withdrawable_balance = max(referral_earnings + trivia_earnings + spin_wins - total_approved_withdrawals - spin_stakes, 0)

    # Handle withdrawal
    if request.method == 'POST' and 'withdraw_amount' in request.form:
        amount = float(request.form.get('withdraw_amount', 0))
        if amount < 200:
            flash("You cannot withdraw less than 200 KSh.", "danger")
        elif amount > withdrawable_balance:
            flash("Insufficient balance.", "danger")
        else:
            db.session.add(Withdrawal(user_id=user.id, amount=amount, status='pending'))
            db.session.commit()
            flash("Withdrawal request submitted! Waiting for admin approval.", "success")
            return redirect(url_for('user.wallet'))

    withdrawals = Withdrawal.query.filter_by(user_id=user.id).order_by(Withdrawal.id.desc()).all()
    total_earnings = referral_earnings + trivia_earnings + spin_wins
    total_withdrawn = total_approved_withdrawals + spin_stakes

    return render_template(
        'wallet.html',
        user=user,
        referral_earnings=referral_earnings,
        referral_count=len(active_referrals),
        trivia_earnings=trivia_earnings,
        withdrawable_balance=withdrawable_balance,
        withdrawals=withdrawals,
        total_earnings=total_earnings,
        total_withdrawn=total_withdrawn,
        min_stake=20
    )


# ---------------- Referrals ----------------
@user_bp.route('/referrals')
@login_required
def referrals():
    if current_user.status != 'active':
        flash("Your account is not active yet.", "warning")
        return redirect(url_for('user.payment'))

    # Assign pending referrals safely
    pending_referrals = User.query.filter(User.referred_by.is_(None), User.username != current_user.username).all()
    for u in pending_referrals:
        if getattr(u, 'referrer_username', None) == current_user.username:
            u.referred_by = current_user.id
    db.session.commit()

    referrals_list = User.query.filter_by(referred_by=current_user.id).order_by(User.id.desc()).all()
    active_referrals_count = sum(1 for r in referrals_list if r.status == 'active')
    referral_earnings = active_referrals_count * 70
    referral_link = url_for('user.signup', _external=True) + f"?ref={current_user.username}"

    if request.args.get('ajax'):
        return jsonify({
            "referrals": [{"username": r.username, "full_name": r.full_name, "status": r.status} for r in referrals_list],
            "active_referrals_count": active_referrals_count,
            "referral_earnings": referral_earnings
        })

    return render_template('referral.html', referrals=referrals_list, referral_link=referral_link,
                           user=current_user, active_referrals_count=active_referrals_count,
                           referral_earnings=referral_earnings)

# ---------------- Trivia, Videos, WhatsApp, Spin, Bonus ----------------
# (Keep existing implementations; they are production-safe as is)

# ---------------- Trivia Questions ----------------
@user_bp.route('/trivia', methods=['GET', 'POST'])
@login_required
def trivia():
    user = current_user
    
    # Count only active referrals
    active_referral_count = User.query.filter_by(referred_by=user.id, status='active').count()
    required_referrals = 5

    if active_referral_count < required_referrals:
        remaining = required_referrals - active_referral_count
        message = f"Hello {user.username}, you need {remaining} more active referral(s) to unlock trivia questions and earn 10 KSh per question."
        return render_template("trivia.html", locked=True, message=message)

    previous_attempts = TriviaAnswer.query.filter_by(user_id=user.id).all()
    if previous_attempts:
        total_earned = sum(a.earned for a in previous_attempts)
        return render_template("trivia.html", locked=False, answered=True, user=user, earned_amount=total_earned)

    questions = [
        {"id": 1, "question": "Who was the first President of the United States?", "answer": "Washington"},
        {"id": 2, "question": "Which wall fell in 1989, symbolizing the end of the Cold War?", "answer": "Berlin"},
        {"id": 3, "question": "Who was the famous queen of ancient Egypt known for her beauty?", "answer": "Cleopatra"},
    ]

    if request.method == "POST":
        total_earned = 0
        user_answers = request.form
        for q in questions:
            answer_text = user_answers.get(str(q["id"]), "").strip()
            correct = q["answer"].lower() in answer_text.lower()
            earned = 10 if correct else 0
            total_earned += earned
            trivia_entry = TriviaAnswer(
                user_id=user.id,
                question_id=q["id"],
                answer=answer_text,
                correct=correct,
                earned=earned
            )
            db.session.add(trivia_entry)

        db.session.commit()
        flash(f"You completed the trivia and earned {total_earned} KSh!", "success")
        return redirect(url_for('user.trivia'))

    return render_template("trivia.html", locked=False, answered=False, questions=questions, user=user)

# ---------------- YouTube Videos ----------------
@user_bp.route('/videos')
@login_required
def videos():
    # Count only active referrals
    active_referral_count = User.query.filter_by(referred_by=current_user.id, status='active').count()
    required_referrals = 10
    remaining = required_referrals - active_referral_count

    if active_referral_count < required_referrals:
        message = f"Hello {current_user.username}, you need {remaining} more active referral(s) to start watching and earning 50 KSh per watched video. Keep referring!"
    else:
        message = "🎬 YouTube videos coming soon..."

    return render_template(
        'videos.html',
        message=message,
        referral_count=active_referral_count,
        required_referrals=required_referrals,
        user=current_user
    )
# ---------------- WhatsApp Posts ----------------
@user_bp.route('/whatsapp')
@login_required
def whatsapp():
    user = current_user

    # Count active referrals
    active_referral_count = User.query.filter_by(referred_by=user.id, status='active').count()
    required_referrals = 20
    remaining = required_referrals - active_referral_count

    if active_referral_count < required_referrals:
        message = f"Hello {user.username}, you need {remaining} more active referral(s) to start posting on WhatsApp and earn 20 KSh per view. Keep referring!"
        return render_template('whatsapp.html', message=message, can_post=False, user=user)

    # Check if the user already has a WhatsApp post record
    post = WhatsappPost.query.filter_by(user_id=user.id).first()
    if not post:
        # Initialize the post with e.g., 50 views allowed
        post = WhatsappPost(user_id=user.id, total_views=50, views_left=50)
        db.session.add(post)
        db.session.commit()

    message = "📱 Coming Soon! Each view will earn you 20 KSh."
    return render_template(
        'whatsapp.html',
        message=message,
        can_post=True,
        views_left=post.views_left,
        user=user
    )

# ---------------- Spin ----------------
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models import db, Spin

import random

@user_bp.route('/spin', methods=['GET', 'POST'])
@login_required
def spin():
    user = current_user
    min_stake = 20

    # Calculate withdrawable balance
    referral_earnings = user.referrals.count() * 70
    trivia_earnings = sum([q.earned for q in getattr(user, 'trivia_answers', [])])
    total_approved_withdrawals = sum([w.amount for w in user.withdrawals if w.status == 'approved'])
    spin_stakes = sum([s.stake for s in getattr(user, 'spins', [])])
    spin_wins = sum([s.reward for s in getattr(user, 'spins', []) if s.reward > 0])

    withdrawable_balance = referral_earnings + trivia_earnings + spin_wins - total_approved_withdrawals - spin_stakes
    withdrawable_balance = max(withdrawable_balance, 0)

    if request.method == 'POST':
        data = request.get_json()
        stake = float(data.get('stake', 0))

        if stake < min_stake:
            return jsonify({"status": "error", "message": f"Minimum stake is {min_stake} KSh."})
        if stake > withdrawable_balance:
            return jsonify({"status": "error", "message": "Insufficient balance to stake."})

        # Weighted spin
        slots = [0.00, 0.50, 1.00, 1.20, 2.00]
        weights = [80, 80, 40, 4, 0]  # 2.00 almost never occurs

        result_multiplier = random.choices(slots, weights=weights, k=1)[0]
        earned = round(stake * result_multiplier, 2)

        # Record spin
        new_spin = Spin(user_id=user.id, stake=stake, reward=earned)
        db.session.add(new_spin)
        db.session.commit()

        # Update balance for frontend
        new_balance = withdrawable_balance - stake + earned

        return jsonify({"status": "success", "earned": earned, "balance": new_balance})

    return render_template('spin.html', user=user, min_stake=min_stake, withdrawable_balance=withdrawable_balance)


# ---------------- Bonus ----------------
@user_bp.route('/bonus')
@login_required
def bonus():
    user = current_user
    bonus_message = f"Hello {user.username}, sorry you have no bonuses. Kindly keep on referring people and get back later for a bonus."
    return render_template("bonus.html", bonus_message=bonus_message, user=user)
