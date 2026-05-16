# 🚀 EduTube Summarizer - Deployment Guide

Deploy your EduTube Summarizer to **Streamlit Cloud** in minutes - completely free!

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Local Development](#local-development)
3. [Deploy to Streamlit Cloud](#deploy-to-streamlit-cloud)
4. [Troubleshooting](#troubleshooting)
5. [Advanced Deployment Options](#advanced-deployment-options)

---

## ⚡ Quick Start

### Option 1: Deploy to Streamlit Cloud (Recommended - FREE)

1. **Ensure your code is on GitHub**
   ```bash
   git add .
   git commit -m "Ready for Streamlit deployment"
   git push origin main
   ```

2. **Go to Streamlit Cloud**
   - Visit https://streamlit.io/cloud
   - Click **"Sign in with GitHub"**

3. **Deploy the App**
   - Click **"New app"**
   - Select:
     - Repository: `vasireddymiteshsai-ui/Edutube-summarizer-ui`
     - Branch: `main`
     - Main file path: `streamlit_app.py`
   - Click **"Deploy"**

4. **Your app is LIVE!** 🎉
   - URL: `https://{username}-{reponame}.streamlit.app/`

---

## 💻 Local Development

### Prerequisites
- Python 3.9 or higher
- pip (Python package manager)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/vasireddymiteshsai-ui/Edutube-summarizer-ui.git
   cd Edutube-summarizer-ui
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements-streamlit.txt
   ```

4. **Run the app locally**
   ```bash
   streamlit run streamlit_app.py
   ```

5. **Access the app**
   - Opens automatically at `http://localhost:8501`
   - Or manually visit: http://localhost:8501

---

## 🌐 Deploy to Streamlit Cloud

### Step-by-Step Instructions

#### 1. Create Streamlit Cloud Account

- Go to https://streamlit.io/cloud
- Click **"Sign in with GitHub"**
- Authorize Streamlit to access your GitHub account
- You'll be redirected to your Streamlit Cloud dashboard

#### 2. Deploy Your App

- Click **"New app"** button
- Fill in the deployment form:

| Field | Value |
|-------|-------|
| **Repository** | vasireddymiteshsai-ui/Edutube-summarizer-ui |
| **Branch** | main |
| **Main file path** | streamlit_app.py |

- Click **"Deploy"**
- Wait 1-2 minutes for deployment

#### 3. Monitor Deployment

- You'll see a "Building..." status
- Logs display in real-time
- Once complete, your app URL appears

#### 4. Access Your Live App

- **URL Format:** `https://{github-username}-{repo-name}.streamlit.app/`
- **Example:** `https://vasireddymiteshsai-ui-edutube-summarizer-ui.streamlit.app/`

### Share Your App

- Copy the URL from the browser bar
- Share with anyone - no installation needed!
- Use the **Share** button in top-right for additional options

---

## 🔧 Configuration

### Streamlit Configuration (`.streamlit/config.toml`)

Customize behavior:

```toml
[theme]
primaryColor = "#6C63FF"          # Purple accent color
backgroundColor = "#FFFFFF"       # White background
secondaryBackgroundColor = "#F0F2F6"  # Light gray sections
textColor = "#1a1a2e"            # Dark text

[client]
showErrorDetails = true           # Show detailed error messages
toolbarMode = "viewer"            # Minimal UI

[server]
headless = true                   # Required for cloud
maxUploadSize = 200               # Max upload: 200MB
enableXsrfProtection = true       # Security
```

---

## 🐛 Troubleshooting

### Issue: "Module not found" Error

**Problem:** `ModuleNotFoundError: No module named 'flask'`

**Solution:**
```bash
pip install -r requirements-streamlit.txt
streamlit run streamlit_app.py
```

### Issue: Database File Not Found

**Problem:** `FileNotFoundError: edutube.db`

**Solution:** The database is created automatically on first run. If you get this error:

1. Delete `.streamlit` cache:
   ```bash
   rm -rf ~/.streamlit/cache
   ```

2. Restart the app:
   ```bash
   streamlit run streamlit_app.py
   ```

### Issue: Streamlit Cloud Deployment Fails

**Problem:** Deploy button shows "Error" status

**Solutions:**
1. **Check `requirements-streamlit.txt`** - ensure all packages are listed
2. **Check main file path** - must be `streamlit_app.py` (not `app.py`)
3. **Check repository visibility** - must be **Public** on GitHub
4. **Check branch exists** - ensure `main` branch has all files

**To fix:**
```bash
# Verify files are committed
git status

# Push changes
git push origin main

# Try redeploying in Streamlit Cloud
# (Click "Redeploy" from app settings)
```

### Issue: Login Not Working

**Problem:** Can't create account or login

**Solution:**

1. **Clear session cache:**
   - Press `C` in Streamlit app (clears cache)
   - Or hard-refresh browser (Ctrl+Shift+R)

2. **Check database:**
   - Look for `edutube.db` file in project directory
   - If missing, it will be created on first run

3. **Verify credentials:**
   - Username must be unique
   - Password must be ≥4 characters

### Issue: PDF Download Not Working

**Problem:** Download button doesn't work on Streamlit Cloud

**Solution:** This is expected on mobile devices. Try on desktop, or:
- Use browser's download manager
- Check browser download folder

---

## 🚀 Advanced Deployment Options

### Alternative 1: Deploy to Heroku (Paid)

1. Install Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli
2. Create `Procfile`:
   ```
   web: streamlit run streamlit_app.py --server.port=$PORT
   ```
3. Deploy:
   ```bash
   heroku login
   heroku create your-app-name
   git push heroku main
   ```

### Alternative 2: Deploy to Railway.app

1. Sign up: https://railway.app
2. Connect GitHub repo
3. Set main command: `streamlit run streamlit_app.py`
4. Deploy!

### Alternative 3: Docker Deployment

1. Create `Dockerfile`:
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY . .
   RUN pip install -r requirements-streamlit.txt
   EXPOSE 8501
   CMD ["streamlit", "run", "streamlit_app.py"]
   ```

2. Build & run:
   ```bash
   docker build -t edutube .
   docker run -p 8501:8501 edutube
   ```

---

## 📊 Performance Tips

### Reduce Cold Start Time

Add to `.streamlit/config.toml`:
```toml
[client]
showErrorDetails = false

[logger]
level = "warning"
```

### Optimize Database Queries

The app uses SQLAlchemy with lazy loading - queries are optimized by default.

### Cache Summary Generation

Streamlit automatically caches expensive functions:
```python
@st.cache_resource
def get_db_connection():
    # Only called once per session
    pass
```

---

## 🔐 Security Considerations

### Passwords

- Passwords are hashed with **PBKDF2** (Werkzeug default)
- Never stored in plain text
- Safe even if database is leaked

### Session Management

- Streamlit session state stored in browser memory
- Cleared when user closes tab
- Secure for public deployments

### Database

- SQLite database stored in project directory
- **Backup important data** before redeploying
- For production, consider migrating to PostgreSQL

### Secrets (Optional)

For sensitive config, use Streamlit Secrets:

1. Create `.streamlit/secrets.toml`:
   ```toml
   DATABASE_URL = "your-postgres-url"
   API_KEY = "your-key"
   ```

2. In code:
   ```python
   db_url = st.secrets["DATABASE_URL"]
   ```

3. In Streamlit Cloud:
   - App settings → Secrets → Add your secrets

---

## 📞 Support & Resources

- **Streamlit Docs:** https://docs.streamlit.io
- **Streamlit Community:** https://discuss.streamlit.io
- **GitHub Issues:** https://github.com/vasireddymiteshsai-ui/Edutube-summarizer-ui/issues
- **My GitHub:** https://github.com/vasireddymiteshsai-ui

---

## ✅ Deployment Checklist

Before going live:

- [ ] All files pushed to GitHub (`main` branch)
- [ ] Repository is **Public**
- [ ] `requirements-streamlit.txt` has all dependencies
- [ ] `streamlit_app.py` is the main file
- [ ] `.streamlit/config.toml` exists and is configured
- [ ] Local testing passes: `streamlit run streamlit_app.py`
- [ ] No hardcoded secrets in code
- [ ] App has a description in README

---

## 🎉 You're All Set!

Your EduTube Summarizer is now deployed and accessible worldwide. Share the URL with friends, classmates, and colleagues!

**Enjoy! 📚✨**
