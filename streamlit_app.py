"""
streamlit_app.py — EduTube Summarizer (Streamlit Version)
=========================================================
Cloud-ready Streamlit app with all Flask functionality preserved.

Features:
  • User authentication (login/signup with password hashing)
  • SQLite database with SQLAlchemy ORM
  • Text summarization engine (same logic as Flask version)
  • Summary history management
  • Search functionality
  • PDF export
  • Session-based user state management

Deploy to Streamlit Cloud:
  1. Push this file to GitHub
  2. Go to https://streamlit.io/cloud
  3. Click "New app" → select repo & file
  4. Done! Your app is live
"""

import streamlit as st
import os
import sqlite3
from datetime import datetime
from pathlib import Path
import io

# Import summarization and PDF logic
from summarizer_logic import generate_summary, generate_summary_plain, generate_pdf

# SQLAlchemy imports
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from werkzeug.security import generate_password_hash, check_password_hash

# ════════════════════════════════════════════════════════════════════════════
#  DATABASE SETUP
# ════════════════════════════════════════════════════════════════════════════

# Create a minimal Flask app for SQLAlchemy (required for ORM)
app = Flask(__name__)
app.config['SECRET_KEY'] = 'edutube-streamlit-secret-key-2026'

# Database path - use Streamlit's cache directory if available
db_path = Path('.') / 'edutube.db'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# ════════════════════════════════════════════════════════════════════════════
#  DATABASE MODELS
# ════════════════════════════════════════════════════════════════════════════

class User(db.Model):
    """User table with one-to-many relationship to summaries."""
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    summaries = db.relationship('Summary', backref='author', lazy=True,
                               cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'


class Summary(db.Model):
    """Summary table - stores generated notes linked to users."""
    __tablename__ = 'summary'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    original_text = db.Column(db.Text, nullable=False)
    summary_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Summary {self.id} by User {self.user_id}>'


# Initialize database tables
with app.app_context():
    db.create_all()


# ════════════════════════════════════════════════════════════════════════════
#  SESSION STATE MANAGEMENT
# ════════════════════════════════════════════════════════════════════════════

def initialize_session():
    """Initialize Streamlit session state variables."""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'current_summary' not in st.session_state:
        st.session_state.current_summary = None
    if 'current_original' not in st.session_state:
        st.session_state.current_original = None
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ''


initialize_session()


# ════════════════════════════════════════════════════════════════════════════
#  AUTHENTICATION FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════

def signup_user(username: str, password: str, confirm_password: str) -> tuple:
    """
    Create a new user account.
    Returns: (success: bool, message: str)
    """
    with app.app_context():
        # Validation
        if not username or not password:
            return False, "Username and password are required."
        
        if len(password) < 4:
            return False, "Password must be at least 4 characters."
        
        if password != confirm_password:
            return False, "Passwords do not match."
        
        # Check if username exists
        existing = User.query.filter_by(username=username).first()
        if existing:
            return False, "Username already exists. Please choose another."
        
        # Create new user
        hashed = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed)
        
        db.session.add(new_user)
        db.session.commit()
        
        return True, "Account created successfully! Please log in."


def login_user(username: str, password: str) -> tuple:
    """
    Authenticate a user.
    Returns: (success: bool, user_id: int or None, message: str)
    """
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            return True, user.id, f"Welcome back, {user.username}!"
        else:
            return False, None, "Invalid username or password."


def logout_user():
    """Clear session and logout."""
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.current_summary = None


# ════════════════════════════════════════════════════════════════════════════
#  SUMMARY FUNCTIONS
# ═══════════════════════════════════════════════════���════════════════════════

def get_user_summaries(user_id: int, search_query: str = '') -> list:
    """Fetch user's summaries, optionally filtered by search query."""
    with app.app_context():
        if search_query:
            summaries = Summary.query.filter(
                Summary.user_id == user_id,
                Summary.summary_text.contains(search_query)
            ).order_by(Summary.created_at.desc()).all()
        else:
            summaries = Summary.query.filter_by(
                user_id=user_id
            ).order_by(Summary.created_at.desc()).all()
        
        return summaries


def create_summary(user_id: int, original_text: str) -> tuple:
    """
    Generate and save a summary.
    Returns: (success: bool, summary_id: int or None, html_summary: str, message: str)
    """
    with app.app_context():
        if not original_text.strip():
            return False, None, None, "Please paste some text to summarise."
        
        try:
            # Generate summaries (HTML and plain text versions)
            summary_html = generate_summary(original_text)
            summary_plain = generate_summary_plain(original_text)
            
            # Save to database
            new_summary = Summary(
                user_id=user_id,
                original_text=original_text,
                summary_text=summary_plain
            )
            db.session.add(new_summary)
            db.session.commit()
            
            summary_id = new_summary.id
            
            return True, summary_id, summary_html, "Summary created successfully!"
        
        except Exception as e:
            return False, None, None, f"Error: {str(e)}"


def delete_summary(summary_id: int, user_id: int) -> tuple:
    """Delete a summary if it belongs to the user."""
    with app.app_context():
        summary = Summary.query.get(summary_id)
        
        if not summary:
            return False, "Summary not found."
        
        if summary.user_id != user_id:
            return False, "Access denied."
        
        db.session.delete(summary)
        db.session.commit()
        
        return True, "Summary deleted."


def get_summary_by_id(summary_id: int, user_id: int):
    """Fetch a specific summary if it belongs to the user."""
    with app.app_context():
        summary = Summary.query.get(summary_id)
        
        if not summary or summary.user_id != user_id:
            return None
        
        return summary


# ════════════════════════════════════════════════════════════════════════════
#  PAGE: LOGIN / SIGNUP
# ════════════════════════════════════════════════════════════════════════════

def page_auth():
    """Login and signup page."""
    st.set_page_config(page_title="EduTube Summarizer", layout="centered")
    
    # Sidebar branding
    with st.sidebar:
        st.markdown("### 📚 EduTube Summarizer")
        st.markdown("Transform your video transcripts into structured study notes")
    
    # Tabs for login/signup
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.markdown("## Welcome Back! 👋")
        
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", use_container_width=True, type="primary"):
            success, user_id, message = login_user(username, password)
            
            if success:
                st.session_state.user_id = user_id
                st.session_state.username = username
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    
    with tab2:
        st.markdown("## Create Your Account 🚀")
        
        username = st.text_input("Choose a Username", key="signup_username")
        password = st.text_input("Create Password", type="password", key="signup_password")
        confirm = st.text_input("Confirm Password", type="password", key="signup_confirm")
        
        if st.button("Sign Up", use_container_width=True, type="primary"):
            success, message = signup_user(username, password, confirm)
            
            if success:
                st.success(message)
            else:
                st.error(message)


# ════════════════════════════════════════════════════════════════════════════
#  PAGE: DASHBOARD
# ════════════════════════════════════════════════════════════════════════════

def page_dashboard():
    """Main dashboard with text input and summary display."""
    st.set_page_config(page_title="Dashboard - EduTube", layout="wide")
    
    # Header
    col1, col2 = st.columns([0.85, 0.15])
    with col1:
        st.markdown("## 📝 EduTube Summarizer")
        st.markdown(f"**Welcome, {st.session_state.username}!**")
    with col2:
        if st.button("🚪 Logout", use_container_width=True):
            logout_user()
            st.rerun()
    
    st.divider()
    
    # Sidebar: History & Search
    with st.sidebar:
        st.markdown("### 📚 Your Summaries")
        
        # Search box
        search_query = st.text_input("Search summaries...", 
                                     value=st.session_state.search_query,
                                     key="search_input")
        st.session_state.search_query = search_query
        
        # Fetch summaries
        summaries = get_user_summaries(st.session_state.user_id, search_query)
        
        if summaries:
            st.markdown(f"**Found: {len(summaries)} summary/summaries**")
            st.divider()
            
            for summary in summaries:
                # Truncate original text for preview
                preview = summary.original_text[:50] + "..." if len(summary.original_text) > 50 else summary.original_text
                
                with st.container(border=True):
                    st.markdown(f"**{preview}**")
                    st.caption(summary.created_at.strftime("%d %b %Y, %I:%M %p"))
                    
                    col1, col2, col3 = st.columns([0.5, 0.25, 0.25])
                    with col1:
                        if st.button("📖 View", key=f"view_{summary.id}", use_container_width=True):
                            st.session_state.current_summary = summary.id
                            st.rerun()
                    with col2:
                        if st.button("📥 PDF", key=f"pdf_{summary.id}", use_container_width=True):
                            pdf_bytes = generate_pdf(
                                summary.original_text,
                                summary.summary_text,
                                st.session_state.username
                            )
                            st.download_button(
                                label="Download",
                                data=pdf_bytes,
                                file_name=f"edutube_notes_{summary.id}.pdf",
                                mime="application/pdf",
                                key=f"download_{summary.id}"
                            )
                    with col3:
                        if st.button("🗑️", key=f"delete_{summary.id}", use_container_width=True):
                            success, msg = delete_summary(summary.id, st.session_state.user_id)
                            if success:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
        else:
            st.info("No summaries yet. Create one to get started!")
    
    # Main area: Input & Display
    tab1, tab2 = st.tabs(["Create New", "View Selected"])
    
    with tab1:
        st.markdown("### Paste Your Text Here")
        original_text = st.text_area(
            "Enter text to summarize:",
            height=300,
            placeholder="Paste your video transcript, article, or notes here...",
            key="text_input"
        )
        
        col1, col2 = st.columns([0.6, 0.4])
        with col1:
            if st.button("✨ Generate Summary", use_container_width=True, type="primary"):
                if original_text.strip():
                    with st.spinner("Generating summary..."):
                        success, summary_id, summary_html, message = create_summary(
                            st.session_state.user_id,
                            original_text
                        )
                        
                        if success:
                            st.session_state.current_summary = summary_id
                            st.session_state.current_original = original_text
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                else:
                    st.warning("Please enter some text to summarize.")
    
    with tab2:
        if st.session_state.current_summary:
            summary = get_summary_by_id(st.session_state.current_summary, 
                                       st.session_state.user_id)
            
            if summary:
                st.markdown("### 📋 Generated Summary")
                
                col1, col2 = st.columns([0.7, 0.3])
                with col2:
                    pdf_bytes = generate_pdf(
                        summary.original_text,
                        summary.summary_text,
                        st.session_state.username
                    )
                    st.download_button(
                        label="⬇️ Download as PDF",
                        data=pdf_bytes,
                        file_name=f"edutube_notes_{summary.id}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                
                # Display summary HTML
                summary_html = generate_summary(summary.original_text)
                st.markdown(summary_html, unsafe_allow_html=True)
                
                st.divider()
                st.markdown("### 📄 Original Text")
                st.text_area("Original text:", value=summary.original_text, 
                            height=200, disabled=True)
        else:
            st.info("👈 Select a summary from the sidebar or create a new one!")


# ════════════════════════════════════════════════════════════════════════════
#  PAGE ROUTER
# ════════════════════════════════════════════════════════════════════════════

def main():
    """Main entry point - routes to correct page."""
    if st.session_state.user_id:
        page_dashboard()
    else:
        page_auth()


if __name__ == "__main__":
    main()
