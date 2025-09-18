from . import db
from flask_login import UserMixin
from datetime import datetime

# ---------------- User Model ----------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    mpesa_no = db.Column(db.String(15), nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # Referral fields
    referral_code = db.Column(db.String(50), nullable=True)
    referred_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    referrer_username = db.Column(db.String(50), nullable=True)

    status = db.Column(db.String(20), default='new')  # new, pending_approval, active, declined
    is_admin = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    payments = db.relationship('Payment', backref='user', lazy=True)
    referrals = db.relationship('User', backref=db.backref('referrer', remote_side=[id]), lazy='dynamic')
    withdrawals = db.relationship('Withdrawal', backref='user', lazy=True)
    trivia_answers = db.relationship('TriviaAnswer', backref='user', lazy=True)
    spins = db.relationship('Spin', backref='user', lazy=True)
    whatsapp_posts = db.relationship('WhatsAppPost', backref='user', lazy=True)

    def __repr__(self):
        return f"<User {self.username}>"

    @property
    def withdrawable_balance(self):
        """Compute withdrawable balance including spins"""
        total_payments = sum(p.amount for p in self.payments if p.status == 'approved')
        total_withdrawals = sum(w.amount for w in self.withdrawals if w.status == 'approved')
        total_spin_stakes = sum(s.stake for s in self.spins)
        total_spin_rewards = sum(s.reward for s in self.spins if s.reward > 0)
        trivia_earnings = sum(t.earned for t in self.trivia_answers)

        balance = total_payments + trivia_earnings + total_spin_rewards - total_withdrawals - total_spin_stakes
        return max(balance, 0)


# ---------------- Payment Model ----------------
class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    mpesa_code = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, declined
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Payment {self.id} - User {self.user_id} - {self.status}>"


# ---------------- Withdrawal Model ----------------
class Withdrawal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, declined
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Withdrawal {self.id} - User {self.user_id} - {self.status}>"


# ---------------- TriviaAnswer Model ----------------
class TriviaAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, nullable=False)
    answer = db.Column(db.String(200), nullable=False)
    correct = db.Column(db.Boolean, default=False)
    earned = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<TriviaAnswer User {self.user_id} Question {self.question_id} Earned {self.earned}>"


# ---------------- Spin Model ----------------
class Spin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stake = db.Column(db.Float, nullable=False)
    reward = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Spin User {self.user_id} Stake {self.stake} Reward {self.reward}>"


# ---------------- WhatsAppPost Model ----------------
class WhatsAppPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_views = db.Column(db.Integer, default=50)
    views_left = db.Column(db.Integer, default=50)
    earnings_per_view = db.Column(db.Float, default=20.0)
    total_earned = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<WhatsAppPost User {self.user_id} Views left {self.views_left}>"
