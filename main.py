import json
import docx
import PyPDF2
import streamlit as st
import re
# App title
st.set_page_config(page_title="Equity Language Review Bot")
st.title("🤖 Equity Language Review Bot")
st.write("Upload your academic document (.docx or .pdf), and we'll flag non-equitable terms with suggested corrections.")

# Load flagged terms from JSON
@st.cache_data
def load_flagged_terms():
    with open("flagged_terms.json", "r", encoding="utf-8") as f:
        return json.load(f)

flagged_data = load_flagged_terms()

# File uploader
uploaded_file = st.file_uploader("Upload a file", type=["pdf", "docx", "txt"])
tone_style = st.selectbox(
    "Choose feedback tone:",
    ["Polite", "Direct", "Educational"]
)

# Text extraction functions
def extract_text_from_docx(file):
    doc = docx.Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text_from_pdf(file):
    def extract_text_from_txt(file):
        return file.read().decode("utf-8")
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

# Core flagging functionimport re

def flag_equity_issues(text, flagged_terms):
    results = []
    lines = text.split("\n")
    for line in lines:
        for entry in flagged_terms:
            pattern = entry.get("regex", None)
            if pattern:
                if re.search(pattern, line, re.IGNORECASE):
                    results.append({
                        "sentence": line.strip(),
                        "flagged": entry["flagged"],
                        "suggestion": entry["suggestion"],
                        "note": entry.get("note", "")
                    })
            else:
                # fallback to substring match if no regex provided
                if entry["flagged"].lower() in line.lower():
                    results.append({
                        "sentence": line.strip(),
                        "flagged": entry["flagged"],
                        "suggestion": entry["suggestion"],
                        "note": entry.get("note", "")
                    })
    return results

# Process uploaded file
def extract_text_from_txt(file):
    return file.read().decode("utf-8")
def format_note(note, tone):
    if tone == "Polite":
        return f"We recommend considering: {note}"
    elif tone == "Direct":
        return note
    elif tone == "Educational":
        return f"This may be problematic because: {note}. Consider revising."
    return note
if uploaded_file:
    if uploaded_file.name.endswith(".docx"):
        text = extract_text_from_docx(uploaded_file)
    elif uploaded_file.name.endswith(".pdf"):
        text = extract_text_from_pdf(uploaded_file)
    elif uploaded_file.name.endswith(".txt"):
        text = extract_text_from_txt(uploaded_file)
    else:
        st.error("Unsupported file type.")
        text = ""

    if text:
        st.info("Analyzing document...")
        flagged_results = flag_equity_issues(text, flagged_data)

        if flagged_results:
            st.subheader("🚩 Flagged Language Found:")
            from collections import Counter

            themes = [entry.get("theme", "Other") for entry in flagged_results]
            theme_counts = Counter(themes)

            st.subheader("📊 Thematic Summary")
            for theme, count in theme_counts.items():
                st.markdown(f"- **{theme}:** {count} flag(s)")
            for item in flagged_results:
                st.markdown(f"""
                ---
                **Sentence:** {item['sentence']}  
                **Flagged Term:** `{item['flagged']}`  
                **Suggestion:** *{item['suggestion']}*  
                **Note:** {format_note(item['note'], tone_style)}
                """)
        else:
            st.success("✅ No flagged terms found! 🎉")
            # After showing flagged items, offer download
            import io
            import pandas as pd

            df = pd.DataFrame(flagged_results)
            report_buffer = io.StringIO()
            df.to_csv(report_buffer, index=False)
            st.download_button(
                "📥 Download Feedback Report",
                report_buffer.getvalue(),
                file_name="equity_feedback.csv",
                mime="text/csv"
            )
