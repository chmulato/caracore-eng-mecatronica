import os
import re
from PIL import Image as PILImage
from reportlab.lib.pagesizes import A5
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, Flowable, KeepTogether,
)
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
CAPITULOS_DIR = os.path.join(WORKSPACE_DIR, "capitulos")
IMAGENS_DIR = os.path.join(WORKSPACE_DIR, "imagens")
DOCS_IMAGENS_DIR = os.path.join(WORKSPACE_DIR, "docs", "imagens")
OUTPUT_PDF = os.path.join(WORKSPACE_DIR, "docs", "romance_instrutivo.pdf")
COVER_IMAGE = os.path.join(WORKSPACE_DIR, "capa.png")

os.makedirs(IMAGENS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(OUTPUT_PDF), exist_ok=True)

MARGIN = 0.62 * inch
CODE_LANGS = {
    "python", "cpp", "c++", "c", "assembly", "asm", "basic",
    "html", "css", "javascript", "js", "diagram", "mermaid",
}

FONT_NAME = "Verdana"
FONT_BOLD = "Verdana-Bold"
FONT_ITALIC = "Verdana-Italic"
FONT_BI = "Verdana-BoldItalic"
FONT_MONO = "CourierNew"

try:
    pdfmetrics.registerFont(TTFont(FONT_NAME, r"C:\Windows\Fonts\verdana.ttf"))
    pdfmetrics.registerFont(TTFont(FONT_BOLD, r"C:\Windows\Fonts\verdanab.ttf"))
    pdfmetrics.registerFont(TTFont(FONT_ITALIC, r"C:\Windows\Fonts\verdanai.ttf"))
    pdfmetrics.registerFont(TTFont(FONT_BI, r"C:\Windows\Fonts\verdanaz.ttf"))
    print("Fonte Verdana registrada com sucesso.")
except Exception as e:
    print(f"Aviso: Não foi possível carregar a fonte Verdana ({e}). Usando Helvetica como fallback.")
    FONT_NAME = "Helvetica"
    FONT_BOLD = "Helvetica-Bold"
    FONT_ITALIC = "Helvetica-Oblique"
    FONT_BI = "Helvetica-BoldOblique"

try:
    pdfmetrics.registerFont(TTFont(FONT_MONO, r"C:\Windows\Fonts\cour.ttf"))
    print("Fonte Courier New registrada com sucesso.")
except Exception as e:
    print(f"Aviso: Não foi possível carregar a fonte Courier New ({e}). Usando Courier como fallback.")
    FONT_MONO = "Courier"

chapter_pages = {}
chapter_titles = {}


def dest_name(key):
    return "ch_" + re.sub(r"[^a-zA-Z0-9]+", "_", key).strip("_")


def clean_heading(text):
    """Remove emojis (Verdana não os desenha) e entidades HTML soltas."""
    text = re.sub(
        r"[\U0001F300-\U0001FAFF\U00002700-\U000027BF\U0001F1E0-\U0001F1FF"
        r"\U00002600-\U000026FF\U0000FE00-\U0000FE0F\U0000200D\u200b]+",
        "",
        text,
    )
    text = text.replace("&rarr;", "→").replace("&larr;", "←").replace("&times;", "×")
    return re.sub(r"\s{2,}", " ", text).strip()


def convert_latex_to_html(math_text):
    math_text = math_text.replace(r"\approx", "≈")
    math_text = math_text.replace(r"\times", "×")
    math_text = math_text.replace(r"\cdot", "·")
    math_text = re.sub(r"\\vec\{(.*?)\}", r"\1", math_text)
    math_text = math_text.replace(r"\vec", "")
    math_text = math_text.replace(r"\text{ m/s}", " m/s")
    math_text = math_text.replace(r"\text{m/s}", " m/s")
    math_text = math_text.replace(r"\text", "")
    math_text = re.sub(r"\\frac\{(.*?)\}\{(.*?)\}", r"(\1) / \2", math_text)
    math_text = re.sub(r"\^\{(.*?)\}", r"<sup>\1</sup>", math_text)
    math_text = re.sub(r"\^(.)", r"<sup>\1</sup>", math_text)

    def italicize_vars(m):
        var = m.group(0)
        if var.lower() in ["m", "s", "sec"]:
            return var
        return f"<i>{var}</i>"

    math_text = re.sub(r"\b(PC|Efe|[a-zA-BD-Z])\b", italicize_vars, math_text)
    return math_text


def format_text(text):
    text = clean_heading(text)

    def repl_link(m):
        label = m.group(1)
        url = m.group(2).replace("&", "&amp;").replace('"', "&quot;")
        return f'<link href="{url}" color="#1b4b7a"><u>{label}</u></link>'

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", repl_link, text)

    def repl_code(m):
        code = m.group(1).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return f'<font face="{FONT_MONO}" size="9" color="#163623">{code}</font>'

    text = re.sub(r"`([^`]+)`", repl_code, text)
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.*?)\*", r"<i>\1</i>", text)
    text = text.replace("“", '"').replace("”", '"').replace('*"', '"').replace('"*', '"')
    text = re.sub(r"\$(.*?)\$", lambda m: convert_latex_to_html(m.group(1)), text)
    return text


def resolve_chapter_image(image_name):
    for folder in (IMAGENS_DIR, DOCS_IMAGENS_DIR):
        path = os.path.join(folder, image_name)
        if os.path.exists(path):
            return path
    return None


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_elements(num_pages)
            super().showPage()
        super().save()

    def draw_page_elements(self, page_count):
        page_w, page_h = self._pagesize

        if self._pageNumber == 1 and os.path.exists(COVER_IMAGE):
            self.saveState()
            self.setFillColor(colors.HexColor("#071018"))
            self.rect(0, 0, page_w, page_h, fill=1, stroke=0)
            self.drawImage(
                COVER_IMAGE, 0, 0,
                width=page_w, height=page_h,
                preserveAspectRatio=True, anchor="c", mask="auto",
            )
            self.restoreState()
            return

        if self._pageNumber <= 3:
            return

        self.saveState()
        self.setFont(FONT_ITALIC, 8)
        self.setFillColor(colors.HexColor("#555555"))
        self.setStrokeColor(colors.HexColor("#dddddd"))
        self.setLineWidth(0.5)
        self.line(MARGIN, page_h - 0.45 * inch, page_w - MARGIN, page_h - 0.45 * inch)

        book_page = self._pageNumber - 3

        if self._pageNumber % 2 == 0:
            self.drawString(MARGIN, 0.4 * inch, f"{book_page}")
            self.drawRightString(page_w - MARGIN, page_h - 0.4 * inch, "A Rebeldia da Mecatrônica")
        else:
            self.drawRightString(page_w - MARGIN, 0.4 * inch, f"{book_page}")
            self.drawString(MARGIN, page_h - 0.4 * inch, "Romance Instrutivo")

        for key, pg in chapter_pages.items():
            if pg == self._pageNumber:
                dest = dest_name(key)
                title = clean_heading(chapter_titles.get(key, key))
                self.bookmarkPage(dest)
                try:
                    self.addOutlineEntry(title, dest, level=0, closed=0)
                except Exception:
                    pass
                break

        self.restoreState()


class PageTracker(Flowable):
    def __init__(self, key, title):
        Flowable.__init__(self)
        self.key = key
        self.title = title
        self.width = 0
        self.height = 0

    def draw(self):
        chapter_pages[self.key] = self.canv._pageNumber
        dest = dest_name(self.key)
        self.canv.bookmarkPage(dest)


class HorizontalRule(Flowable):
    def __init__(self, color=colors.HexColor("#e6dcd3")):
        Flowable.__init__(self)
        self.color = color
        self._width = 1
        self.height = 14

    def wrap(self, availWidth, availHeight):
        self._width = availWidth
        return (availWidth, self.height)

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(0.6)
        y = self.height / 2.0
        self.canv.line(0, y, self._width, y)


class NonBlankPageBreak(Flowable):
    """Starts a new chapter page without leaving an empty sheet behind."""

    def wrap(self, availWidth, availHeight):
        # SimpleDocTemplate frames have 6pt padding on each side.
        usable = A5[1] - 2 * MARGIN - 0.15 * inch - 12
        if availHeight >= usable - 20:
            return (0, 0)
        return (availWidth, availHeight)

    def draw(self):
        pass


def create_discovery_box(lines, styles):
    full_text = "<br/>".join([format_text(l) for l in lines])
    intro_label = "<font color='#d95d14'><b>[Descoberta e Anotação do Diário]</b></font><br/>"
    p_diary = Paragraph(intro_label + full_text, styles["DiaryStyle"])
    t = Table([[p_diary]], colWidths=[A5[0] - 2 * MARGIN])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fdfaf6")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("LINELEFT", (0, 0), (0, -1), 3, colors.HexColor("#d95d14")),
        ("BOX", (0, 0), (-1, -1), 0.2, colors.HexColor("#e6dcd3")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return KeepTogether([t, Spacer(1, 8)])


def create_note_box(lines, styles):
    title = "Nota"
    body_parts = []
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("[!"):
            continue
        if line.startswith("#"):
            title = clean_heading(line.lstrip("#").strip())
            continue
        if line.startswith("- ") or line.startswith("* "):
            body_parts.append(f"• {format_text(line[2:])}")
        else:
            body_parts.append(format_text(line))

    intro_label = f"<font color='#1b4b7a'><b>[{title}]</b></font><br/>"
    p_note = Paragraph(intro_label + "<br/>".join(body_parts), styles["CalloutStyle"])
    t = Table([[p_note]], colWidths=[A5[0] - 2 * MARGIN])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f3f7fb")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("LINELEFT", (0, 0), (0, -1), 3, colors.HexColor("#1b4b7a")),
        ("BOX", (0, 0), (-1, -1), 0.2, colors.HexColor("#d5e2ee")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return KeepTogether([t, Spacer(1, 10)])


def create_code_block(code_lines, cap_index, styles, lang=""):
    escaped_lines = []
    for line in code_lines:
        leading = len(line) - len(line.lstrip(" "))
        rest = line.lstrip(" ")
        rest = rest.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        escaped_lines.append(("&nbsp;" * leading) + rest)
    code_text = "<br/>".join(escaped_lines) if escaped_lines else "&nbsp;"

    max_line_len = max((len(line) for line in code_lines), default=0)
    available_width = A5[0] - 2 * MARGIN - 24
    if max_line_len > 0:
        calculated_font_size = min(8.5, available_width / (max_line_len * 0.6))
        calculated_font_size = max(8.0, calculated_font_size)
    else:
        calculated_font_size = 8.0
    calculated_leading = calculated_font_size + 2.4

    unique_style_name = f"CodeStyle_{cap_index}_{abs(hash(code_text))}"
    p_style = ParagraphStyle(
        name=unique_style_name,
        parent=styles["CodeStyle"],
        fontSize=calculated_font_size,
        leading=calculated_leading,
    )
    p_code = Paragraph(code_text, p_style)
    t = Table([[p_code]], colWidths=[A5[0] - 2 * MARGIN])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#132e1c")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("BOX", (0, 0), (-1, -1), 4, colors.HexColor("#4a2f13")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return [t, Spacer(1, 10)]


def create_mermaid_path(code_lines, styles):
    blob = "\n".join(code_lines)
    labels = re.findall(r'\["([^"]+)"\]', blob)
    if not labels:
        labels = [ln.strip() for ln in code_lines if ln.strip() and not ln.strip().startswith("graph")]

    if not labels:
        return []

    parts = []
    for i, lab in enumerate(labels):
        parts.append(f"<b>{lab}</b>")
        if i < len(labels) - 1:
            parts.append("<font color='#d95d14'>- - -</font>")
    p = Paragraph("<br/>".join(parts), styles["PathStyle"])
    t = Table([[p]], colWidths=[A5[0] - 2 * MARGIN])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fdfaf6")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#d95d14")),
    ]))
    return [KeepTogether([t]), Spacer(1, 10)]


def create_pdf_register_diagram(styles):
    p_title = Paragraph(
        "<font size='9' color='#fffae0'><b>GAVETAS DO PROCESSADOR (REGISTRADORES)</b></font>",
        styles["NormalStyle"],
    )
    cell_a = Paragraph("<font color='#fffae0'><b>Reg A</b></font><br/><font size='8' color='#e2f3e8'>Acumulador</font>", styles["NormalStyle"])
    cell_b = Paragraph("<font color='#ffffff'><b>Reg B</b></font><br/><font size='8' color='#e2f3e8'>Auxiliar</font>", styles["NormalStyle"])
    cell_c = Paragraph("<font color='#ffffff'><b>Reg C</b></font><br/><font size='8' color='#e2f3e8'>Geral</font>", styles["NormalStyle"])
    cell_d = Paragraph("<font color='#ffffff'><b>Reg D</b></font><br/><font size='8' color='#e2f3e8'>Geral</font>", styles["NormalStyle"])

    t_cards = Table([[cell_a, cell_b], [cell_c, cell_d]], colWidths=[(A5[0] - 2 * MARGIN - 40) / 2] * 2)
    t_cards.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#163623")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (0, 0), 1.5, colors.HexColor("#fffae0")),
        ("BOX", (1, 0), (1, 0), 0.5, colors.HexColor("#ffffff")),
        ("BOX", (0, 1), (0, 1), 0.5, colors.HexColor("#ffffff")),
        ("BOX", (1, 1), (1, 1), 0.5, colors.HexColor("#ffffff")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))

    container = Table([[p_title], [t_cards]], colWidths=[A5[0] - 2 * MARGIN])
    container.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#132e1c")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BOX", (0, 0), (-1, -1), 4, colors.HexColor("#4a2f13")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return container


def flush_buffers(story, diary_lines, note_lines, styles):
    if note_lines:
        story.append(create_note_box(note_lines, styles))
        note_lines.clear()
    if diary_lines:
        story.append(create_discovery_box(diary_lines, styles))
        diary_lines.clear()


def parse_markdown_to_story(file_path, cap_index, styles):
    story = []

    with open(file_path, "r", encoding="utf-8") as f:
        first_line = f.readline().strip().lstrip("#").strip()

    if "Capítulo" in first_line:
        match = re.search(r"Capítulo\s+(\d+)", first_line)
        num = int(match.group(1)) if match else cap_index
        image_name = f"cap{num}.png"
    else:
        image_name = f"cap{cap_index}.png"

    image_path = resolve_chapter_image(image_name)
    image_inserted = False
    is_first_p_of_section = True

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = re.split(r"(```[\s\S]*?```)", content)

    for block in blocks:
        if block.startswith("```"):
            is_first_p_of_section = True
            code_lines = block.strip("`").strip().split("\n")
            block_type = code_lines[0].strip().lower() if code_lines else ""
            if block_type in CODE_LANGS:
                code_lines = code_lines[1:]

            if block_type == "diagram":
                story.append(create_pdf_register_diagram(styles))
                story.append(Spacer(1, 10))
                continue
            if block_type == "mermaid":
                story.extend(create_mermaid_path(code_lines, styles))
                continue

            story.extend(create_code_block(code_lines, cap_index, styles, block_type))
        else:
            lines = block.split("\n")
            diary_lines = []
            note_lines = []

            for line in lines:
                line_str = line.strip()
                if not line_str:
                    flush_buffers(story, diary_lines, note_lines, styles)
                    is_first_p_of_section = True
                    continue

                if line_str in ("---", "***", "___"):
                    flush_buffers(story, diary_lines, note_lines, styles)
                    story.append(HorizontalRule())
                    is_first_p_of_section = True
                    continue

                if line_str.startswith("$$") and line_str.endswith("$$"):
                    flush_buffers(story, diary_lines, note_lines, styles)
                    eq = line_str.strip("$").strip()
                    formatted_eq = convert_latex_to_html(eq)
                    p_eq = Paragraph(f"<b>{formatted_eq}</b>", styles["EquationStyle"])
                    t_eq = Table([[p_eq]], colWidths=[A5[0] - 2 * MARGIN])
                    t_eq.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#132e1c")),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("TOPPADDING", (0, 0), (-1, -1), 12),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                        ("LEFTPADDING", (0, 0), (-1, -1), 12),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                        ("BOX", (0, 0), (-1, -1), 3.5, colors.HexColor("#4a2f13")),
                    ]))
                    story.append(t_eq)
                    story.append(Spacer(1, 10))
                    is_first_p_of_section = True
                    continue

                quote_body = line_str.lstrip(">").strip() if line_str.startswith(">") else ""
                is_note_marker = quote_body.startswith("[!NOTE]") or quote_body.startswith("[!TIP]") or quote_body.startswith("[!WARNING]")

                if is_note_marker or note_lines:
                    if line_str.startswith(">") or is_note_marker:
                        if diary_lines:
                            story.append(create_discovery_box(diary_lines, styles))
                            diary_lines = []
                        note_lines.append(quote_body or line_str)
                        continue
                    flush_buffers(story, diary_lines, note_lines, styles)

                is_diary_line = (
                    line_str.startswith('*"') or line_str.startswith("“") or line_str.startswith(">")
                    or line_str.startswith('*"')
                )

                if line_str.startswith("#"):
                    flush_buffers(story, diary_lines, note_lines, styles)
                    is_first_p_of_section = True
                    hashes = len(line_str) - len(line_str.lstrip("#"))
                    heading = clean_heading(line_str[hashes:].strip())

                    if hashes == 1:
                        story.append(Paragraph(heading, styles["BookTitleStyle"]))
                        story.append(Spacer(1, 10))
                        if image_path and not image_inserted:
                            img = PILImage.open(image_path)
                            orig_w, orig_h = img.size
                            aspect = orig_h / orig_w
                            max_w = A5[0] - 2 * MARGIN
                            max_h = 240
                            if max_w * aspect <= max_h:
                                img_w, img_h = max_w, max_w * aspect
                            else:
                                img_h, img_w = max_h, max_h / aspect
                            story.append(Image(image_path, width=img_w, height=img_h))
                            story.append(Spacer(1, 15))
                            image_inserted = True
                    elif hashes == 2:
                        story.append(Paragraph(heading, styles["SectionHeaderStyle"]))
                        story.append(Spacer(1, 8))
                    else:
                        story.append(Paragraph(heading, styles["SubSectionHeaderStyle"]))
                        story.append(Spacer(1, 6))

                elif line_str.startswith("* ") or line_str.startswith("- "):
                    flush_buffers(story, diary_lines, note_lines, styles)
                    formatted_line = format_text(line_str[2:])
                    story.append(Paragraph(f"• {formatted_line}", styles["ListItemStyle"]))
                    is_first_p_of_section = True

                elif re.match(r"^\d+\.\s+", line_str):
                    flush_buffers(story, diary_lines, note_lines, styles)
                    num, rest = re.match(r"^(\d+)\.\s+(.*)", line_str).groups()
                    story.append(Paragraph(f"{num}. {format_text(rest)}", styles["ListItemStyle"]))
                    is_first_p_of_section = True

                elif is_diary_line:
                    if note_lines:
                        story.append(create_note_box(note_lines, styles))
                        note_lines = []
                    diary_lines.append(line_str.lstrip(">").strip())

                else:
                    flush_buffers(story, diary_lines, note_lines, styles)
                    formatted_line = format_text(line_str)
                    if is_first_p_of_section:
                        story.append(Paragraph(formatted_line, styles["NarrativeFirstStyle"]))
                        is_first_p_of_section = False
                    else:
                        story.append(Paragraph(formatted_line, styles["NarrativeStyle"]))
                    story.append(Spacer(1, 4))

            flush_buffers(story, diary_lines, note_lines, styles)
            is_first_p_of_section = True

    return story


def build_story(styles, page_map=None):
    story = []

    if os.path.exists(COVER_IMAGE):
        print("Inserindo capa em página inteira...")
        story.append(PageBreak())

    print("Inserindo dedicatória...")
    story.append(Spacer(1, 100))
    dedicatoria_text = (
        "<i>Dedicado à minha família, cujo apoio silencioso e inabalável estruturou "
        "o caminho para que este projeto de vida ganhasse o mundo.<br/><br/>"
        "E a todos os jovens engenheiros e mentes inquietas que, diante de estradas de barro "
        "ou algoritmos complexos, escolhem o caminho da persistência técnica e do "
        "despertar lúdico como ferramentas reais de emancipação.</i>"
    )
    story.append(Paragraph(dedicatoria_text, styles["DedicationStyle"]))
    story.append(PageBreak())

    print("Inserindo sumário...")
    story.append(Paragraph("Sumário", styles["BookTitleStyle"]))
    story.append(Spacer(1, 8))

    toc_data = []
    capitulos_files = sorted([f for f in os.listdir(CAPITULOS_DIR) if f.endswith(".md")])

    for idx, cap in enumerate(capitulos_files):
        cap_path = os.path.join(CAPITULOS_DIR, cap)
        with open(cap_path, "r", encoding="utf-8") as f:
            first_line = clean_heading(f.readline().strip().lstrip("#").strip())
        chapter_titles[cap] = first_line
        dest = dest_name(cap)

        if page_map and cap in page_map:
            pg = str(page_map[cap] - 3)
        else:
            pg = ""

        p_title = Paragraph(
            f'<link href="#{dest}" color="#1b4b7a">{first_line}</link>',
            styles["TOCStyle"],
        )
        p_page = Paragraph(
            f'<link href="#{dest}" color="#555555">{pg}</link>',
            styles["TOCPageStyle"],
        )
        toc_data.append([p_title, p_page])

    t_toc = Table(toc_data, colWidths=[300, 32])
    t_toc.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), FONT_NAME),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#2a2b2d")),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#eeeeee")),
    ]))
    story.append(KeepTogether([t_toc]))
    story.append(PageBreak())

    for idx, cap in enumerate(capitulos_files):
        cap_path = os.path.join(CAPITULOS_DIR, cap)
        if idx > 0:
            story.append(NonBlankPageBreak())
        story.append(PageTracker(cap, chapter_titles.get(cap, cap)))
        story.extend(parse_markdown_to_story(cap_path, idx, styles))

    print("Inserindo créditos...")
    story.append(PageBreak())
    story.append(Spacer(1, 90))
    story.append(Paragraph("Créditos", styles["BookTitleStyle"]))
    story.append(Spacer(1, 14))
    story.append(Paragraph(
        "<b>A Rebeldia da Mecatrônica</b><br/>Romance Instrutivo de Tecnologia e Sociedade",
        styles["CreditStyle"],
    ))
    story.append(Spacer(1, 16))
    story.append(Paragraph("Autor: Christian Vladimir Uhdre Mulato", styles["CreditStyle"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Publicado por <b>Cara Core Informática</b><br/>"
        "CNPJ 23.969.028/0001-37 · www.caracore.com.br · suporte@caracore.com.br",
        styles["CreditStyle"],
    ))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Leitura online e PDF gratuitos.", styles["CreditStyle"]))

    return story


def build_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="BookTitleStyle",
        parent=styles["Heading1"],
        fontName=FONT_BOLD,
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#0f2a4a"),
        spaceAfter=10,
        keepWithNext=True,
    ))
    styles.add(ParagraphStyle(
        name="SectionHeaderStyle",
        parent=styles["Heading2"],
        fontName=FONT_BOLD,
        fontSize=12.5,
        leading=16,
        textColor=colors.HexColor("#1b4b7a"),
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True,
    ))
    styles.add(ParagraphStyle(
        name="SubSectionHeaderStyle",
        parent=styles["Heading3"],
        fontName=FONT_BOLD,
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#d95d14"),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True,
    ))
    styles.add(ParagraphStyle(
        name="NormalStyle",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=12,
        leading=17,
        textColor=colors.HexColor("#2a2b2d"),
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="EquationStyle",
        fontName=FONT_MONO,
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#fffae0"),
        alignment=1,
        spaceBefore=0,
        spaceAfter=0,
    ))
    styles.add(ParagraphStyle(
        name="NarrativeStyle",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=12,
        leading=17,
        textColor=colors.HexColor("#1a1b1d"),
        firstLineIndent=14,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="NarrativeFirstStyle",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=12,
        leading=17,
        textColor=colors.HexColor("#1a1b1d"),
        firstLineIndent=0,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="DiaryStyle",
        parent=styles["Normal"],
        fontName=FONT_ITALIC,
        fontSize=11,
        leading=15.5,
        textColor=colors.HexColor("#3a3b3d"),
    ))
    styles.add(ParagraphStyle(
        name="CalloutStyle",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=10.5,
        leading=15,
        textColor=colors.HexColor("#1a1b1d"),
    ))
    styles.add(ParagraphStyle(
        name="PathStyle",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=11,
        leading=16,
        alignment=1,
        textColor=colors.HexColor("#1a1b1d"),
    ))
    styles.add(ParagraphStyle(
        name="DedicationStyle",
        parent=styles["Normal"],
        fontName=FONT_ITALIC,
        fontSize=12,
        leading=18,
        textColor=colors.HexColor("#333333"),
        alignment=1,
    ))
    styles.add(ParagraphStyle(
        name="CreditStyle",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=11,
        leading=16,
        textColor=colors.HexColor("#333333"),
        alignment=1,
    ))
    styles.add(ParagraphStyle(
        name="ListItemStyle",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=12,
        leading=16.5,
        textColor=colors.HexColor("#2a2b2d"),
        leftIndent=15,
        spaceAfter=3,
    ))
    styles.add(ParagraphStyle(
        name="CodeStyle",
        fontName=FONT_MONO,
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#e2f3e8"),
    ))
    styles.add(ParagraphStyle(
        name="TOCStyle",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#1b4b7a"),
    ))
    styles.add(ParagraphStyle(
        name="TOCPageStyle",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=9,
        leading=12,
        alignment=2,
        textColor=colors.HexColor("#555555"),
    ))
    return styles


def make_doc():
    doc = SimpleDocTemplate(
        OUTPUT_PDF,
        pagesize=A5,
        rightMargin=MARGIN,
        leftMargin=MARGIN,
        topMargin=MARGIN + 0.15 * inch,
        bottomMargin=MARGIN,
        title="A Rebeldia da Mecatrônica",
        author="Christian Vladimir Uhdre Mulato",
        subject="Romance instrutivo de engenharia, mecatrônica e tecnologia para jovens. Publicado pela Cara Core Informática.",
        creator="Cara Core Informática",
        lang="pt-BR",
    )
    return doc


def main():
    print("Iniciando compilação do livro em A5 (modo leitura)...")
    styles = build_styles()

    print("Passo 1: Detectando número das páginas dos capítulos...")
    chapter_pages.clear()
    doc_temp = make_doc()
    story_temp = build_story(styles, page_map=None)
    doc_temp.build(story_temp, canvasmaker=NumberedCanvas)

    print("Passo 2: Gerando versão final do PDF com Sumário, bookmarks e links...")
    page_map = dict(chapter_pages)
    chapter_pages.clear()
    doc_final = make_doc()
    story_final = build_story(styles, page_map=page_map)
    doc_final.build(story_final, canvasmaker=NumberedCanvas)

    print(f"Livro compilado com sucesso em: {OUTPUT_PDF}")


if __name__ == "__main__":
    main()
