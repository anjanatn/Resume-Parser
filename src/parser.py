import os
import re
import hashlib
from datetime import datetime
import pymupdf  # PyMuPDF
import pypdf
from .utils import (
    SKILLS_TAXONOMY, DEGREE_PATTERNS, clean_text,
    extract_email, extract_phone, extract_linkedin, extract_github
)


class ResumeParser:
    def __init__(self):
        self.skills_taxonomy = SKILLS_TAXONOMY

    # ─────────────────────────── TEXT EXTRACTION ────────────────────────────

    def extract_text(self, file_path_or_stream, filename="document.pdf"):
        """Dispatch to correct extractor based on file extension."""
        ext = os.path.splitext(filename)[1].lower() if filename else ".pdf"

        if ext in [".txt", ".text"]:
            return self._read_txt(file_path_or_stream)
        if ext in [".docx", ".doc"]:
            return self._read_docx(file_path_or_stream)
        return self.extract_text_from_pdf(file_path_or_stream)

    def _read_txt(self, src):
        try:
            if isinstance(src, str):
                with open(src, "r", encoding="utf-8", errors="ignore") as f:
                    return clean_text(f.read())
            content = src.read()
            if isinstance(content, bytes):
                content = content.decode("utf-8", errors="ignore")
            src.seek(0)
            return clean_text(content)
        except Exception as e:
            print(f"[WARN] TXT read error: {e}")
            return ""

    def _read_docx(self, src):
        try:
            import docx
            doc = docx.Document(src)
            parts = []
            for para in doc.paragraphs:
                if para.text.strip():
                    parts.append(para.text)
            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join(c.text.strip() for c in row.cells if c.text.strip())
                    if row_text:
                        parts.append(row_text)
            return clean_text("\n".join(parts))
        except Exception as e:
            print(f"[WARN] DOCX read error: {e}")
            return ""

    def extract_text_from_pdf(self, pdf_path_or_stream):
        """
        Extract text from PDF.
        Strategy:
          1. PyMuPDF (fast, handles digital PDFs)
          2. pypdf fallback (alternative digital extraction)
          3. OCR via pytesseract (for scanned/image-only PDFs)
        """
        raw_text = ""

        # --- Attempt 1: PyMuPDF ---
        try:
            if isinstance(pdf_path_or_stream, str):
                doc = pymupdf.open(pdf_path_or_stream)
            else:
                data = pdf_path_or_stream.read()
                doc = pymupdf.open(stream=data, filetype="pdf")
                pdf_path_or_stream.seek(0)

            for page in doc:
                raw_text += page.get_text("text") + "\n"
            doc.close()
        except Exception as e:
            print(f"[WARN] PyMuPDF failed: {e}")

        # --- Attempt 2: pypdf fallback ---
        if not raw_text.strip():
            try:
                if not isinstance(pdf_path_or_stream, str):
                    pdf_path_or_stream.seek(0)
                reader = pypdf.PdfReader(pdf_path_or_stream)
                for page in reader.pages:
                    raw_text += (page.extract_text() or "") + "\n"
                if not isinstance(pdf_path_or_stream, str):
                    pdf_path_or_stream.seek(0)
            except Exception as e:
                print(f"[WARN] pypdf failed: {e}")

        # --- Attempt 3: OCR for scanned PDFs ---
        if len(raw_text.strip()) < 80:
            raw_text = self._ocr_pdf(pdf_path_or_stream) or raw_text

        return clean_text(raw_text)

    def _ocr_pdf(self, pdf_path_or_stream):
        """
        OCR fallback for scanned/image-based PDFs using pytesseract + Pillow.
        Requires: pip install pytesseract Pillow
        Also requires Tesseract-OCR binary: https://tesseract-ocr.github.io/
        """
        try:
            import pytesseract
            from PIL import Image
            import io

            pages_text = []
            if isinstance(pdf_path_or_stream, str):
                doc = pymupdf.open(pdf_path_or_stream)
            else:
                pdf_path_or_stream.seek(0)
                doc = pymupdf.open(stream=pdf_path_or_stream.read(), filetype="pdf")
                pdf_path_or_stream.seek(0)

            for page in doc:
                # Render page at 200 DPI for better OCR accuracy
                mat = pymupdf.Matrix(200 / 72, 200 / 72)
                pix = page.get_pixmap(matrix=mat)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                text = pytesseract.image_to_string(img, lang="eng")
                pages_text.append(text)
            doc.close()

            result = "\n".join(pages_text)
            if result.strip():
                print(f"[INFO] OCR extracted {len(result)} chars")
            return clean_text(result)
        except ImportError:
            print("[INFO] OCR unavailable — install pytesseract and Pillow for scanned PDF support")
            return ""
        except Exception as e:
            print(f"[WARN] OCR failed: {e}")
            return ""

    # ────────────────────────────── PARSE ───────────────────────────────────

    def parse(self, file_path_or_stream, filename="Resume.pdf"):
        """Main entry point. Returns a structured candidate profile dict."""
        raw_text = self.extract_text(file_path_or_stream, filename=filename)
        lines = [l.strip() for l in raw_text.split("\n") if l.strip()]

        name = self._extract_name(lines, filename)
        title = self._extract_title(lines)
        contact_info = self._extract_contact(raw_text)
        skills = self._extract_skills(raw_text)
        education_info = self._extract_education(raw_text)
        exp_years, work_history = self._extract_experience(raw_text)

        cand_id = os.path.splitext(os.path.basename(filename))[0]
        short_hash = hashlib.md5(cand_id.encode("utf-8")).hexdigest()[:4].upper()
        anonymous_id = f"CAND-{short_hash}"

        top_skills_str = ", ".join(skills[:4]) if skills else "software engineering"
        summary_pitch = (
            f"{title} with {exp_years} yrs experience "
            f"({top_skills_str}) and {education_info['highest_degree']} degree."
        )

        return {
            "id": cand_id,
            "anonymous_id": anonymous_id,
            "filename": filename,
            "name": name,
            "title": title,
            "contact": contact_info,
            "skills": skills,
            "experience_years": exp_years,
            "highest_degree": education_info["highest_degree"],
            "education": education_info["degrees"],
            "work_history": work_history,
            "raw_text": raw_text,
            "summary_pitch": summary_pitch,
            "status": "New",
        }

    # ─────────────────────────── EXTRACTORS ─────────────────────────────────

    def _extract_name(self, lines, filename):
        """Extract candidate name from header lines."""
        if not lines:
            return self._name_from_filename(filename)

        # Try first 4 lines — skip lines with URLs, digits, section headers
        for line in lines[:4]:
            clean = re.sub(r"(?i)\b(resume|cv|curriculum vitae|page\s+\d+)\b", "", line).strip()
            clean = re.sub(r"https?://\S+", "", clean).strip()
            if (
                clean
                and 2 <= len(clean.split()) <= 5
                and not re.search(r"\d|@|\.com|\.io|\.in|http|linkedin|github", clean)
                and not re.search(
                    r"(?i)\b(summary|experience|skills|education|profile|overview|contact|objective|work)\b",
                    clean,
                )
            ):
                return clean

        return self._name_from_filename(filename)

    def _name_from_filename(self, filename):
        base = os.path.splitext(os.path.basename(filename))[0]
        base = re.sub(r"^resume_\d+_", "", base)
        # Strip date-like suffixes e.g. _20250203_073955_0000
        base = re.sub(r"_\d{8}_\d+(_\d+)?$", "", base)
        return base.replace("_", " ").replace("-", " ").title()

    def _extract_title(self, lines):
        """Extract headline/title from first few lines."""
        title_keywords = [
            "engineer", "developer", "designer", "analyst", "architect",
            "manager", "lead", "specialist", "consultant", "scientist",
            "intern", "fresher", "graduate", "officer", "executive"
        ]
        if len(lines) > 1:
            for line in lines[1:6]:
                line_lower = line.lower()
                if not re.search(r"@|\d{3}-|\.com|http|github|linkedin|\d{4}", line):
                    if any(kw in line_lower for kw in title_keywords) and len(line.split()) <= 10:
                        return line
                    if len(line.split()) <= 8 and not re.search(
                        r"(?i)\b(summary|overview|skills|education|objective|contact|work)\b", line
                    ):
                        # Second-line heuristic: short non-section line
                        if 2 <= len(line.split()) <= 6:
                            return line
        return "Software Professional"

    def _extract_contact(self, text):
        """
        Improved contact extraction with multi-format phone support
        and location pattern recognition.
        """
        email = extract_email(text)
        phone = self._extract_phone_improved(text)
        linkedin = extract_linkedin(text)
        github = extract_github(text)
        location = self._extract_location(text)

        return {
            "email": email or "N/A",
            "phone": phone or "N/A",
            "linkedin": linkedin or "N/A",
            "github": github or "N/A",
            "location": location or "Not specified",
        }

    def _extract_phone_improved(self, text):
        """
        Extended phone patterns covering Indian (+91), US, and international formats.
        """
        patterns = [
            # International with country code
            r"\+\d{1,3}[\s\-.]?\(?\d{1,4}\)?[\s\-.]?\d{3,4}[\s\-.]?\d{3,4}",
            # Indian mobile 10-digit with/without spaces
            r"\b[6-9]\d{9}\b",
            # US/Canada format
            r"\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4}",
            # Spaced formats like 98 76 54 3210
            r"\b\d{2,5}[\s\-]\d{2,5}[\s\-]\d{2,5}\b",
        ]
        for pat in patterns:
            match = re.search(pat, text)
            if match:
                phone = match.group(0).strip()
                # Sanity: at least 7 digits
                if len(re.sub(r"\D", "", phone)) >= 7:
                    return phone
        return None

    def _extract_location(self, text):
        """Improved location extraction for Indian and international cities."""
        # Pattern: City, State/Country abbreviation
        loc_match = re.search(r"\b([A-Z][a-zA-Z\s]+,\s*(?:[A-Z]{2,3}|India|USA|UK|Germany|Canada|Australia))\b", text)
        if loc_match:
            return loc_match.group(1).strip()

        # Indian cities heuristic
        indian_cities = [
            "Bangalore", "Bengaluru", "Mumbai", "Delhi", "Chennai",
            "Hyderabad", "Pune", "Kolkata", "Kochi", "Thiruvananthapuram",
            "Kozhikode", "Thrissur", "Ernakulam", "Calicut", "Trivandrum"
        ]
        for city in indian_cities:
            if re.search(r"\b" + city + r"\b", text, re.IGNORECASE):
                return city

        # "Location:" prefix
        loc_label = re.search(r"(?i)(?:location|address|city)\s*[:\-]\s*([^\n,;]{3,40})", text)
        if loc_label:
            return loc_label.group(1).strip()

        return None

    def _extract_skills(self, text):
        """
        Match text against canonical skills taxonomy.
        Uses word-boundary matching and special handling for symbols.
        """
        text_lower = text.lower()
        matched = set()

        for keyword, canonical in self.skills_taxonomy.items():
            if keyword in ["c++", "c#", ".net", "next.js", "node.js", "vue.js", "ci/cd"]:
                pattern = r"(?i)" + re.escape(keyword)
            else:
                pattern = r"(?i)(?<![a-zA-Z])" + re.escape(keyword) + r"(?![a-zA-Z])"

            if re.search(pattern, text_lower):
                matched.add(canonical)

        return sorted(matched)

    def _extract_education(self, text):
        degrees = []
        highest_degree = "None"
        max_level = 0

        for pattern, degree_name, level in DEGREE_PATTERNS:
            for m in re.finditer(pattern, text):
                if level > max_level:
                    max_level = level
                    highest_degree = degree_name
                start = max(0, m.start() - 30)
                end = min(len(text), m.end() + 80)
                ctx = text[start:end].replace("\n", " ").strip()
                if degree_name not in [d["degree"] for d in degrees]:
                    degrees.append({"degree": degree_name, "context": ctx})

        return {"highest_degree": highest_degree, "degrees": degrees}

    def _extract_experience(self, text):
        """
        Parse work history using date ranges. Prefers explicit stated years.
        Improved with broader section detection and year-only ranges.
        """
        current_year = datetime.now().year

        # 1. Explicit "X years of experience" mention
        stated_years = None
        exp_mention = re.search(
            r"(?i)(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:experience|industry|professional)",
            text,
        )
        if exp_mention:
            try:
                stated_years = float(exp_mention.group(1))
            except ValueError:
                pass

        # 2. Isolate experience section
        exp_section = text
        exp_heading = re.search(
            r"(?i)\b(work\s+experience|professional\s+experience|employment\s+history|experience\s+timeline|work\s+history|career\s+history)\b",
            text,
        )
        edu_heading = re.search(
            r"(?i)\b(education|academic\s+background|qualifications)\b", text
        )
        if exp_heading:
            start_pos = exp_heading.end()
            end_pos = (
                edu_heading.start()
                if edu_heading and edu_heading.start() > start_pos
                else len(text)
            )
            exp_section = text[start_pos:end_pos]

        # 3. Match date ranges
        date_pattern = (
            r"(?i)\b"
            r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?\s*"
            r"(\d{4})\s*"
            r"[-\u2013\u2014to]+\s*"
            r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?\s*"
            r"(\d{4}|Present|Current|Now|Till\s+Date)\b"
        )
        matches = re.findall(date_pattern, exp_section)
        month_map = {
            "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
            "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
        }
        total_months = 0
        for start_m, start_y, end_m, end_y in matches:
            try:
                sy = int(start_y)
                sm = month_map.get(start_m.lower(), 1) if start_m else 1
                ey_str = end_y.lower().strip()
                if ey_str in ["present", "current", "now"] or "date" in ey_str:
                    ey = current_year
                    em = datetime.now().month
                else:
                    ey = int(end_y)
                    em = month_map.get(end_m.lower(), 12) if end_m else 12
                months = (ey - sy) * 12 + (em - sm)
                if 0 < months <= 240:
                    total_months += months
            except ValueError:
                continue

        calc_years = round(total_months / 12.0, 1)
        if stated_years is not None:
            final_years = stated_years
        elif calc_years > 0:
            final_years = calc_years
        else:
            final_years = 0.5  # Fresh candidate default

        # 4. Extract job role lines
        history = []
        for line in exp_section.split("\n"):
            if re.search(
                r"(?i)\b(engineer|developer|architect|analyst|manager|lead|specialist|consultant|intern|officer)\b",
                line,
            ):
                if len(line.split()) <= 12 and line.strip() not in history:
                    history.append(line.strip())

        return final_years, history[:5]
