"""
app.py — EduTube Summarizer (Main Flask Application)
=====================================================
This file contains:
  1. Flask app configuration & SQLite database setup
  2. SQLAlchemy ORM models (User, Summary) with One-to-Many relationship
  3. All routes: authentication, dashboard, search, PDF export

DBMS Concepts Demonstrated:
  • Relational Schema Design (Primary Keys, Foreign Keys)
  • One-to-Many Relationship (User → Summaries)
  • CRUD Operations via SQLAlchemy ORM
  • SQL LIKE operator for search functionality
  • Referential Integrity via ForeignKey constraints
"""

# ── Imports ──────────────────────────────────────────────────────────────
import os
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, send_file
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Import our custom modules
from summarizer_logic import generate_summary, generate_summary_plain, generate_pdf

import io  # For serving PDF bytes as file download


# ═══════════════════════════════════════════════════════════════════════════
#  APP CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

app = Flask(__name__)

# Secret key for session management (cookie signing)
app.config['SECRET_KEY'] = 'edutube-dbms-project-2026-secret-key'

# ── SQLite Database Configuration ────────────────────────────────────────
# SQLite stores the entire database in a single file.
# This is ideal for academic projects — no server setup needed.
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'edutube.db')

# Disable modification tracking (saves memory, not needed here)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialise SQLAlchemy — this connects Flask with the SQLite database
db = SQLAlchemy(app)


# ═══════════════════════════════════════════════════════════════════════════
#  DATABASE MODELS (ORM — Object Relational Mapping)
# ═══════════════════════════════════════════════════════════════════════════
#
# DBMS CONCEPT: Entity-Relationship Mapping
# ──────────────────────────────────────────
#   User  ──(1)────(M)──  Summary
#
#   One User can have MANY Summaries   → One-to-Many relationship
#   Each Summary belongs to ONE User   → Foreign Key constraint
#


class User(db.Model):
    """
    USER TABLE
    ──────────
    Stores registered user accounts.

    Columns:
      id            — INTEGER, Primary Key (auto-increment)
      username      — VARCHAR, Unique, Not Null
      password_hash — VARCHAR, Not Null (stores hashed password, NEVER plaintext)

    Relationship:
      summaries — One-to-Many link to Summary table (backref)
    """
    __tablename__ = 'user'  # Explicit table name

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    # One-to-Many: A user can have many summaries
    # backref='author' creates a reverse reference: summary.author → User
    # lazy=True means summaries are loaded on first access (lazy loading)
    summaries = db.relationship('Summary', backref='author', lazy=True,
                                cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.username}>'


class Summary(db.Model):
    """
    SUMMARY TABLE
    ─────────────
    Stores generated summaries linked to users.

    Columns:
      id            — INTEGER, Primary Key (auto-increment)
      user_id       — INTEGER, Foreign Key → user.id (enforces referential integrity)
      original_text — TEXT, Not Null (the input text)
      summary_text  — TEXT, Not Null (the generated summary)
      created_at    — DATETIME, defaults to current UTC time

    DBMS Concepts:
      • Foreign Key ensures every summary is linked to a valid user
      • CASCADE delete: if a user is deleted, their summaries are also removed
    """
    __tablename__ = 'summary'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # FOREIGN KEY — links each summary to its owner
    # This enforces REFERENTIAL INTEGRITY at the database level
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    original_text = db.Column(db.Text, nullable=False)
    summary_text = db.Column(db.Text, nullable=False)

    # Default timestamp — automatically set when a record is created
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Summary {self.id} by User {self.user_id}>'


# ═══════════════════════════════════════════════════════════════════════════
#  HELPER — Login Required Decorator (simplified)
# ═══════════════════════════════════════════════════════════════════════════

def login_required(f):
    """
    Custom decorator to protect routes.
    Checks if 'user_id' exists in the Flask session.
    If not, redirects to the login page.
    """
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


# ═══════════════════════════════════════════════════════════════════════════
#  ROUTES — AUTHENTICATION
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    """Root route — redirect to dashboard if logged in, else to login."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    SIGNUP ROUTE
    ────────────
    GET  → Render signup form
    POST → Validate input, hash password, INSERT new user into database

    DBMS Operations:
      • SELECT (check if username already exists)
      • INSERT (add new user record)
      • COMMIT (save transaction)
    """
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm  = request.form.get('confirm_password', '').strip()

        # ── Validation ───────────────────────────────────────────────
        if not username or not password:
            flash('Username and password are required.', 'danger')
            return redirect(url_for('signup'))

        if len(password) < 4:
            flash('Password must be at least 4 characters.', 'danger')
            return redirect(url_for('signup'))

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('signup'))

        # SELECT — check if username is already taken
        existing = User.query.filter_by(username=username).first()
        if existing:
            flash('Username already exists. Please choose another.', 'danger')
            return redirect(url_for('signup'))

        # ── Create new user ──────────────────────────────────────────
        # werkzeug.security.generate_password_hash uses PBKDF2 by default
        hashed = generate_password_hash(password)

        new_user = User(username=username, password_hash=hashed)

        # INSERT into database & COMMIT transaction
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('login.html', mode='signup')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    LOGIN ROUTE
    ───────────
    GET  → Render login form
    POST → SELECT user by username, verify password hash, create session

    DBMS Operations:
      • SELECT with WHERE clause (find user by username)
    """
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        # SELECT — find user by username
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            # Create session — store user ID in a signed cookie
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html', mode='login')


@app.route('/logout')
def logout():
    """Clear session data and redirect to login."""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# ═══════════════════════════════════════════════════════════════════════════
#  ROUTES — DASHBOARD & CORE FUNCTIONALITY
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/dashboard')
@login_required
def dashboard():
    """
    DASHBOARD ROUTE
    ───────────────
    Displays the main split-screen workspace.

    DBMS Operations:
      • SELECT with WHERE + ORDER BY
        (fetch all summaries for the logged-in user, newest first)

    The Jinja2 template iterates over summaries to populate the sidebar.
    """
    # SELECT * FROM summary WHERE user_id = ? ORDER BY created_at DESC
    user_summaries = Summary.query.filter_by(
        user_id=session['user_id']
    ).order_by(Summary.created_at.desc()).all()

    return render_template('dashboard.html', summaries=user_summaries)


@app.route('/summarize', methods=['POST'])
@login_required
def summarize():
    """
    SUMMARIZE ROUTE
    ───────────────
    Receives text from the dashboard textarea, generates a summary,
    INSERTs the result into the database, and re-renders the dashboard.

    DBMS Operations:
      • INSERT (save new summary record)
      • COMMIT (persist the transaction)
      • SELECT (reload summaries for sidebar)
    """
    original_text = request.form.get('original_text', '').strip()

    if not original_text:
        flash('Please paste some text to summarise.', 'warning')
        return redirect(url_for('dashboard'))

    # Generate summary using our extractive algorithm
    # HTML version for dashboard display (with headings, bullets, highlights)
    summary_html = generate_summary(original_text)
    # Plain-text version for database storage (used in search & PDF export)
    summary_plain = generate_summary_plain(original_text)

    # INSERT — save to database (plain text for searchability via SQL LIKE)
    new_summary = Summary(
        user_id=session['user_id'],
        original_text=original_text,
        summary_text=summary_plain
    )
    db.session.add(new_summary)
    db.session.commit()

    # Reload summaries for sidebar display
    user_summaries = Summary.query.filter_by(
        user_id=session['user_id']
    ).order_by(Summary.created_at.desc()).all()

    return render_template(
        'dashboard.html',
        summaries=user_summaries,
        current_summary=summary_html,
        current_original=original_text,
        summary_id=new_summary.id
    )


@app.route('/search')
@login_required
def search():
    """
    SEARCH ROUTE
    ────────────
    Uses the SQL LIKE operator to filter summaries by keyword.

    DBMS Concept:
      • SQL LIKE with wildcards: WHERE summary_text LIKE '%keyword%'
      • This demonstrates pattern matching in relational databases.
    """
    query = request.args.get('q', '').strip()

    if query:
        # SQL LIKE operator — % is a wildcard matching any sequence of characters
        # SQLAlchemy .contains() translates to: WHERE column LIKE '%value%'
        user_summaries = Summary.query.filter(
            Summary.user_id == session['user_id'],
            Summary.summary_text.contains(query)
        ).order_by(Summary.created_at.desc()).all()
    else:
        user_summaries = Summary.query.filter_by(
            user_id=session['user_id']
        ).order_by(Summary.created_at.desc()).all()

    return render_template(
        'dashboard.html',
        summaries=user_summaries,
        search_query=query
    )


@app.route('/download_pdf/<int:summary_id>')
@login_required
def download_pdf(summary_id):
    """
    PDF EXPORT ROUTE
    ────────────────
    Fetches a summary from the database and generates a downloadable PDF.

    DBMS Operations:
      • SELECT with WHERE (fetch specific summary by ID)
      • Access control: verify the summary belongs to the logged-in user
    """
    # SELECT — fetch summary by primary key
    summary = Summary.query.get_or_404(summary_id)

    # Security check — ensure user owns this summary
    if summary.user_id != session['user_id']:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))

    # Generate PDF bytes using ReportLab
    pdf_bytes = generate_pdf(
        original_text=summary.original_text,
        summary_text=summary.summary_text,
        username=session['username']
    )

    # Serve PDF as downloadable file
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'edutube_notes_{summary.id}.pdf'
    )


@app.route('/delete/<int:summary_id>', methods=['POST'])
@login_required
def delete_summary(summary_id):
    """
    DELETE ROUTE
    ────────────
    Removes a summary from the database.

    DBMS Operations:
      • SELECT (find the record)
      • DELETE (remove the record)
      • COMMIT (persist the change)
    """
    summary = Summary.query.get_or_404(summary_id)

    if summary.user_id != session['user_id']:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))

    db.session.delete(summary)
    db.session.commit()
    flash('Note deleted.', 'info')
    return redirect(url_for('dashboard'))


# ═══════════════════════════════════════════════════════════════════════════
#  DATABASE INITIALISATION & APP STARTUP
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    # Create all tables if they don't exist
    # This is equivalent to running CREATE TABLE IF NOT EXISTS for each model
    with app.app_context():
        db.create_all()
        print("[OK] Database tables created (if not already present).")

    # Run the Flask development server
    # debug=True enables auto-reload and detailed error pages
    app.run(debug=True, port=5000)
