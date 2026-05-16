"""
summarizer_logic.py — EduTube Summarizer
========================================
Module 1: Extractive Text Summarisation (pure Python, no ML)
Module 2: PDF Report Generation (ReportLab)

Algorithm — Word-Frequency Scoring:
  1. Clean input → remove extra whitespace
  2. Split into sentences
  3. Remove stopwords, count word frequencies (collections.Counter)
  4. Score each sentence = sum(word_freq) / sentence_length
  5. Return top-7 sentences in original order
"""

import re
from collections import Counter
import io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable


# ═══════════════════════════════════════════════════════════════════
#  STOPWORDS — common English words with little semantic meaning
# ═══════════════════════════════════════════════════════════════════

STOPWORDS = {
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves",
    "you", "your", "yours", "yourself", "yourselves",
    "he", "him", "his", "himself", "she", "her", "hers", "herself",
    "it", "its", "itself", "they", "them", "their", "theirs", "themselves",
    "what", "which", "who", "whom", "this", "that", "these", "those",
    "am", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "having", "do", "does", "did", "doing",
    "a", "an", "the", "and", "but", "if", "or", "because", "as",
    "until", "while", "of", "at", "by", "for", "with", "about",
    "against", "between", "through", "during", "before", "after",
    "above", "below", "to", "from", "up", "down", "in", "out",
    "on", "off", "over", "under", "again", "further", "then", "once",
    "here", "there", "when", "where", "why", "how", "all", "both",
    "each", "few", "more", "most", "other", "some", "such", "no",
    "nor", "not", "only", "own", "same", "so", "than", "too",
    "very", "s", "t", "can", "will", "just", "don", "should", "now",
    "also", "would", "could", "may", "might", "shall", "must",
    "yet", "still", "already", "even", "much", "many", "every",
}


# ═══════════════════════════════════════════════════════════════════
#  SECTION 1 — TEXT SUMMARISATION (Structured Notes Engine)
# ═══════════════════════════════════════════════════════════════════

def clean_text(text: str) -> str:
    """Collapse whitespace and strip edges."""
    return re.sub(r'\s+', ' ', text).strip()


def tokenize_sentences(text: str) -> list:
    """Split text into sentences on . ! ? followed by space."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def get_word_frequencies(sentences: list) -> Counter:
    """
    Build a word-frequency table from all sentences.
    Filters stopwords so only content-bearing words remain.
    Uses collections.Counter — O(n) frequency counting.
    (DBMS analogy: SELECT word, COUNT(*) GROUP BY word)
    """
    all_words = re.findall(r'\b[a-z]+\b', ' '.join(sentences).lower())
    filtered = [w for w in all_words if w not in STOPWORDS]
    return Counter(filtered)


def score_sentences(sentences: list, word_freq: Counter) -> dict:
    """
    Score each sentence by normalised word-frequency.
    Score = sum(freq of each word) / number of words in sentence.
    """
    scores = {}
    for idx, sent in enumerate(sentences):
        words = re.findall(r'\b[a-z]+\b', sent.lower())
        if words:
            scores[idx] = sum(word_freq.get(w, 0) for w in words) / len(words)
        else:
            scores[idx] = 0
    return scores


def get_dominant_keyword(sentence: str, word_freq: Counter) -> str:
    """
    Find the most important (highest-frequency) content word in a sentence.
    Used to cluster sentences under topic headings.
    """
    words = re.findall(r'\b[a-z]+\b', sentence.lower())
    content_words = [w for w in words if w not in STOPWORDS]
    if not content_words:
        return "general"
    # Return the word with the highest frequency in the overall text
    return max(content_words, key=lambda w: word_freq.get(w, 0))


def cluster_sentences_by_topic(sentences: list, indices: list,
                                word_freq: Counter) -> dict:
    """
    Group selected sentences into topic clusters based on their
    dominant keyword. This creates logical sections in the notes.

    Returns: dict  { "topic_keyword": [sentence1, sentence2, ...] }
    """
    clusters = {}
    for idx in indices:
        keyword = get_dominant_keyword(sentences[idx], word_freq)
        if keyword not in clusters:
            clusters[keyword] = []
        clusters[keyword].append(sentences[idx])
    return clusters


def format_topic_heading(keyword: str) -> str:
    """
    Turn a raw keyword into a readable section heading.
    e.g. "learning" → "Learning", "data" → "Data"
    """
    return keyword.capitalize()


def generate_summary(text: str, num_sentences: int = 7) -> str:
    """
    Structured Notes Generator.

    Pipeline:
      1. Clean & tokenize text into sentences
      2. Build word-frequency table (collections.Counter)
      3. Score & rank sentences by importance
      4. Cluster top sentences by dominant keyword → topic sections
      5. Format as structured HTML notes with headings & bullet points

    Returns HTML string ready for rendering in the dashboard.
    """
    cleaned = clean_text(text)
    if not cleaned:
        return "Please provide some text to summarise."

    sentences = tokenize_sentences(cleaned)
    total_sentences = len(sentences)
    total_words = len(cleaned.split())

    # For very short texts, return a simple formatted version
    if total_sentences <= 3:
        return (
            '<div class="structured-notes">'
            '<div class="notes-section">'
            '<h6 class="section-heading">Key Points</h6>'
            '<ul class="notes-list">'
            + ''.join(f'<li>{s}</li>' for s in sentences)
            + '</ul></div></div>'
        )

    # ── Step 1: Build word frequencies ───────────────────────────
    word_freq = get_word_frequencies(sentences)

    # ── Step 2: Score & rank sentences ───────────────────────────
    scores = score_sentences(sentences, word_freq)

    # Select top-N sentences (pick more for longer texts)
    pick_count = min(num_sentences, total_sentences - 1)
    top_indices = sorted(scores, key=scores.get, reverse=True)[:pick_count]
    top_indices.sort()  # Preserve reading order within clusters

    # ── Step 3: Identify top keywords for the overview ───────────
    top_keywords = [kw for kw, _ in word_freq.most_common(5)]

    # ── Step 4: Cluster sentences by topic ───────────────────────
    clusters = cluster_sentences_by_topic(sentences, top_indices, word_freq)

    # ── Step 5: Build structured HTML output ─────────────────────
    html_parts = ['<div class="structured-notes">']

    # --- Overview banner ---
    html_parts.append(
        '<div class="notes-overview">'
        f'<span class="overview-stat"><i class="bi bi-card-text"></i> {total_words} words</span>'
        f'<span class="overview-stat"><i class="bi bi-list-ol"></i> {total_sentences} sentences</span>'
        f'<span class="overview-stat"><i class="bi bi-bookmark-star"></i> {pick_count} key points</span>'
        '</div>'
    )

    # --- Topic tags ---
    html_parts.append('<div class="topic-tags">')
    for kw in top_keywords:
        html_parts.append(f'<span class="topic-tag">{kw}</span>')
    html_parts.append('</div>')

    # --- Clustered sections ---
    section_num = 0
    for keyword, sents in clusters.items():
        section_num += 1
        heading = format_topic_heading(keyword)
        html_parts.append(
            f'<div class="notes-section">'
            f'<h6 class="section-heading">'
            f'<span class="section-number">{section_num}</span>'
            f'{heading}</h6>'
            f'<ul class="notes-list">'
        )
        for sent in sents:
            # Highlight the topic keyword in each bullet point
            highlighted = re.sub(
                rf'\b({re.escape(keyword)})\b',
                r'<mark>\1</mark>',
                sent,
                flags=re.IGNORECASE
            )
            html_parts.append(f'<li>{highlighted}</li>')
        html_parts.append('</ul></div>')

    html_parts.append('</div>')

    return '\n'.join(html_parts)


def generate_summary_plain(text: str, num_sentences: int = 7) -> str:
    """
    Plain-text version of the summary (used for PDF export and search).
    Same algorithm, but returns clean text instead of HTML.
    """
    cleaned = clean_text(text)
    if not cleaned:
        return "Please provide some text to summarise."

    sentences = tokenize_sentences(cleaned)

    if len(sentences) <= 3:
        return '\n'.join(f'* {s}' for s in sentences)

    word_freq = get_word_frequencies(sentences)
    scores = score_sentences(sentences, word_freq)

    pick_count = min(num_sentences, len(sentences) - 1)
    top_indices = sorted(scores, key=scores.get, reverse=True)[:pick_count]
    top_indices.sort()

    clusters = cluster_sentences_by_topic(sentences, top_indices, word_freq)

    lines = []
    for keyword, sents in clusters.items():
        lines.append(f'\n[ {format_topic_heading(keyword)} ]')
        for sent in sents:
            lines.append(f'  * {sent}')

    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════════
#  SECTION 2 — PDF GENERATION (ReportLab)
# ═══════════════════════════════════════════════════════════════════

PRIMARY = HexColor("#6C63FF")
DARK    = HexColor("#1a1a2e")

def generate_pdf(original_text: str, summary_text: str, username: str) -> bytes:
    """
    Build a styled PDF report and return it as bytes.
    Used by the /download_pdf route to serve the file.
    """
    buf = io.BytesIO()

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=2*cm, bottomMargin=2*cm,
        leftMargin=2*cm, rightMargin=2*cm,
        title="EduTube Smart Notes", author=username,
    )

    styles = getSampleStyleSheet()

    title_s = ParagraphStyle('T', parent=styles['Title'], fontSize=22,
                             textColor=PRIMARY, spaceAfter=6*mm,
                             alignment=TA_CENTER, fontName='Helvetica-Bold')

    sub_s = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=10,
                           textColor=HexColor("#888"), alignment=TA_CENTER,
                           spaceAfter=8*mm)

    head_s = ParagraphStyle('H', parent=styles['Heading2'], fontSize=14,
                            textColor=DARK, spaceBefore=6*mm, spaceAfter=4*mm,
                            fontName='Helvetica-Bold')

    body_s = ParagraphStyle('B', parent=styles['BodyText'], fontSize=10,
                            textColor=HexColor("#2d2d2d"), leading=15,
                            alignment=TA_JUSTIFY, spaceAfter=4*mm)

    foot_s = ParagraphStyle('F', parent=styles['Normal'], fontSize=8,
                            textColor=HexColor("#aaa"), alignment=TA_CENTER)

    now = datetime.now().strftime("%d %B %Y  |  %I:%M %p")
    story = []

    # Title & subtitle
    story.append(Paragraph("EduTube - Smart Notes Report", title_s))
    story.append(Paragraph(f"Generated by <b>{username}</b>  |  {now}", sub_s))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY,
                            spaceBefore=2*mm, spaceAfter=6*mm))

    # Original text (truncated if >3000 chars)
    story.append(Paragraph("Original Text", head_s))
    disp = original_text[:3000]
    if len(original_text) > 3000:
        disp += " ... [truncated]"
    story.append(Paragraph(disp.replace('\n', '<br/>'), body_s))
    story.append(Spacer(1, 6*mm))

    # Summary
    story.append(HRFlowable(width="100%", thickness=0.5,
                            color=HexColor("#ccc"),
                            spaceBefore=2*mm, spaceAfter=4*mm))
    story.append(Paragraph("Generated Summary", head_s))
    story.append(Paragraph(summary_text.replace('\n', '<br/>'), body_s))

    # Footer
    story.append(Spacer(1, 12*mm))
    story.append(HRFlowable(width="100%", thickness=0.5,
                            color=HexColor("#ccc"),
                            spaceBefore=2*mm, spaceAfter=4*mm))
    story.append(Paragraph(
        "EduTube Summarizer  |  B.Tech DBMS Academic Project  |  Flask + SQLite",
        foot_s))

    doc.build(story)
    buf.seek(0)
    return buf.read()
