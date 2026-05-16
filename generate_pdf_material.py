import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, ListFlowable, ListItem

def create_reading_material_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        title="EduTube Summarizer - Reading Material",
        author="System"
    )

    styles = getSampleStyleSheet()

    PRIMARY = HexColor("#6C63FF")
    DARK = HexColor("#1a1a2e")
    TEXT_CLR = HexColor("#2d2d2d")

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        textColor=PRIMARY,
        spaceAfter=8 * mm,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
    )

    heading1_style = ParagraphStyle(
        'Heading1',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=DARK,
        spaceBefore=10 * mm,
        spaceAfter=6 * mm,
        fontName='Helvetica-Bold',
        borderPadding=4,
        borderWidth=0,
        borderColor=PRIMARY,
    )

    heading2_style = ParagraphStyle(
        'Heading2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=PRIMARY,
        spaceBefore=6 * mm,
        spaceAfter=4 * mm,
        fontName='Helvetica-Bold',
    )

    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['BodyText'],
        fontSize=11,
        textColor=TEXT_CLR,
        leading=16,
        alignment=TA_JUSTIFY,
        spaceAfter=4 * mm,
    )
    
    bullet_style = ParagraphStyle(
        'BulletText',
        parent=styles['BodyText'],
        fontSize=11,
        textColor=TEXT_CLR,
        leading=16,
        alignment=TA_LEFT,
        spaceAfter=2 * mm,
    )

    story = []

    # Title
    story.append(Paragraph("EduTube Summarizer", title_style))
    story.append(Paragraph("Project Documentation & Reading Material", ParagraphStyle('Sub', parent=styles['Normal'], fontSize=14, textColor=HexColor("#888888"), alignment=TA_CENTER, spaceAfter=12 * mm)))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2 * mm, spaceAfter=8 * mm))

    # Section 1: Overall System Flow
    story.append(Paragraph("1. Overall System Flow (Application Cycle)", heading1_style))
    story.append(Paragraph("The application follows a standard Client-Server architecture with a Flask backend. The cycle operates as follows:", body_style))
    
    flow_steps = [
        "<b>User Access & Authentication:</b> The user accesses the web application. If they are not logged in, they are redirected to the Login/Signup page.",
        "<b>Dashboard Workspace:</b> Once authenticated, the Flask backend creates a secure session and serves the Dashboard.",
        "<b>Text Input & Processing:</b> The user pastes text and submits it. The Flask route (/summarize) intercepts this POST request and passes the raw text to the 'summarizer_logic.py' engine.",
        "<b>Summarization Engine:</b> The text undergoes cleaning, tokenization, stopword filtering, word-frequency scoring, and topic clustering.",
        "<b>Database Storage:</b> The generated plain-text structured notes and the original text are stored in the SQLite database via SQLAlchemy, linked to the user's ID via a Foreign Key.",
        "<b>UI Update:</b> The dashboard reloads, displaying the HTML-formatted structured notes and updating the History sidebar."
    ]
    
    story.append(ListFlowable([ListItem(Paragraph(step, bullet_style)) for step in flow_steps], bulletType='bullet', start='circle'))
    story.append(Spacer(1, 6 * mm))

    # Section 2: Database Logic Cycle
    story.append(Paragraph("2. Database Logic Cycle", heading1_style))
    story.append(Paragraph("The project demonstrates core Relational Database Management System (RDBMS) concepts, primarily focusing on Entity-Relationship mapping, referential integrity, and CRUD operations.", body_style))
    
    story.append(Paragraph("Database Models:", heading2_style))
    db_models = [
        "<b>User Table:</b> Contains 'id' (Primary Key), 'username' (Unique string), and 'password_hash'.",
        "<b>Summary Table:</b> Contains 'id' (Primary Key), 'user_id' (Foreign Key referencing User.id), 'original_text', 'summary_text', and 'created_at'."
    ]
    story.append(ListFlowable([ListItem(Paragraph(model, bullet_style)) for model in db_models], bulletType='bullet', start='circle'))
    
    story.append(Paragraph("Database Operations Lifecycle:", heading2_style))
    crud_steps = [
        "<b>Registration (INSERT):</b> Executes an INSERT query to create a new user record. A uniqueness constraint prevents duplicate usernames.",
        "<b>Authentication (SELECT):</b> Uses a SELECT query with a WHERE clause to fetch user details and verify the hashed password.",
        "<b>Data Creation (INSERT + FK):</b> When a note is generated, an INSERT query stores it. The Foreign Key 'user_id' enforces Referential Integrity.",
        "<b>Data Retrieval (SELECT + ORDER BY):</b> The sidebar history is populated using a SELECT query sorted by the 'created_at' timestamp in descending order.",
        "<b>Data Filtering (SQL LIKE):</b> The search functionality utilizes the SQL LIKE operator (e.g., WHERE summary_text LIKE '%keyword%') for pattern matching.",
        "<b>Data Deletion (DELETE + CASCADE):</b> Users can delete specific notes. If a user account is deleted, the CASCADE rule automatically deletes all their linked notes, preventing orphaned records."
    ]
    story.append(ListFlowable([ListItem(Paragraph(step, bullet_style)) for step in crud_steps], bulletType='bullet', start='circle'))
    story.append(Spacer(1, 6 * mm))

    # Section 3: Reading Material: Key Concepts
    story.append(Paragraph("3. Reading Material: Key Concepts", heading1_style))
    
    story.append(Paragraph("Extractive Text Summarization", heading2_style))
    story.append(Paragraph("The core engine relies on Extractive Summarization. Unlike generative AI, our algorithm identifies and extracts the most important existing sentences from the text based on statistical properties.", body_style))
    
    nlp_steps = [
        "<b>Stopword Filtering:</b> Common words (like 'the', 'and', 'is') are removed because they lack semantic value.",
        "<b>Word-Frequency Scoring:</b> Words that appear frequently (after stopword removal) indicate the main topics. Sentences containing many high-frequency words receive a higher score.",
        "<b>Clustering:</b> By identifying the 'dominant keyword' in a high-scoring sentence, the algorithm groups related sentences into thematic sections."
    ]
    story.append(ListFlowable([ListItem(Paragraph(step, bullet_style)) for step in nlp_steps], bulletType='bullet', start='circle'))
    
    story.append(Paragraph("Relational Database Management Systems (RDBMS)", heading2_style))
    rdbms_concepts = [
        "<b>Primary Keys (PK):</b> Unique identifiers for each record.",
        "<b>Foreign Keys (FK):</b> A column linking to the primary key of another table, ensuring referential integrity.",
        "<b>One-to-Many Relationship:</b> One User can be associated with multiple Summaries, but each Summary belongs to exactly one User.",
        "<b>Object-Relational Mapping (ORM):</b> We use Flask-SQLAlchemy, an ORM that allows interaction with the SQL database using Python classes instead of writing raw SQL strings, enhancing security against SQL injection."
    ]
    story.append(ListFlowable([ListItem(Paragraph(concept, bullet_style)) for concept in rdbms_concepts], bulletType='bullet', start='circle'))
    
    story.append(Paragraph("Flask Web Framework", heading2_style))
    flask_concepts = [
        "<b>Routing:</b> Mapping URLs (like /dashboard) to Python functions.",
        "<b>Jinja2 Templating:</b> Dynamically generating HTML by injecting variables and using loops (e.g., looping over database results to render the history sidebar).",
        "<b>Session Management:</b> Storing user state securely in signed browser cookies to keep users logged in."
    ]
    story.append(ListFlowable([ListItem(Paragraph(concept, bullet_style)) for concept in flask_concepts], bulletType='bullet', start='circle'))

    # Footer
    story.append(Spacer(1, 12 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#cccccc"), spaceBefore=2 * mm, spaceAfter=4 * mm))
    story.append(Paragraph("EduTube Summarizer • DBMS Academic Project Reading Material", ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, textColor=HexColor("#aaaaaa"), alignment=TA_CENTER)))

    doc.build(story)
    print(f"PDF generated successfully at {output_path}")

if __name__ == "__main__":
    output_pdf_path = os.path.join(os.path.dirname(__file__), "EduTube_Summarizer_Reading_Material.pdf")
    create_reading_material_pdf(output_pdf_path)
