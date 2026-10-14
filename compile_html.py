import os
import re
import shutil

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
CAPITULOS_DIR = os.path.join(WORKSPACE_DIR, "capitulos")
OUTPUT_HTML = os.path.join(WORKSPACE_DIR, "docs", "index.html")
CODE_LANGS = {
    "python", "cpp", "c++", "c", "assembly", "asm", "basic",
    "html", "css", "javascript", "js", "diagram", "mermaid",
}


def convert_latex_to_html_local(math_text):
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

    return re.sub(r"\b(PC|Efe|[a-zA-BD-Z])\b", italicize_vars, math_text)


def format_inline(text):
    text = text.replace("&rarr;", "→").replace("&larr;", "←").replace("&times;", "×")

    def repl_link(m):
        return (
            f'<a class="ext-link" href="{m.group(2)}" target="_blank" '
            f'rel="noopener noreferrer">{m.group(1)}</a>'
        )

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", repl_link, text)
    text = re.sub(r"`([^`]+)`", r'<code class="inline-code">\1</code>', text)
    text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.*?)\*", r"<em>\1</em>", text)
    text = re.sub(
        r"\$(.*?)\$",
        lambda m: f'<span class="html-math">{convert_latex_to_html_local(m.group(1))}</span>',
        text,
    )
    return text


def mermaid_path_html(code_lines):
    labels = re.findall(r'\["([^"]+)"\]', "\n".join(code_lines))
    if not labels:
        return ""
    parts = []
    for i, lab in enumerate(labels):
        parts.append(f'<div class="path-step">{lab}</div>')
        if i < len(labels) - 1:
            parts.append('<div class="path-arrow" aria-hidden="true"></div>')
    return f'<div class="learning-path">{"".join(parts)}</div>'


def format_markdown_to_html(content):
    blocks = re.split(r"(```[\s\S]*?```)", content)
    formatted_blocks = []
    in_diary = False
    diary_buffer = []
    note_buffer = []
    list_buffer = []

    def flush_diary():
        nonlocal in_diary, diary_buffer
        if diary_buffer:
            formatted_blocks.append(
                '<div class="discovery-box"><span class="box-tag">Diário de Bordo</span>'
                f'{"<br/>".join(diary_buffer)}</div>'
            )
        in_diary = False
        diary_buffer = []

    def flush_note():
        nonlocal note_buffer
        if not note_buffer:
            return
        title = "Nota"
        items, paras = [], []
        for raw in note_buffer:
            line = raw.strip()
            if not line or line.startswith("[!"):
                continue
            if line.startswith("#"):
                title = line.lstrip("#").strip()
            elif line.startswith("- ") or line.startswith("* "):
                items.append(f"<li>{format_inline(line[2:])}</li>")
            else:
                paras.append(f"<p>{format_inline(line)}</p>")
        body = "".join(paras)
        if items:
            body += f"<ul>{''.join(items)}</ul>"
        formatted_blocks.append(
            f'<aside class="callout-box"><span class="box-tag">{title}</span>{body}</aside>'
        )
        note_buffer = []

    def flush_list():
        nonlocal list_buffer
        if list_buffer:
            formatted_blocks.append(f"<ul>{''.join(list_buffer)}</ul>")
        list_buffer = []

    def flush_all():
        flush_note()
        flush_diary()
        flush_list()

    for block in blocks:
        if block.startswith("```"):
            flush_all()
            lines = block.strip("`").strip().split("\n")
            block_type = lines[0].strip().lower() if lines else ""
            if block_type in CODE_LANGS:
                lines = lines[1:]
            clean_code = "\n".join(lines).replace("<", "&lt;").replace(">", "&gt;")
            if block_type == "diagram":
                formatted_blocks.append("""
<div class="register-diagram">
  <div class="diagram-title">Gavetas do Processador (Registradores)</div>
  <div class="diagram-grid">
    <div class="register-card active"><span class="reg-name">Reg A</span><span class="reg-desc">Acumulador</span></div>
    <div class="register-card"><span class="reg-name">Reg B</span><span class="reg-desc">Auxiliar</span></div>
    <div class="register-card"><span class="reg-name">Reg C</span><span class="reg-desc">Geral</span></div>
    <div class="register-card"><span class="reg-name">Reg D</span><span class="reg-desc">Geral</span></div>
  </div>
</div>""")
            elif block_type == "mermaid":
                formatted_blocks.append(mermaid_path_html(lines))
            else:
                formatted_blocks.append(f"<pre><code>{clean_code}</code></pre>")
            continue

        block = re.sub(
            r"\$\$(.*?)\$\$",
            lambda m: f'<div class="html-equation">{convert_latex_to_html_local(m.group(1))}</div>',
            block,
        )

        for line in block.split("\n"):
            line_str = line.strip()
            if not line_str:
                flush_all()
                continue
            if line_str in ("---", "***", "___"):
                flush_all()
                formatted_blocks.append('<hr class="section-rule">')
                continue

            quote_body = line_str.lstrip(">").strip() if line_str.startswith(">") else ""
            if quote_body.startswith("[!NOTE]") or quote_body.startswith("[!TIP]") or (
                note_buffer and line_str.startswith(">")
            ):
                flush_diary()
                flush_list()
                note_buffer.append(quote_body or line_str)
                continue
            if note_buffer:
                flush_note()

            if line_str.startswith("#"):
                flush_all()
                hashes = len(line_str) - len(line_str.lstrip("#"))
                heading = format_inline(line_str[hashes:].strip())
                tag = {1: "h1", 2: "h2", 3: "h3"}.get(hashes, "h4")
                css = ' class="chapter-title"' if hashes == 1 else ""
                formatted_blocks.append(f"<{tag}{css}>{heading}</{tag}>")
            elif line_str.startswith("* ") or line_str.startswith("- "):
                flush_note()
                flush_diary()
                list_buffer.append(f"<li>{format_inline(line_str[2:])}</li>")
            elif re.match(r"^\d+\.\s+", line_str):
                flush_note()
                flush_diary()
                numbered = re.sub(r"^\d+\.\s+", "", line_str)
                list_buffer.append(f"<li>{format_inline(numbered)}</li>")
            elif line_str.startswith(">") or line_str.startswith("*“") or line_str.startswith("“"):
                flush_list()
                in_diary = True
                diary_buffer.append(format_inline(line_str.lstrip(">").strip()))
            elif in_diary:
                diary_buffer.append(format_inline(line_str))
            else:
                flush_all()
                level = re.match(
                    r"\*\*(Nível\s+[12]\s+\((?:Iniciante|Avançado)\):[^*]+)\*\*\s*(.*)",
                    line.strip(),
                )
                if level:
                    badge, rest = level.group(1), level.group(2)
                    kind = "beginner" if "Iniciante" in badge else "advanced"
                    extra = f" {format_inline(rest)}" if rest else ""
                    formatted_blocks.append(
                        f'<p class="challenge-heading challenge-{kind}"><strong>{badge}</strong>{extra}</p>'
                    )
                else:
                    formatted_blocks.append(f'<p class="narrative-p">{format_inline(line_str)}</p>')
        flush_all()
    return "\n".join(formatted_blocks)


def main():
    print("Iniciando compilação do livro em HTML responsivo...")

    html_start = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="theme-color" content="#1e293b">
    <meta name="author" content="Christian Vladimir Uhdre Mulato">
    <meta name="description" content="A Rebeldia da Mecatrônica — romance instrutivo de tecnologia e sociedade, de Christian Vladimir Uhdre Mulato.">
    <title>A Rebeldia da Mecatrônica — Christian Vladimir Uhdre Mulato</title>
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🤖</text></svg>">
    <style>
        :root {
            --bg-color: #0f172a;
            --header-bg: #1e293b;
            --text-color: #f1f5f9;
            --text-muted: #94a3b8;
            --primary: #d95d14;
            --primary-glow: rgba(217, 93, 20, 0.15);
            --secondary: #3b82f6;
            --card-bg: rgba(30, 41, 59, 0.7);
            --border-color: #334155;
            --header-h: 56px;
            --sidebar-w: 280px;
            --read-max: 40rem;
        }
        html { scroll-behavior: smooth; scroll-padding-top: calc(var(--header-h) + 16px); }
        * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }
        body {
            font-family: Inter, "Segoe UI", sans-serif;
            background: var(--bg-color);
            color: var(--text-color);
            line-height: 1.7;
            padding-top: var(--header-h);
            padding-left: env(safe-area-inset-left);
            padding-right: env(safe-area-inset-right);
        }
        .read-progress {
            position: fixed; top: 0; left: 0; height: 3px; width: 0;
            background: var(--primary); z-index: 120; pointer-events: none;
        }
        .mobile-header {
            position: fixed; top: 0; left: 0; right: 0; height: var(--header-h);
            background: var(--header-bg); border-bottom: 1px solid var(--border-color);
            display: flex; align-items: center; justify-content: space-between;
            padding: 0 0.85rem; z-index: 100;
            padding-top: env(safe-area-inset-top);
        }
        .header-title {
            font-family: Outfit, sans-serif; font-size: 0.95rem; font-weight: 700; color: #fff;
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
            max-width: calc(100vw - 148px);
        }
        .header-actions { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
        .menu-button {
            background: none; border: 0; color: var(--text-color); font-size: 1.45rem;
            cursor: pointer; padding: 8px; min-width: 44px; min-height: 44px;
        }
        .header-download-btn {
            background: var(--primary); color: #fff; text-decoration: none;
            padding: 0.4rem 0.7rem; border-radius: 6px; font-size: 0.78rem; font-weight: 700;
        }
        .header-app-btn {
            color: #bae6fd; text-decoration: none; padding: 0.4rem 0.55rem;
            border: 1px solid #316582; border-radius: 6px; font-size: 0.78rem; font-weight: 700;
        }
        .nav-drawer {
            position: fixed; top: var(--header-h); bottom: 0; left: -100%; width: min(85%, 300px);
            background: var(--header-bg); border-right: 1px solid var(--border-color);
            z-index: 99; transition: left 0.25s ease; overflow-y: auto; padding: 1.25rem;
        }
        .nav-drawer.open { left: 0; }
        .nav-drawer h2 {
            font-family: Outfit, sans-serif; font-size: 1.05rem; color: var(--primary);
            margin-bottom: 1rem; border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem;
        }
        .nav-drawer ul { list-style: none; }
        .nav-drawer a {
            color: var(--text-muted); text-decoration: none; font-size: 0.9rem;
            display: block; padding: 0.55rem 0.5rem; border-radius: 6px;
        }
        .nav-drawer a.active, .nav-drawer a:hover {
            color: #fff; background: var(--bg-color); border-left: 3px solid var(--primary); padding-left: 0.65rem;
        }
        .overlay {
            position: fixed; top: var(--header-h); inset: var(--header-h) 0 0 0;
            background: rgba(0,0,0,0.5); z-index: 98; display: none;
        }
        .overlay.show { display: block; }
        .content-container {
            width: 100%; max-width: var(--read-max); margin: 0 auto;
            padding: 1.25rem 1.15rem 3.5rem;
        }
        .cover-section { text-align: center; padding: 1.25rem 0 2.5rem; border-bottom: 1px solid var(--border-color); margin-bottom: 2.5rem; }
        .cover-image {
            width: min(100%, 280px); height: auto; border-radius: 12px;
            box-shadow: 0 12px 32px rgba(0,0,0,0.5), 0 0 24px var(--primary-glow);
            margin-bottom: 1.25rem; border: 1px solid var(--border-color);
        }
        .cover-title { font-family: Outfit, sans-serif; font-size: clamp(1.6rem, 6vw, 2.35rem); font-weight: 700; color: #fff; margin-bottom: 0.4rem; line-height: 1.2; }
        .cover-subtitle { font-size: 0.98rem; color: var(--text-muted); margin-bottom: 0.35rem; }
        .cover-author { font-size: 1rem; color: #e2e8f0; font-weight: 600; margin-bottom: 1.25rem; }
        .download-cta-btn {
            display: inline-flex; align-items: center; justify-content: center;
            background: var(--primary); color: #fff; text-decoration: none;
            padding: 0.75rem 1.35rem; border-radius: 8px; font-size: 0.92rem; font-weight: 700;
            margin: 0.5rem 0 1rem; box-shadow: 0 4px 15px rgba(217,93,20,0.4);
        }
        .app-cta-btn {
            display: inline-flex; align-items: center; justify-content: center;
            color: #e0f2fe; text-decoration: none; padding: 0.7rem 1.15rem;
            border: 1px solid #3b82f6; border-radius: 8px; font-size: 0.9rem; font-weight: 700;
            margin: 0.5rem 0.35rem 1rem; background: rgba(59,130,246,0.12);
        }
        .dedication { font-style: italic; font-size: 0.98rem; color: var(--text-muted); text-align: center; margin: 1.5rem auto 0; line-height: 1.65; max-width: 36rem; }
        .chapter-section { margin-bottom: 4rem; scroll-margin-top: calc(var(--header-h) + 12px); }
        .chapter-title {
            font-family: Outfit, sans-serif; font-size: clamp(1.35rem, 5vw, 1.85rem);
            color: #fff; margin-bottom: 1.25rem; border-bottom: 2px solid var(--border-color);
            padding-bottom: 0.5rem; font-weight: 700; line-height: 1.25;
        }
        h2 { font-family: Outfit, sans-serif; color: var(--secondary); font-size: 1.18rem; margin: 1.8rem 0 0.7rem; }
        h3 { font-family: Outfit, sans-serif; color: var(--primary); font-size: 1.05rem; margin: 1.4rem 0 0.55rem; }
        h4 { color: #fdba74; font-size: 1rem; margin: 1.1rem 0 0.45rem; }
        p, .narrative-p {
            margin-bottom: 1rem; color: #e2e8f0; font-size: 1.05rem; line-height: 1.75;
        }
        .narrative-p { text-indent: 1.15em; }
        .chapter-title + .narrative-p, h2 + .narrative-p, h3 + .narrative-p, h4 + .narrative-p,
        ul + .narrative-p, .discovery-box + .narrative-p, pre + .narrative-p,
        .html-equation + .narrative-p, .chapter-image + .narrative-p,
        .register-diagram + .narrative-p, .callout-box + .narrative-p,
        .challenge-heading + .narrative-p, .learning-path + .narrative-p, hr + .narrative-p {
            text-indent: 0;
        }
        ul { margin: 0.4rem 0 1.1rem 1.15rem; }
        li { margin-bottom: 0.45rem; color: #cbd5e1; font-size: 1.02rem; line-height: 1.6; }
        .section-rule { border: 0; border-top: 1px solid var(--border-color); margin: 1.6rem 0; }
        .ext-link { color: #7dd3fc; }
        .inline-code {
            font-family: "Fira Code", monospace; font-size: 0.88em; color: #bbf7d0;
            background: #163623; padding: 0.1em 0.35em; border-radius: 4px;
        }
        .discovery-box {
            background: rgba(30,41,59,0.45); border-left: 4px solid var(--primary);
            border: 1px solid var(--border-color); border-left-width: 4px; border-left-color: var(--primary);
            padding: 14px 16px; border-radius: 4px 12px 12px 4px; margin: 1.5rem 0;
            font-style: italic; color: #f8fafc; font-size: 0.98rem; line-height: 1.65;
        }
        .box-tag {
            font-style: normal; font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
            color: var(--primary); letter-spacing: 1.2px; display: block; margin-bottom: 8px;
        }
        .callout-box {
            background: rgba(30, 58, 95, 0.35); border: 1px solid #1e4976; border-left: 4px solid var(--secondary);
            padding: 14px 16px; border-radius: 4px 12px 12px 4px; margin: 1.5rem 0;
        }
        .callout-box .box-tag { color: #93c5fd; }
        .callout-box p, .callout-box li { font-size: 0.98rem; color: #e2e8f0; }
        .challenge-heading {
            margin: 1.2rem 0 0.6rem; padding: 0.65rem 0.9rem; border-radius: 8px; font-size: 1rem;
        }
        .challenge-beginner { background: rgba(22, 101, 52, 0.35); border-left: 4px solid #4ade80; }
        .challenge-advanced { background: rgba(124, 45, 18, 0.35); border-left: 4px solid var(--primary); }
        pre {
            background: linear-gradient(135deg, #112919 0%, #153520 100%);
            border: 5px solid #4a2f13; padding: 1rem; border-radius: 6px;
            overflow-x: auto; margin: 1.4rem 0; -webkit-overflow-scrolling: touch;
            box-shadow: inset 0 0 25px rgba(0,0,0,0.8);
        }
        code { font-family: "Fira Code", ui-monospace, monospace; font-size: 0.84rem; color: #e2f3e8; }
        .html-equation {
            background: linear-gradient(135deg, #112919 0%, #153520 100%);
            border: 5px solid #4a2f13; border-radius: 6px; padding: 1rem; text-align: center;
            margin: 1.4rem 0; color: #fffae0; font-family: "Fira Code", monospace; font-size: 0.95rem;
            overflow-x: auto;
        }
        .html-math {
            font-family: "Fira Code", monospace; color: #fffae0; background: #1a3c26;
            padding: 2px 6px; border-radius: 3px; font-size: 0.9rem;
        }
        .chapter-image { width: 100%; height: auto; border-radius: 8px; margin: 0 0 1.5rem; border: 1px solid var(--border-color); }
        .register-diagram {
            background: linear-gradient(135deg, #132e1c 0%, #1a3e26 100%);
            border: 5px solid #4a2f13; border-radius: 6px; padding: 1.1rem; margin: 1.4rem 0;
        }
        .diagram-title { font-family: Outfit, sans-serif; font-size: 0.9rem; font-weight: 700; text-transform: uppercase; color: #fffae0; letter-spacing: 1.2px; margin-bottom: 1rem; text-align: center; }
        .diagram-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        .register-card { background: rgba(255,255,255,0.05); border: 2px dashed rgba(255,255,255,0.3); border-radius: 4px; padding: 10px; text-align: center; }
        .register-card.active { border: 2px solid #fffae0; }
        .reg-name { display: block; font-family: "Fira Code", monospace; font-size: 1.1rem; font-weight: 700; color: #fff; }
        .reg-desc { display: block; font-size: 0.75rem; color: rgba(255,255,255,0.7); }
        .learning-path {
            background: #fdfaf6; color: #1a1b1d; border: 1px solid #d95d14; border-radius: 10px;
            padding: 1.1rem; margin: 1.4rem 0; text-align: center;
        }
        .path-step { font-weight: 700; padding: 0.25rem 0; }
        .path-arrow { width: 2px; height: 16px; background: #d95d14; margin: 4px auto; }
        .next-chapter-container { display: flex; justify-content: center; margin: 3rem 0 1rem; padding-top: 1.8rem; border-top: 1px dashed var(--border-color); }
        .next-chapter-link {
            display: inline-flex; align-items: center; text-align: center; gap: 8px;
            background: var(--card-bg); border: 1px solid var(--border-color); color: var(--primary);
            text-decoration: none; padding: 0.85rem 1.3rem; border-radius: 10px;
            font-family: Outfit, sans-serif; font-weight: 600; font-size: 0.92rem; line-height: 1.35;
        }

        @media (min-width: 640px) {
            :root { --header-h: 60px; }
            .content-container { padding: 1.6rem 1.75rem 4rem; }
            .cover-image { width: min(100%, 340px); }
            p, .narrative-p { font-size: 1.08rem; }
        }
        @media (min-width: 768px) {
            .content-container { padding: 2rem 2.25rem 4.5rem; }
            .cover-image { width: min(100%, 380px); }
            .header-title { font-size: 1.05rem; max-width: none; }
            pre code { font-size: 0.88rem; }
        }
        @media (min-width: 1024px) {
            .menu-button { display: none; }
            .overlay { display: none !important; }
            .nav-drawer {
                left: 0; width: var(--sidebar-w); top: var(--header-h);
                box-shadow: none;
            }
            .content-container {
                margin-left: var(--sidebar-w);
                max-width: none;
                padding: 2.4rem 3rem 5rem;
            }
            .chapter-section { max-width: var(--read-max); }
            .cover-section { max-width: 52rem; }
            .cover-section { display: grid; grid-template-columns: 280px 1fr; gap: 2rem; align-items: center; text-align: left; }
            .cover-image { width: 100%; margin-bottom: 0; }
            .cover-copy { text-align: left; }
            .header-title { max-width: none; }
        }
        @media (min-width: 1280px) {
            :root { --read-max: 44rem; --sidebar-w: 300px; }
            .content-container { padding: 2.6rem 4rem 5rem; }
        }
        @media (prefers-reduced-motion: reduce) {
            html { scroll-behavior: auto; }
            .nav-drawer { transition: none; }
        }
    </style>
</head>
<body>
    <div class="read-progress" id="readProgress"></div>
    <header class="mobile-header">
        <span class="header-title">A Rebeldia da Mecatrônica</span>
        <div class="header-actions">
            <a href="app/" class="header-app-btn">Universo</a>
            <a href="romance_instrutivo.pdf" class="header-download-btn" download>PDF</a>
            <button class="menu-button" id="menuBtn" aria-label="Abrir sumário">☰</button>
        </div>
    </header>
    <div class="overlay" id="overlay"></div>
    <nav class="nav-drawer" id="drawer" aria-label="Sumário">
        <h2>Capítulos</h2>
        <ul>
            <li><a href="#cover" class="active">Capa</a></li>
"""

    capitulos = sorted([f for f in os.listdir(CAPITULOS_DIR) if f.endswith(".md")])
    chapter_slugs, chapter_labels, menu_items = [], [], []

    for idx, cap in enumerate(capitulos, start=1):
        cap_path = os.path.join(CAPITULOS_DIR, cap)
        with open(cap_path, "r", encoding="utf-8") as f:
            first_line = f.readline().strip().lstrip("#").strip()
        clean_title = first_line.split(":")[-1].strip() if ":" in first_line else first_line
        if "Capítulo" in first_line:
            match = re.search(r"Capítulo\s+(\d+)", first_line)
            num = int(match.group(1)) if match else idx
            slug, label = f"cap{num}", f"Cap. {num}: {clean_title}"
        elif "Apêndice" in first_line:
            match = re.search(r"Apêndice\s+([A-Z])", first_line)
            letra = match.group(1) if match else "A"
            slug, label = f"apendice-{letra.lower()}", f"Apêndice {letra}: {clean_title}"
        else:
            if "Estudar" in first_line:
                slug = "como-estudar"
            elif "Prólogo" in first_line:
                slug = "prologo"
            else:
                slug = cap.replace(".md", "").replace("00_", "").replace("_", "-")
            label = first_line
        chapter_slugs.append(slug)
        chapter_labels.append(label)
        menu_items.append(f'            <li><a href="#{slug}">{label}</a></li>')

    chapters_content = []
    for idx, cap in enumerate(capitulos):
        slug = chapter_slugs[idx]
        cap_path = os.path.join(CAPITULOS_DIR, cap)
        with open(cap_path, "r", encoding="utf-8") as f:
            first_line = f.readline().strip().lstrip("#").strip()
        img_name = None
        if "Capítulo" in first_line:
            match = re.search(r"Capítulo\s+(\d+)", first_line)
            num = int(match.group(1)) if match else (idx + 1)
            img_name = f"cap{num}.png"
        with open(cap_path, "r", encoding="utf-8") as f:
            body = f.read()
        formatted_body = format_markdown_to_html(body)
        if img_name and os.path.exists(os.path.join(WORKSPACE_DIR, "imagens", img_name)):
            img_html = f'<img src="imagens/{img_name}" alt="Ilustração: {chapter_labels[idx]}" class="chapter-image">'
            if "</h1>" in formatted_body:
                parts = formatted_body.split("</h1>", 1)
                formatted_body = parts[0] + "</h1>\n" + img_html + parts[1]
            else:
                formatted_body = img_html + formatted_body
        next_link_html = ""
        if idx < len(chapter_slugs) - 1:
            next_slug = chapter_slugs[idx + 1]
            next_label = chapter_labels[idx + 1]
            next_link_html = f"""
            <div class="next-chapter-container">
                <a href="#{next_slug}" class="next-chapter-link">Próximo: {next_label}</a>
            </div>"""
        chapters_content.append(f"""
        <article id="{slug}" class="chapter-section">
            {formatted_body}
            {next_link_html}
        </article>""")

    html_middle = """
        </ul>
    </nav>

    <main class="content-container">
        <section id="cover" class="cover-section">
            <img src="capa.jpg" alt="Capa do livro A Rebeldia da Mecatrônica" class="cover-image" width="1024" height="1536">
            <div class="cover-copy">
                <h1 class="cover-title">A Rebeldia da Mecatrônica</h1>
                <p class="cover-subtitle">Romance Instrutivo de Tecnologia e Sociedade</p>
                <p class="cover-author">Christian Vladimir Uhdre Mulato</p>
                <a href="app/" class="app-cta-btn">Entrar no Universo Rebeldia</a>
                <a href="romance_instrutivo.pdf" class="download-cta-btn" download>Baixar PDF para leitura offline</a>
                <div class="dedication">
                    Dedicado à minha família, cujo apoio silencioso e inabalável estruturou
                    o caminho para que este projeto de vida ganhasse o mundo.<br/><br/>
                    E a todos os jovens engenheiros e mentes inquietas que, diante de estradas de barro
                    ou algoritmos complexos, escolhem o caminho da persistência técnica e do
                    despertar lúdico como ferramentas reais de emancipação.
                </div>
            </div>
        </section>
"""

    html_end = """
    </main>
    <script>
        const menuBtn = document.getElementById('menuBtn');
        const drawer = document.getElementById('drawer');
        const overlay = document.getElementById('overlay');
        const links = document.querySelectorAll('.nav-drawer a');
        const sections = document.querySelectorAll('#cover, .chapter-section');
        const progress = document.getElementById('readProgress');
        const desktopMq = window.matchMedia('(min-width: 1024px)');

        function isDesktop() { return desktopMq.matches; }
        function closeMenu() {
            drawer.classList.remove('open');
            overlay.classList.remove('show');
        }
        function toggleMenu() {
            if (isDesktop()) return;
            drawer.classList.toggle('open');
            overlay.classList.toggle('show');
        }
        menuBtn.addEventListener('click', toggleMenu);
        overlay.addEventListener('click', closeMenu);

        links.forEach(link => {
            link.addEventListener('click', (e) => {
                const target = document.querySelector(link.getAttribute('href'));
                if (!target) return;
                e.preventDefault();
                if (!isDesktop()) closeMenu();
                const top = target.getBoundingClientRect().top + window.pageYOffset - 72;
                window.scrollTo({ top, behavior: 'smooth' });
                history.pushState(null, '', link.getAttribute('href'));
            });
        });

        function onScroll() {
            const doc = document.documentElement;
            const max = doc.scrollHeight - doc.clientHeight;
            progress.style.width = (max > 0 ? (doc.scrollTop / max) * 100 : 0) + '%';
            let current = 'cover';
            sections.forEach(section => {
                if (window.pageYOffset >= section.offsetTop - 140) current = section.id;
            });
            links.forEach(link => {
                link.classList.toggle('active', link.getAttribute('href') === '#' + current);
            });
        }
        window.addEventListener('scroll', onScroll, { passive: true });
        desktopMq.addEventListener('change', () => { if (isDesktop()) closeMenu(); });
    </script>
</body>
</html>
"""

    os.makedirs(os.path.dirname(OUTPUT_HTML), exist_ok=True)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_start + "\n".join(menu_items) + html_middle + "\n".join(chapters_content) + html_end)

    docs_dir = os.path.join(WORKSPACE_DIR, "docs")
    capa_src = os.path.join(WORKSPACE_DIR, "capa.png")
    if os.path.exists(capa_src):
        shutil.copy2(capa_src, os.path.join(docs_dir, "capa.png"))
        try:
            from PIL import Image
            cover = Image.open(capa_src).convert("RGB")
            cover.save(os.path.join(docs_dir, "capa.jpg"), "JPEG", quality=85, optimize=True)
        except Exception as e:
            print(f"Aviso: não foi possível gerar capa.jpg ({e})")

    docs_imagens_dir = os.path.join(docs_dir, "imagens")
    os.makedirs(docs_imagens_dir, exist_ok=True)
    imagens_dir = os.path.join(WORKSPACE_DIR, "imagens")
    if os.path.exists(imagens_dir):
        for item in os.listdir(imagens_dir):
            s_file = os.path.join(imagens_dir, item)
            if os.path.isfile(s_file):
                shutil.copy2(s_file, os.path.join(docs_imagens_dir, item))

    print(f"HTML responsivo compilado em: {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
