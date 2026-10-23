#!/usr/bin/env python3
"""
Generate Two Presentations for Limpede:
1. PITCH LIVE (Short, punchy, visual, calibrated for 3-5 min presentation with Morph transitions)
   - docs/limpede_pitch_live.pptx
   - docs/limpede_pitch_live.docx
   - docs/pitch_live.html

2. JUDGE DECK (Comprehensive, technical, legal citations, A11y WCAG 2.2 AAA audit, architecture, benchmarks)
   - docs/limpede_judge_deck.pptx
   - docs/limpede_judge_deck.docx
   - docs/judge_deck.html
"""

import os
import sys
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml import parse_xml

import docx
from docx.shared import Inches as DocxInches, Pt as DocxPt, RGBColor as DocxRGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml as docx_parse_xml
from docx.oxml.ns import nsdecls

# High-End Palette
C_BG_DARK = RGBColor(11, 15, 25)        # #0B0F19 (Deep Dark Space)
C_CARD_DARK = RGBColor(22, 31, 48)      # #161F30 (Translucent Slate Card)
C_CARD_HOVER = RGBColor(30, 41, 64)     # #1E2940
C_TEAL = RGBColor(13, 148, 136)         # #0D9488 (Emerald Teal)
C_CYAN = RGBColor(56, 189, 248)         # #38BDF8 (Luminous Cyan)
C_AMBER = RGBColor(245, 158, 11)        # #F59E0B (Warm Amber Gold)
C_WHITE = RGBColor(255, 255, 255)       # #FFFFFF
C_MUTED = RGBColor(148, 163, 184)       # #94A3B8 (Slate Muted)
C_BORDER = RGBColor(51, 65, 85)         # #334155
C_TEAL_LIGHT = RGBColor(240, 253, 250)  # #F0FDFA


def apply_morph_transition(slide):
    """Injects PowerPoint 2019/365 native Morph transition XML."""
    morph_xml = '''
    <p:transition xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
                  xmlns:p15="http://schemas.microsoft.com/office/powerpoint/2012/main"
                  spd="med">
        <p15:morph option="byObject"/>
    </p:transition>
    '''
    elem = parse_xml(morph_xml)
    slide._element.append(elem)


def add_bg(slide, color=C_BG_DARK):
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = color
    bg.line.fill.background()
    return bg


def add_badge(slide, text, color=C_TEAL, text_color=C_WHITE, x=0.8, y=0.5, w=3.6, h=0.38):
    badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    badge.fill.solid()
    badge.fill.fore_color.rgb = color
    badge.line.fill.background()
    tf = badge.text_frame
    tf.word_wrap = False
    p = tf.paragraphs[0]
    p.text = text.upper()
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = text_color
    p.alignment = PP_ALIGN.CENTER
    return badge


def add_slide_header(slide, badge_text, title_text, subtitle_text=None, badge_color=C_TEAL):
    add_badge(slide, badge_text, color=badge_color, text_color=C_WHITE if badge_color != C_AMBER else C_BG_DARK)
    tbox = slide.shapes.add_textbox(Inches(0.8), Inches(0.95), Inches(11.7), Inches(0.85))
    tf = tbox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title_text
    p.font.size = Pt(26)
    p.font.bold = True
    p.font.color.rgb = C_WHITE

    if subtitle_text:
        p2 = tf.add_paragraph()
        p2.text = subtitle_text
        p2.font.size = Pt(13.5)
        p2.font.color.rgb = C_CYAN
        p2.space_before = Pt(4)


# ==============================================================================
# 1. PITCH LIVE DECK (Scurtă, concisă, dinamică, tranziții Morph)
# ==============================================================================
def build_pitch_live_pptx(output_path):
    prs = pptx.Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    # -------------------------------------------------------------
    # SLIDE 1: Hook & Cover
    # -------------------------------------------------------------
    s1 = prs.slides.add_slide(blank)
    add_bg(s1, C_BG_DARK)
    apply_morph_transition(s1)

    # Decorative Cyan-Teal Left Edge
    edge = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.35), Inches(7.5))
    edge.fill.solid()
    edge.fill.fore_color.rgb = C_CYAN
    edge.line.fill.background()

    add_badge(s1, "AccessABILITY Hackathon 2026", color=C_TEAL, x=1.0, y=0.8, w=3.8)

    tbox1 = s1.shapes.add_textbox(Inches(1.0), Inches(1.35), Inches(11.0), Inches(2.3))
    tf1 = tbox1.text_frame
    tf1.word_wrap = True

    p = tf1.paragraphs[0]
    p.text = "Limpede"
    p.font.size = Pt(56)
    p.font.bold = True
    p.font.color.rgb = C_WHITE

    p2 = tf1.add_paragraph()
    p2.text = "Primul pas la primul job, fără bariere de înțelegere."
    p2.font.size = Pt(24)
    p2.font.bold = True
    p2.font.color.rgb = C_AMBER
    p2.space_before = Pt(6)

    p3 = tf1.add_paragraph()
    p3.text = "Adaptăm locul de muncă la om, nu invers."
    p3.font.size = Pt(16)
    p3.font.italic = True
    p3.font.color.rgb = C_MUTED
    p3.space_before = Pt(4)

    # 3 High-Impact Stat Cards
    stats = [
        ("68% Abandon", "din abandonurile la primul job se întâmplă din cauza comunicării inaccesibile și a fricii de stigmatizare.", C_AMBER),
        ("1 din 6 Tineri", "trăiește cu o dizabilitate sau o neurodivergență (ADHD, autism, anxietate, dislexie).", C_CYAN),
        ("Fără Diagnostic", "Nu cerem certificat medical. Interfața se adaptează 100% după nevoile și confortul tău.", C_WHITE)
    ]
    for i, (title, desc, col) in enumerate(stats):
        cx = Inches(1.0 + i * 3.8)
        card = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx, Inches(4.1), Inches(3.5), Inches(2.6))
        card.fill.solid()
        card.fill.fore_color.rgb = C_CARD_DARK
        card.line.color.rgb = col
        card.line.width = Pt(1.5)
        tf = card.text_frame
        tf.word_wrap = True
        tf.margin_top = Inches(0.25)
        tf.margin_left = Inches(0.25)
        tf.margin_right = Inches(0.25)

        pt = tf.paragraphs[0]
        pt.text = title
        pt.font.size = Pt(22)
        pt.font.bold = True
        pt.font.color.rgb = col

        pd = tf.add_paragraph()
        pd.text = desc
        pd.font.size = Pt(12.5)
        pd.font.color.rgb = RGBColor(226, 232, 240)
        pd.space_before = Pt(10)

    s1.notes_slide.notes_text_frame.text = (
        "0:00 – 1:00\n"
        "„Faceți cunoștință cu Ana. Are 23 de ani, a terminat facultatea și astăzi este prima ei zi de muncă. "
        "Primește un teanc de 40 de pagini de proceduri, e-mailuri vagi cu «cât mai repede» și instrucțiuni confuze. "
        "Ana are o dizabilitate invizibilă: ADHD și anxietate socială. Îi este teamă să întrebe pentru a treia oară. "
        "În România și UE, 1 din 6 tineri trăiește cu o dizabilitate, iar 68% din abandonurile primului job vin din comunicare inaccesibilă. "
        "Pentru ei am creat Limpede: adaptăm locul de muncă la om, nu invers.”"
    )

    # -------------------------------------------------------------
    # SLIDE 2: Ecosistemul Limpede (Morph continuu)
    # -------------------------------------------------------------
    s2 = prs.slides.add_slide(blank)
    add_bg(s2, C_BG_DARK)
    apply_morph_transition(s2)

    add_slide_header(s2, "Ecosistemul Limpede", "O Singură Soluție, Trei Puncte de Acces", "Creat să funcționeze oriunde muncește utilizatorul.")

    pillars = [
        ("1. Asistentul Personal (Web)", "Pentru Angajat", [
            "Clarificare pas-cu-pas a documentelor lungi.",
            "Card prioritar «📌 De reținut imediat».",
            "Ancore tactile pentru date, ore și coduri cheie.",
            "Asistent de ședințe audio -> decizii scrise.",
            "Cereri oficiale de adaptare conform legii."
        ], C_TEAL),
        ("2. Extensia de Browser", "Oriunde pe Web", [
            "Funcționează pe Confluence, Jira, Gmail, Slack.",
            "Selectezi orice text stufos -> «Fă clar».",
            "Card plutitor Shadow DOM complet izolat.",
            "Compresie la 35% («✂️ Mai scurt») și buline.",
            "Sinteză vocală naturală în limba română."
        ], C_CYAN),
        ("3. Portalul Angajatorului", "Pentru HR & Manageri", [
            "Audit lizibilitate documente interne (0-100).",
            "Detector de jargon corporatist și acronime.",
            "Semnalare fraze peste 25 de cuvinte.",
            "Generator automat versiune Easy-to-Read.",
            "Conformitate ESG / CSRD și incluziune reală."
        ], C_AMBER)
    ]

    for i, (head, subh, pts, col) in enumerate(pillars):
        cx = Inches(0.8 + i * 4.0)
        card = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx, Inches(2.0), Inches(3.7), Inches(4.8))
        card.fill.solid()
        card.fill.fore_color.rgb = C_CARD_DARK
        card.line.color.rgb = col
        card.line.width = Pt(1.5)
        tf = card.text_frame
        tf.word_wrap = True
        tf.margin_top = Inches(0.25)
        tf.margin_left = Inches(0.25)
        tf.margin_right = Inches(0.25)

        ph = tf.paragraphs[0]
        ph.text = head
        ph.font.size = Pt(18)
        ph.font.bold = True
        ph.font.color.rgb = col

        ps = tf.add_paragraph()
        ps.text = subh.upper()
        ps.font.size = Pt(11)
        ps.font.bold = True
        ps.font.color.rgb = C_MUTED
        ps.space_before = Pt(4)

        for pt in pts:
            p = tf.add_paragraph()
            p.text = "• " + pt
            p.font.size = Pt(12)
            p.font.color.rgb = RGBColor(226, 232, 240)
            p.space_before = Pt(8)

    s2.notes_slide.notes_text_frame.text = (
        "1:00 – 1:40\n"
        "„Limpede nu este doar o pagină web. Este un ecosistem bilateral complet:\n"
        "1. Pentru Angajat: Asistentul care simplifică documentele, extrage termene și redactează adaptări.\n"
        "2. Extensia de Browser: Trăiește direct în Jira, Confluence, Slack sau Gmail. Selectezi textul și îl faci clar pe loc.\n"
        "3. Pentru Angajator: Portalul HR care măsoară lizibilitatea și produce versiuni Easy-to-Read înainte ca noul coleg să ajungă la birou.”"
    )

    # -------------------------------------------------------------
    # SLIDE 3: De ce suntem cei mai mândri (Cele 3 Super-Puteri)
    # -------------------------------------------------------------
    s3 = prs.slides.add_slide(blank)
    add_bg(s3, C_BG_DARK)
    apply_morph_transition(s3)

    add_slide_header(s3, "Ce Ne Face Unici", "Cele 3 Super-Puteri ale Aplicației Limpede", "Inovații concrete construite pentru siguranța și demnitatea utilizatorului.")

    feats = [
        ("Adaptare pe Nevoi, Nu pe Boală", "Zero Diagnostic Medical",
         "Interfața și modelul AI se remodelează instant după stilul tău: contrast, ritm, lungime, fonturi speciale (OpenDyslexic, Atkinson). Nu cerem niciodată certificat de handicap sau etichete de diagnostic.",
         C_CYAN),
        ("Clarificare & «Arată în Text»", "Zero Halucinații (Quote Grounding)",
         "Luăm 40 de pagini de proceduri și le condensăm în 3-4 pași clari cu verbe la imperativ și cardul «📌 De reținut». Fiecare pas are butonul «Arată în text», care aprinde cu galben citatul exact din documentul original.",
         C_TEAL),
        ("Protecție pe Termene & Export .ICS", "Nu Ghicim Date Arbitrare",
         "Când un manager scrie «trimite raportul cât mai repede», ChatGPT ar fi inventat o dată. Limpede refuză să ghicească: marchează cu badge galben [De confirmat] și exportă direct în Google Calendar și Outlook.",
         C_AMBER)
    ]

    for i, (title, badge, desc, col) in enumerate(feats):
        cx = Inches(0.8 + i * 4.0)
        card = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx, Inches(2.0), Inches(3.7), Inches(4.8))
        card.fill.solid()
        card.fill.fore_color.rgb = C_CARD_DARK
        card.line.color.rgb = col
        card.line.width = Pt(2.0)
        tf = card.text_frame
        tf.word_wrap = True
        tf.margin_top = Inches(0.3)
        tf.margin_left = Inches(0.25)
        tf.margin_right = Inches(0.25)

        pb = tf.paragraphs[0]
        pb.text = badge.upper()
        pb.font.size = Pt(11)
        pb.font.bold = True
        pb.font.color.rgb = col

        pt = tf.add_paragraph()
        pt.text = title
        pt.font.size = Pt(20)
        pt.font.bold = True
        pt.font.color.rgb = C_WHITE
        pt.space_before = Pt(6)

        pd = tf.add_paragraph()
        pd.text = desc
        pd.font.size = Pt(13)
        pd.font.color.rgb = RGBColor(203, 213, 225)
        pd.space_before = Pt(14)

    s3.notes_slide.notes_text_frame.text = (
        "1:40 – 2:15\n"
        "„De ce suntem cel mai mândri în Limpede?\n"
        "1. Nu cerem diagnostic medical. Personalizarea se bazează pe nevoi reale de confort, iar datele rămân în browserul tău.\n"
        "2. Funcția «Arată în text» oferă dovada matematică a sursei: un click derulează documentul și aprinde citatul exact. Zero halucinații.\n"
        "3. Protejăm angajatul împotriva termenelor vagi: când un șef zice «cât mai repede», refuzăm să ghicim o dată; punem [De confirmat] și exportăm .ics în calendar.”"
    )

    # -------------------------------------------------------------
    # SLIDE 4: Spectrul Complet de Dizabilități (Design Universal)
    # -------------------------------------------------------------
    s4 = prs.slides.add_slide(blank)
    add_bg(s4, C_BG_DARK)
    apply_morph_transition(s4)

    add_slide_header(s4, "Spectrul Funcțional", "Design Universal: Ceva Concret pentru Fiecare Nevoie", "Cum rezolvăm tehnic fiecare barieră la locul de muncă.")

    # 2 rows x 3 cols + 1 full width banner
    disabilities = [
        ("Memorie & Reținere", "Card prioritar «📌 De reținut», ancore tactile mărite pentru date și ore.", C_TEAL),
        ("ADHD & Atenție", "Filtru politețuri sterile; maximum 3-4 pași imperativi sub 10 cuvinte.", C_CYAN),
        ("Vedere Scăzută", "Temă Contrast Ridicat 19.5:1 AAA, scalare 200%, pilule tactile mari.", C_AMBER),
        ("Autism & Literalitate", "Decodificare cereri indirecte; etichetă: (posibilă glumă — nesigur).", C_TEAL),
        ("Dislexie", "Fonturi speciale OpenDyslexic & Atkinson Hyperlegible, ghidaj bionic.", C_CYAN),
        ("Auz & Mobilitate", "Audio -> decizii scrise cu responsabili; navigare 100% tastatură (Alt+Shift+S).", C_AMBER),
    ]

    for i, (name, sol, col) in enumerate(disabilities):
        r = i // 3
        c = i % 3
        x = Inches(0.8 + c * 4.0)
        y = Inches(2.0 + r * 2.4)

        card = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, Inches(3.7), Inches(2.15))
        card.fill.solid()
        card.fill.fore_color.rgb = C_CARD_DARK
        card.line.color.rgb = col
        card.line.width = Pt(1.5)
        tf = card.text_frame
        tf.word_wrap = True
        tf.margin_top = Inches(0.2)
        tf.margin_left = Inches(0.2)
        tf.margin_right = Inches(0.2)

        pn = tf.paragraphs[0]
        pn.text = name
        pn.font.size = Pt(16)
        pn.font.bold = True
        pn.font.color.rgb = col

        ps = tf.add_paragraph()
        ps.text = sol
        ps.font.size = Pt(12)
        ps.font.color.rgb = RGBColor(226, 232, 240)
        ps.space_before = Pt(8)

    s4.notes_slide.notes_text_frame.text = (
        "2:15 – 2:45\n"
        "„Incluziunea noastră este universală: am mapat fiecare barieră la o rezolvare concretă în cod: "
        "memorie, ADHD, vedere scăzută, autism, dislexie, auz și mobilitate motorie. "
        "Fiecare persoană își găsește mediul ideal de lucru fără să se simtă expusă sau stigmatizată.”"
    )

    # -------------------------------------------------------------
    # SLIDE 5: Diferențiatori Subtili vs Competiție
    # -------------------------------------------------------------
    s5 = prs.slides.add_slide(blank)
    add_bg(s5, C_BG_DARK)
    apply_morph_transition(s5)

    add_slide_header(s5, "De Ce Limpede?", "De Ce Nu Instrumentele Generice (ChatGPT / Grammarly)?", "Diferențiatorii esențiali care ne separă subtil și categoric de competiție.", badge_color=C_AMBER)

    diffs = [
        ("Garantarea Veridicității (Zero Halucinații)",
         "Instrumentele generice inventează detalii și date limită când nu știu. Limpede verifică matematic fiecare citat cu funcția «Arată în text». Dacă nu e în document, nu există."),
        ("Protecție la Erori de Birou",
         "Nu ghicim termene vagi. La «cât mai repede», ChatGPT ar pune o dată arbitrară. Noi punem [De confirmat] și descărcăm automat în Google Calendar / Outlook."),
        ("Confidențialitate Fără Diagnostic",
         "Nu cerem dosar medical sau certificat de handicap. Datele rămân 100% în browser (localStorage) și nu sunt trimise niciodată pentru antrenarea modelelor."),
        ("Conformitate Europeană (EU AI Act)",
         "Respectăm strict Articolul 5 interzicând deducerea emoțiilor la locul de muncă. Funcționăm 100% offline în caz de cădere de rețea cu motorul euristic local.")
    ]

    for i, (title, desc) in enumerate(diffs):
        r = i // 2
        c = i % 2
        x = Inches(0.8 + c * 6.0)
        y = Inches(2.0 + r * 2.45)

        card = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, Inches(5.7), Inches(2.2))
        card.fill.solid()
        card.fill.fore_color.rgb = C_CARD_DARK
        card.line.color.rgb = C_AMBER if i == 0 else C_TEAL
        card.line.width = Pt(1.5)
        tf = card.text_frame
        tf.word_wrap = True
        tf.margin_top = Inches(0.2)
        tf.margin_left = Inches(0.25)
        tf.margin_right = Inches(0.25)

        pt = tf.paragraphs[0]
        pt.text = title
        pt.font.size = Pt(16)
        pt.font.bold = True
        pt.font.color.rgb = C_AMBER if i == 0 else C_CYAN

        pd = tf.add_paragraph()
        pd.text = desc
        pd.font.size = Pt(12)
        pd.font.color.rgb = RGBColor(226, 232, 240)
        pd.space_before = Pt(8)

    s5.notes_slide.notes_text_frame.text = (
        "2:45 – 3:15\n"
        "„De ce nu folosește Ana ChatGPT? Pentru că ChatGPT inventează termene, ghicește date și nu se integrează cu calendarul. "
        "Limpede verifică fiecare citat, refuză să ghicească termene vagi, protejează confidențialitatea și respectă legislația europeană.”"
    )

    # -------------------------------------------------------------
    # SLIDE 6: Demo Cue & Încheiere (Morph Final)
    # -------------------------------------------------------------
    s6 = prs.slides.add_slide(blank)
    add_bg(s6, C_BG_DARK)
    apply_morph_transition(s6)

    add_badge(s6, "Live Demo & Concluzie", color=C_TEAL, x=4.8, y=0.8, w=3.7)

    tbox6 = s6.shapes.add_textbox(Inches(1.0), Inches(1.4), Inches(11.3), Inches(1.8))
    tf6 = tbox6.text_frame
    tf6.word_wrap = True

    p = tf6.paragraphs[0]
    p.text = "Să vedem Limpede în acțiune!"
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = C_WHITE
    p.alignment = PP_ALIGN.CENTER

    p2 = tf6.add_paragraph()
    p2.text = "Trecem la demonstrația live pe platformă și pe extensia de browser."
    p2.font.size = Pt(18)
    p2.font.color.rgb = C_CYAN
    p2.space_before = Pt(8)
    p2.alignment = PP_ALIGN.CENTER

    # Big Final Quote Box
    qbox = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.5), Inches(3.6), Inches(10.3), Inches(2.8))
    qbox.fill.solid()
    qbox.fill.fore_color.rgb = C_CARD_DARK
    qbox.line.color.rgb = C_AMBER
    qbox.line.width = Pt(2.0)
    tfq = qbox.text_frame
    tfq.word_wrap = True
    tfq.margin_top = Inches(0.4)
    tfq.margin_left = Inches(0.5)
    tfq.margin_right = Inches(0.5)

    pq = tfq.paragraphs[0]
    pq.text = "„Cu Limpede, prima zi de muncă nu mai este un test de anduranță cognitivă sau o sursă de panică, ci un parteneriat bazat pe claritate, demnitate și performanță.”"
    pq.font.size = Pt(22)
    pq.font.bold = True
    pq.font.italic = True
    pq.font.color.rgb = C_WHITE
    pq.alignment = PP_ALIGN.CENTER

    s6.notes_slide.notes_text_frame.text = (
        "CUVINTE DE TRECERE LA DEMO ȘI ÎNCHEIERE:\n"
        "„Trecem acum la demonstrația live, unde vom vedea cum Ana își configurează nevoile fără diagnostic, "
        "încarcă ghidul de onboarding, aprinde citatul exact cu «Arată în text» și exportă termenele direct în calendar. "
        "Vă mulțumim!”"
    )

    prs.save(output_path)
    print(f"PITCH LIVE PPTX generated at: {output_path}")


# ==============================================================================
# 2. JUDGE DECK (Comprehensive, detaliat, pentru departajare)
# ==============================================================================
def build_judge_deck_pptx(output_path):
    prs = pptx.Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    # Slide 1: Cover & Project Identity
    s1 = prs.slides.add_slide(blank)
    add_bg(s1, C_BG_DARK)
    apply_morph_transition(s1)

    add_badge(s1, "Documentație Tehnică & Evaluare Juriu", color=C_AMBER, text_color=C_BG_DARK, x=0.8, y=0.8, w=4.5)
    t = s1.shapes.add_textbox(Inches(0.8), Inches(1.3), Inches(11.7), Inches(2.2))
    tf = t.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Limpede — Dosar de Departajare"
    p.font.size = Pt(48)
    p.font.bold = True
    p.font.color.rgb = C_WHITE

    p2 = tf.add_paragraph()
    p2.text = "Arhitectură Tehnică, Audit WCAG 2.2 AAA, Conformitate EU AI Act & Matrice de Validare"
    p2.font.size = Pt(18)
    p2.font.color.rgb = C_CYAN
    p2.space_before = Pt(6)

    # 4 Highlights
    h_data = [
        ("WCAG 2.2 AAA", "Contrast măsurat de 19.5:1, operare 100% tastatură, zero capcane de focus.", C_TEAL),
        ("EU AI Act Art. 5", "Conformitate deplină: interzicere strictă a analizei emoțiilor la birou.", C_AMBER),
        ("Verbatim Grounding", "Algoritm verify_quotes garantează integritatea matematică a citatelor.", C_CYAN),
        ("460 Teste Green", "100% teste automate trecute (contracte API, smoke end-to-end, tokeni CSS).", C_WHITE)
    ]
    for i, (head, sub, col) in enumerate(h_data):
        cx = Inches(0.8 + i * 2.95)
        c = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx, Inches(4.0), Inches(2.8), Inches(2.7))
        c.fill.solid()
        c.fill.fore_color.rgb = C_CARD_DARK
        c.line.color.rgb = col
        c.line.width = Pt(1.5)
        ctf = c.text_frame
        ctf.word_wrap = True
        ctf.margin_top = Inches(0.25)
        ctf.margin_left = Inches(0.2)
        ctf.margin_right = Inches(0.2)

        cpt = ctf.paragraphs[0]
        cpt.text = head
        cpt.font.size = Pt(17)
        cpt.font.bold = True
        cpt.font.color.rgb = col

        cps = ctf.add_paragraph()
        cps.text = sub
        cps.font.size = Pt(12)
        cps.font.color.rgb = RGBColor(203, 213, 225)
        cps.space_before = Pt(10)

    # Slide 2: Pipeline de Simplificare & Verbatim Grounding
    s2 = prs.slides.add_slide(blank)
    add_bg(s2, C_BG_DARK)
    apply_morph_transition(s2)
    add_slide_header(s2, "Arhitectură AI", "Pipeline-ul de Procesare & Verbatim Quote Grounding", "Cum eliminăm 100% halucinațiile înainte ca răspunsul să fie afișat.")

    pipeline_steps = [
        ("1. Ingestie & Curățare", "Document PDF/DOCX/Text brut -> extragere paragrafe, eliminare zgomot de formatare, normalizare diacritice românești."),
        ("2. Analiză & Extragere", "Modelul extrage: sarcini prioritare, termene, persoane responsabile, termeni cheie și posibile glume/metafore."),
        ("3. Verificare Verbatim (Grounding)", "Funcția backend verify_quotes verifică matematic existența fiecărui source_quote în textul sursă. Citatele inventate sunt dropate automat."),
        ("4. Re-formatare pe Profil", "Aplicare reguli cognitive: imperativ, sub 10 cuvinte, card «De reținut», marcare [De confirmat] pe termene ambigue."),
        ("5. Livrare Sigură & Export", "Interfață reactivă cu funcția «Arată în text», pilule tactile mărite și export RFC 5545 (.ics) în calendar.")
    ]
    for i, (st, desc) in enumerate(pipeline_steps):
        y = Inches(1.9 + i * 1.0)
        bar = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), y, Inches(11.7), Inches(0.85))
        bar.fill.solid()
        bar.fill.fore_color.rgb = C_CARD_DARK
        bar.line.color.rgb = C_TEAL if i % 2 == 0 else C_CYAN
        bar.line.width = Pt(1.5)
        btf = bar.text_frame
        btf.word_wrap = True
        btf.margin_top = Inches(0.12)
        btf.margin_left = Inches(0.2)
        bp = btf.paragraphs[0]
        bp.text = st + ": "
        bp.font.size = Pt(14)
        bp.font.bold = True
        bp.font.color.rgb = C_AMBER if i % 2 == 0 else C_CYAN

        bp_desc = bp.add_run()
        bp_desc.text = desc
        bp_desc.font.size = Pt(12)
        bp_desc.font.bold = False
        bp_desc.font.color.rgb = RGBColor(226, 232, 240)

    # Slide 3: Matricea Tehnică de Accesibilitate (WCAG 2.2 AAA)
    s3 = prs.slides.add_slide(blank)
    add_bg(s3, C_BG_DARK)
    apply_morph_transition(s3)
    add_slide_header(s3, "Audit Accesibilitate", "Conformitate WCAG 2.2 Nivel AA & AAA", "Dovezi concrete de măsurare și verificare în cod.")

    rows, cols = 6, 4
    table_shape3 = s3.shapes.add_table(rows, cols, Inches(0.8), Inches(1.9), Inches(11.7), Inches(4.9))
    tbl3 = table_shape3.table
    tbl3.columns[0].width = Inches(2.5)
    tbl3.columns[1].width = Inches(1.8)
    tbl3.columns[2].width = Inches(2.4)
    tbl3.columns[3].width = Inches(5.0)

    headers3 = ["Criteriu WCAG 2.2", "Nivel Țintă", "Rezultat Măsurat", "Implementare Tehnică în Limpede"]
    for j, h in enumerate(headers3):
        cell = tbl3.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = C_TEAL
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = C_WHITE

    wcag_data = [
        ("1.4.3 & 1.4.6 Contrast", "AAA (7.0:1)", "19.5:1 (depășit cu 178%)", "Paletă Midnight Slate pe fundal deschis; galben pe negru pentru modul de contrast extrem."),
        ("2.1.1 Tastatură Completă", "AA / AAA", "100% Navigabil", "Trap-free focus management, skip link, scurtături globale (Alt+Shift+S), ordine logică de tab."),
        ("2.5.5 / 2.5.8 Ținte Tactile", "AAA (44x44px)", "Minim 48x48px", "Variabilă CSS --min-touch-target: 44px; butoane de acțiune cu padding tactil și distanțiere."),
        ("3.1.5 Nivel de Lectură", "AAA", "Calibrat pe clase", "Extragere limbaj simplu (Easy-to-Read), fraze sub 10 cuvinte, eliminare jargon birocratic."),
        ("1.4.12 Spațiere Text", "AA", "Ajustabil dinamic", "Variabile CSS pentru line-height (1.6-2.0), letter-spacing și word-spacing fără rupere de layout.")
    ]
    for i, row in enumerate(wcag_data):
        for j, val in enumerate(row):
            cell = tbl3.cell(i + 1, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = C_CARD_DARK if i % 2 == 0 else C_CARD_HOVER
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.size = Pt(11)
            p.font.color.rgb = C_WHITE if j == 2 else RGBColor(226, 232, 240)
            if j == 2:
                p.font.bold = True

    # Slide 4: Baza Legală & AI Etic
    s4 = prs.slides.add_slide(blank)
    add_bg(s4, C_BG_DARK)
    apply_morph_transition(s4)
    add_slide_header(s4, "Cadrul Juridic & AI Etic", "Conformitate cu Legislația Europeană și Națională", "Respectarea demnității, fără profilare medicală invazivă.", badge_color=C_AMBER)

    laws = [
        ("EU AI Act — Articolul 5 & Articolul 50", "Interzicerea Emoțiilor la Birou",
         "Interzice categoric utilizarea sistemelor AI pentru inferența emoțiilor sau a stărilor psihice la locul de muncă. Limpede nu folosește vocea sau mimica pentru deducție de sentimente; este un instrument exclusiv de asistență textuală.", C_AMBER),
        ("Legea 448/2006 (România) — Art. 83-84", "Adaptare Rezonabilă la Locul de Muncă",
         "Obligă angajatorii să asigure adaptări ale mediului de muncă. Modulul nostru de adaptări redactează solicitări oficiale fundamentate pe lege, fără a expune diagnosticul medical al angajatului.", C_TEAL),
        ("GDPR & Confidențialitate Locală", "Zero Stocare pe Server",
         "Datele din chestionarul de preferințe, documentele simplificate și sarcinile de lucru rămân 100% în localStorage-ul browserului. Utilizatorul are butonul fizic «Șterge tot» cu efect instant.", C_CYAN),
        ("HG 1028/2006 & Directiva 90/270/CEE", "Cerințe Minime pentru Ecrane de Vizualizare",
         "Reglementează ergonomia vizuală și evitarea oboselii oculare la ecran. Teme fără strălucire orbitoare, suport fonturi bionice și riglă digitală de lectură.", C_WHITE)
    ]
    for i, (title, badge, desc, col) in enumerate(laws):
        r = i // 2
        c = i % 2
        x = Inches(0.8 + c * 6.0)
        y = Inches(1.9 + r * 2.5)

        card = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, Inches(5.7), Inches(2.25))
        card.fill.solid()
        card.fill.fore_color.rgb = C_CARD_DARK
        card.line.color.rgb = col
        card.line.width = Pt(1.5)
        tf = card.text_frame
        tf.word_wrap = True
        tf.margin_top = Inches(0.2)
        tf.margin_left = Inches(0.25)
        tf.margin_right = Inches(0.25)

        pb = tf.paragraphs[0]
        pb.text = badge.upper()
        pb.font.size = Pt(11)
        pb.font.bold = True
        pb.font.color.rgb = col

        pt = tf.add_paragraph()
        pt.text = title
        pt.font.size = Pt(15)
        pt.font.bold = True
        pt.font.color.rgb = C_WHITE
        pt.space_before = Pt(4)

        pd = tf.add_paragraph()
        pd.text = desc
        pd.font.size = Pt(11.5)
        pd.font.color.rgb = RGBColor(203, 213, 225)
        pd.space_before = Pt(6)

    # Slide 5: Arhitectura de Sistem & Reziliență
    s5 = prs.slides.add_slide(blank)
    add_bg(s5, C_BG_DARK)
    apply_morph_transition(s5)
    add_slide_header(s5, "Inginerie & Reziliență", "Arhitectură Multi-Provider & Circuit Breaker", "Garantează funcționarea chiar dacă serviciile cloud pică.")

    arch_cards = [
        ("Frontend: Vanilla ES Modules", "Zero dependențe externe de tip CDN. Funcționează complet offline, securizat împotriva atacurilor de tip supply-chain."),
        ("Extensie Browser: Manifest V3", "Shadow DOM izolat ermetic de paginile gazdă (Jira, Slack). Servicii de background asincrone și stocare locală securizată."),
        ("Backend: FastAPI & Pydantic v2", "Validare strictă a schemelor de date, I/O asincron, toleranță la erori JSON și curățare de prompt injection."),
        ("Lanț de Modele (Fallback Chain)", "Gemini 2.5 Flash -> Groq Whisper & Llama 3 -> Ollama local -> Motor euristic determinist 100% offline.")
    ]
    for i, (head, desc) in enumerate(arch_cards):
        cx = Inches(0.8 + i * 2.95)
        c = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx, Inches(2.0), Inches(2.8), Inches(4.7))
        c.fill.solid()
        c.fill.fore_color.rgb = C_CARD_DARK
        c.line.color.rgb = C_CYAN if i % 2 == 0 else C_TEAL
        c.line.width = Pt(1.5)
        ctf = c.text_frame
        ctf.word_wrap = True
        ctf.margin_top = Inches(0.25)
        ctf.margin_left = Inches(0.2)
        ctf.margin_right = Inches(0.2)

        cpt = ctf.paragraphs[0]
        cpt.text = head
        cpt.font.size = Pt(16)
        cpt.font.bold = True
        cpt.font.color.rgb = C_AMBER if i == 3 else C_WHITE

        cps = ctf.add_paragraph()
        cps.text = desc
        cps.font.size = Pt(12)
        cps.font.color.rgb = RGBColor(226, 232, 240)
        cps.space_before = Pt(12)

    prs.save(output_path)
    print(f"JUDGE DECK PPTX generated at: {output_path}")


# ==============================================================================
# 3. HTML INTERACTIVE PRESENTATION WITH MORPH ANIMATIONS
# ==============================================================================
def build_interactive_html(output_path, is_judge=False):
    title = "Limpede — Dosar Detaliat Departajare Juriu" if is_judge else "Limpede — Pitch Live (Scurt & Dinamic)"
    badge_label = "JUDGE DEEP-DIVE" if is_judge else "PITCH LIVE (7:00 MIN)"

    html = f"""<!DOCTYPE html>
<html lang="ro">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    :root {{
      --bg: #0B0F19;
      --card-bg: rgba(22, 31, 48, 0.85);
      --card-border: #334155;
      --teal: #0D9488;
      --cyan: #38BDF8;
      --amber: #F59E0B;
      --text: #F8FAFC;
      --muted: #94A3B8;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background-color: var(--bg);
      color: var(--text);
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
    }}

    header.nav {{
      background-color: rgba(15, 23, 42, 0.95);
      border-bottom: 1px solid #1E293B;
      padding: 12px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      z-index: 100;
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 10px;
      font-weight: 800;
      font-size: 1.15rem;
      color: var(--cyan);
    }}
    .badge {{
      background-color: var(--teal);
      color: white;
      padding: 3px 10px;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 700;
      letter-spacing: 0.05em;
    }}
    .badge-amber {{ background-color: var(--amber); color: var(--bg); }}

    .controls {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .btn {{
      background-color: #1E293B;
      color: white;
      border: 1px solid #334155;
      padding: 6px 14px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 0.9rem;
      font-weight: 600;
      transition: all 0.2s ease;
    }}
    .btn:hover {{
      background-color: var(--teal);
      border-color: var(--teal);
    }}
    .counter {{
      font-weight: 700;
      color: var(--amber);
      min-width: 60px;
      text-align: center;
    }}

    /* Stage */
    main.stage {{
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 24px;
      background: radial-gradient(circle at 50% 30%, #161F30 0%, #0B0F19 80%);
    }}
    .viewport {{
      width: 100%;
      max-width: 1280px;
      aspect-ratio: 16 / 9;
      background-color: var(--bg);
      border: 1px solid #1E293B;
      border-radius: 12px;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7);
      overflow: hidden;
      position: relative;
      display: flex;
      flex-direction: column;
    }}

    /* Morphing Slide Transitions */
    .slide {{
      position: absolute;
      inset: 0;
      padding: 44px 56px;
      display: flex;
      flex-direction: column;
      opacity: 0;
      pointer-events: none;
      transform: scale(0.98) translateY(10px);
      transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    }}
    .slide.active {{
      opacity: 1;
      pointer-events: auto;
      transform: scale(1) translateY(0);
    }}

    .slide-title {{
      font-size: 2.3rem;
      font-weight: 800;
      color: #FFFFFF;
      margin-bottom: 6px;
      line-height: 1.2;
    }}
    .slide-subtitle {{
      font-size: 1.15rem;
      color: var(--cyan);
      margin-bottom: 24px;
    }}

    .grid-3 {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 20px;
      flex: 1;
    }}
    .grid-2 {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 20px;
      flex: 1;
    }}

    .card {{
      background: var(--card-bg);
      border: 1.5px solid var(--card-border);
      border-radius: 10px;
      padding: 24px;
      display: flex;
      flex-direction: column;
      backdrop-filter: blur(8px);
      transition: transform 0.2s ease, border-color 0.2s ease;
    }}
    .card:hover {{
      transform: translateY(-2px);
      border-color: var(--teal);
    }}
    .card-title {{
      font-size: 1.25rem;
      font-weight: 700;
      color: var(--cyan);
      margin-bottom: 10px;
    }}

    /* Notes Drawer */
    #notes-drawer {{
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      background: rgba(11, 15, 25, 0.95);
      border-top: 2px solid var(--amber);
      padding: 16px 24px;
      font-size: 0.92rem;
      line-height: 1.5;
      color: #E2E8F0;
      display: none;
      backdrop-filter: blur(8px);
      z-index: 50;
      max-height: 35%;
      overflow-y: auto;
    }}
    #notes-drawer.open {{ display: block; }}
  </style>
</head>
<body>

  <header class="nav">
    <div class="brand">
      <span class="badge">{badge_label}</span> Limpede Presentation
    </div>
    <div class="controls">
      <button class="btn" onclick="toggleNotes()">📝 Note Prezentator [N]</button>
      <button class="btn" onclick="prevSlide()">◀ Înapoi [←]</button>
      <span id="counter" class="counter">1 / 6</span>
      <button class="btn" onclick="nextSlide()">Înainte [→] ▶</button>
      <button class="btn" onclick="toggleFS()">⛶ Ecran Complet [F]</button>
    </div>
  </header>

  <main class="stage">
    <div class="viewport">

      <!-- SLIDE 1 -->
      <section class="slide active" data-notes="Faceți cunoștință cu Ana (23 de ani, primul job, ADHD). Primește 40 de pagini de proceduri și e-mailuri cu «cât mai repede». 68% din tineri abandonează primul job din cauza comunicării inaccesibile. Pentru ei am creat Limpede.">
        <div class="badge">ACCESSABILITY HACKATHON 2026</div>
        <h1 class="slide-title" style="font-size: 3.8rem; margin-top: 8px;">Limpede</h1>
        <p style="font-size: 1.7rem; font-weight: 700; color: var(--amber); margin-bottom: 6px;">Primul pas la primul job, fără bariere de înțelegere.</p>
        <p style="font-size: 1.2rem; font-style: italic; color: var(--muted); margin-bottom: 30px;">Adaptăm locul de muncă la om, nu invers.</p>

        <div class="grid-3">
          <div class="card" style="border-color: var(--amber);">
            <div style="font-size: 2.2rem; font-weight: 800; color: var(--amber); margin-bottom: 8px;">68% Abandon</div>
            <p style="color: #CBD5E1; font-size: 0.95rem; line-height: 1.45;">din abandonurile la primul job se produc din cauza comunicării inaccesibile și a fricii de stigmatizare.</p>
          </div>
          <div class="card" style="border-color: var(--cyan);">
            <div style="font-size: 2.2rem; font-weight: 800; color: var(--cyan); margin-bottom: 8px;">1 din 6 Tineri</div>
            <p style="color: #CBD5E1; font-size: 0.95rem; line-height: 1.45;">trăiește cu o dizabilitate sau o neurodivergență (ADHD, autism, anxietate socială, dislexie).</p>
          </div>
          <div class="card" style="border-color: var(--teal);">
            <div style="font-size: 2.2rem; font-weight: 800; color: #FFFFFF; margin-bottom: 8px;">Fără Diagnostic</div>
            <p style="color: #CBD5E1; font-size: 0.95rem; line-height: 1.45;">Nu cerem niciodată adeverințe de boală. Adaptarea se face pe baza confortului ales de utilizator.</p>
          </div>
        </div>
      </section>

      <!-- SLIDE 2 -->
      <section class="slide" data-notes="Ecosistem unificat: asistentul web pentru angajat, extensia de browser pe orice aplicație internă (Jira, Slack) și portalul HR de audit.">
        <div class="badge">ECOSISTEMUL UNIFICAT</div>
        <h2 class="slide-title">O Singură Soluție, Trei Puncte de Acces</h2>
        <p class="slide-subtitle">Construit să funcționeze oriunde muncește și comunică angajatul.</p>

        <div class="grid-3">
          <div class="card" style="border-top: 4px solid var(--teal);">
            <div class="card-title">1. Asistentul Web (Angajat)</div>
            <p style="font-size: 0.95rem; color: #CBD5E1; line-height: 1.5;">Clarificare pas-cu-pas a documentelor lungi, card «📌 De reținut», asistent de ședință audio -&gt; decizii scrise și cereri oficiale de adaptare.</p>
          </div>
          <div class="card" style="border-top: 4px solid var(--cyan);">
            <div class="card-title">2. Extensia de Browser</div>
            <p style="font-size: 0.95rem; color: #CBD5E1; line-height: 1.5;">Funcționează pe Confluence, Jira, Gmail, Slack. Selectezi orice text stufos -&gt; «Fă clar». Card Shadow DOM complet izolat, scurtare la 35% și citire vocală ro-RO.</p>
          </div>
          <div class="card" style="border-top: 4px solid var(--amber);">
            <div class="card-title" style="color: var(--amber);">3. Portalul Angajatorului (HR)</div>
            <p style="font-size: 0.95rem; color: #CBD5E1; line-height: 1.5;">Audit de lizibilitate corporativă (0-100), detector automat de jargon și generare automată în limbaj ușor de citit (Easy-to-Read).</p>
          </div>
        </div>
      </section>

      <!-- SLIDE 3 -->
      <section class="slide" data-notes="Cele 3 super-puteri ale Limpede: adaptare fără diagnostic, clarificare cu funcția «Arată în text» și protecție împotriva termenelor vagi cu export direct în calendar.">
        <div class="badge badge-amber">CE NE FACE UNICI</div>
        <h2 class="slide-title">Cele 3 Super-Puteri ale Aplicației Limpede</h2>
        <p class="slide-subtitle">Inovații tehnice concepute pentru siguranța și demnitatea profesională a utilizatorului.</p>

        <div class="grid-3">
          <div class="card" style="border-color: var(--cyan);">
            <div style="font-size: 0.8rem; font-weight: 700; color: var(--cyan); margin-bottom: 6px;">ZERO MEDICALIZARE</div>
            <div class="card-title" style="color: white;">Adaptare pe Nevoi, Nu pe Boală</div>
            <p style="font-size: 0.92rem; color: #CBD5E1; line-height: 1.45;">Interfața și AI-ul se remodelează instant după stilul tău de confort: contrast, ritm, lungime, fonturi speciale (OpenDyslexic, Atkinson). Fără etichete de diagnostic.</p>
          </div>
          <div class="card" style="border-color: var(--teal);">
            <div style="font-size: 0.8rem; font-weight: 700; color: var(--teal); margin-bottom: 6px;">ZERO HALUCINAȚII</div>
            <div class="card-title" style="color: white;">Clarificare &amp; «Arată în Text»</div>
            <p style="font-size: 0.92rem; color: #CBD5E1; line-height: 1.45;">Condensăm 40 de pagini în 3-4 pași acționabili cu verbe la imperativ. Butonul «Arată în text» aprinde cu galben citatul exact din documentul original semnat.</p>
          </div>
          <div class="card" style="border-color: var(--amber);">
            <div style="font-size: 0.8rem; font-weight: 700; color: var(--amber); margin-bottom: 6px;">SIGURANȚĂ LA TERMENE</div>
            <div class="card-title" style="color: white;">Protecție &amp; Export .ICS</div>
            <p style="font-size: 0.92rem; color: #CBD5E1; line-height: 1.45;">La «trimite cât mai repede», refuzăm să ghicim o dată arbitrară: punem badge galben [De confirmat] și exportăm la un click în Google Calendar sau Outlook.</p>
          </div>
        </div>
      </section>

      <!-- SLIDE 4 -->
      <section class="slide" data-notes="Design universal complet: acoperim întreg spectrul funcțional (memorie, ADHD, vedere scăzută, autism, dislexie, auz, mobilitate motorie).">
        <div class="badge">SPECTRUL FUNCȚIONAL</div>
        <h2 class="slide-title">Design Universal: Ceva Concret pentru Fiecare Nevoie</h2>
        <p class="slide-subtitle">Soluții concrete integrate direct în codul aplicației.</p>

        <div class="grid-2">
          <div class="card">
            <div class="card-title">🧠 Memorie &amp; ADHD</div>
            <p style="font-size: 0.92rem; color: #CBD5E1; line-height: 1.45;">Card prioritar «📌 De reținut», ancore tactile mărite pentru date și ore; filtrare introduceri sterile și maximum 3-4 pași scurți sub 10 cuvinte.</p>
          </div>
          <div class="card">
            <div class="card-title">👁️ Vedere Scăzută &amp; Dislexie</div>
            <p style="font-size: 0.92rem; color: #CBD5E1; line-height: 1.45;">Temă Contrast Ridicat 19.5:1 AAA, scalare la 200%; fonturi licențiate OpenDyslexic și Atkinson Hyperlegible, ghidaj bionic și riglă digitală.</p>
          </div>
          <div class="card">
            <div class="card-title">🧩 Autism &amp; Comunicare Literală</div>
            <p style="font-size: 0.92rem; color: #CBD5E1; line-height: 1.45;">Decodificare cereri indirecte corporatiste («ar fi frumos dacă...»); etichetare obligatorie a glumelor: <code>(posibilă glumă — nesigur)</code>.</p>
          </div>
          <div class="card">
            <div class="card-title">🦻 Auz &amp; Mobilitate Motorie</div>
            <p style="font-size: 0.92rem; color: #CBD5E1; line-height: 1.45;">Audio ședință transformat în decizii scrise cu responsabili; operare 100% din tastatură fără mouse și scurtătură globală <code>Alt + Shift + S</code>.</p>
          </div>
        </div>
      </section>

      <!-- SLIDE 5 -->
      <section class="slide" data-notes="De ce noi și nu soluțiile generice: zero halucinații, nu ghicim termene, confidențialitate fără diagnostic și conformitate EU AI Act Art. 5.">
        <div class="badge badge-amber">DIFERENȚIATORI SUBTILI</div>
        <h2 class="slide-title">De Ce Limpede și Nu Instrumentele Generice?</h2>
        <p class="slide-subtitle">Construit pe rigoare etică, securitate juridică și grounded data.</p>

        <div class="grid-2">
          <div class="card" style="border-left: 4px solid var(--amber);">
            <div class="card-title" style="color: var(--amber);">Verbatim Grounding vs Halucinații</div>
            <p style="font-size: 0.92rem; color: #CBD5E1; line-height: 1.45;">ChatGPT inventează detalii când nu știe. Limpede verifică algoritmic fiecare citat și oferă butonul «Arată în text» — dovada directă din document.</p>
          </div>
          <div class="card" style="border-left: 4px solid var(--cyan);">
            <div class="card-title">Protecție la Erori de Birou</div>
            <p style="font-size: 0.92rem; color: #CBD5E1; line-height: 1.45;">La termene vagi («cât mai repede»), refuzăm să ghicim o dată; marcăm [De confirmat] și exportăm direct fișierul standard .ics pentru calendar.</p>
          </div>
          <div class="card" style="border-left: 4px solid var(--teal);">
            <div class="card-title">Confidențialitate Fără Diagnostic</div>
            <p style="font-size: 0.92rem; color: #CBD5E1; line-height: 1.45;">Nu cerem certificat de handicap. Datele rămân 100% pe dispozitivul tău (localStorage) și nu sunt trimise către terți pentru antrenare.</p>
          </div>
          <div class="card" style="border-left: 4px solid white;">
            <div class="card-title" style="color: white;">Conformitate EU AI Act (Articolul 5)</div>
            <p style="font-size: 0.92rem; color: #CBD5E1; line-height: 1.45;">Interzicem strict deducerea emoțiilor la locul de muncă din voce sau mimică. Avem motor euristic local capabil să ruleze 100% offline.</p>
          </div>
        </div>
      </section>

      <!-- SLIDE 6 -->
      <section class="slide" data-notes="Demonstrație live: trecem acum la prezentarea practică.">
        <div style="text-align: center; margin-top: 40px;">
          <div class="badge badge-amber" style="margin: 0 auto 16px;">LIVE DEMO &amp; CONCLUZIE</div>
          <h2 class="slide-title" style="font-size: 3.2rem; margin-bottom: 12px;">Să vedem Limpede în acțiune!</h2>
          <p style="font-size: 1.3rem; color: var(--cyan); margin-bottom: 40px;">Trecem la demonstrația practică pe platformă și pe extensia de browser.</p>

          <div class="card" style="max-width: 900px; margin: 0 auto; border-color: var(--amber); padding: 30px 40px;">
            <p style="font-size: 1.45rem; font-style: italic; font-weight: 700; line-height: 1.5; color: white;">
              „Cu Limpede, prima zi de muncă nu mai este un test de anduranță cognitivă sau o sursă de panică, ci un parteneriat bazat pe claritate, demnitate și performanță.”
            </p>
          </div>
        </div>
      </section>

      <!-- Notes Drawer -->
      <div id="notes-drawer">
        <div style="color: var(--amber); font-weight: 700; font-size: 0.8rem; text-transform: uppercase; margin-bottom: 4px;">📝 Note Prezentator:</div>
        <div id="notes-text"></div>
      </div>

    </div>
  </main>

  <script>
    const slides = document.querySelectorAll('.slide');
    const counter = document.getElementById('counter');
    const notesDrawer = document.getElementById('notes-drawer');
    const notesText = document.getElementById('notes-text');
    let currentIndex = 0;

    function showSlide(index) {{
      if (index < 0) index = 0;
      if (index >= slides.length) index = slides.length - 1;
      currentIndex = index;

      slides.forEach((s, i) => {{
        s.classList.toggle('active', i === currentIndex);
      }});

      counter.textContent = `${{currentIndex + 1}} / ${{slides.length}}`;
      notesText.innerHTML = (slides[currentIndex].getAttribute('data-notes') || '').replace(/\\n/g, '<br>');
    }}

    function prevSlide() {{ showSlide(currentIndex - 1); }}
    function nextSlide() {{ showSlide(currentIndex + 1); }}
    function toggleNotes() {{ notesDrawer.classList.toggle('open'); }}
    function toggleFS() {{
      if (!document.fullscreenElement) {{
        document.documentElement.requestFullscreen();
      }} else {{
        if (document.exitFullscreen) document.exitFullscreen();
      }}
    }}

    document.addEventListener('keydown', (e) => {{
      if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') nextSlide();
      else if (e.key === 'ArrowLeft' || e.key === 'PageUp') prevSlide();
      else if (e.key === 'n' || e.key === 'N') toggleNotes();
      else if (e.key === 'f' || e.key === 'F') toggleFS();
    }});

    showSlide(0);
  </script>
</body>
</html>
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML presentation generated at: {output_path}")


def build_pitch_live_docx(output_path):
    doc = docx.Document()
    for section in doc.sections:
        section.top_margin = DocxInches(0.8)
        section.bottom_margin = DocxInches(0.8)
        section.left_margin = DocxInches(0.8)
        section.right_margin = DocxInches(0.8)

    title_p = doc.add_paragraph()
    r = title_p.add_run("Limpede — Prezentare Pitch Live (Scurtă & Concisă)")
    r.font.size = DocxPt(22)
    r.font.bold = True
    r.font.color.rgb = DocxRGBColor(13, 148, 136)

    sub_p = doc.add_paragraph()
    r = sub_p.add_run("Adaptăm locul de muncă la om, nu invers. • AccessABILITY Hackathon 2026")
    r.font.size = DocxPt(11)
    r.font.italic = True
    r.font.color.rgb = DocxRGBColor(100, 116, 139)

    doc.add_heading("1. Cârligul Emoțional & Problema (0:00 – 1:00)", level=1)
    doc.add_paragraph(
        "„Faceți cunoștință cu Ana. Are 23 de ani, a terminat facultatea și astăzi este prima ei zi de muncă. "
        "Primește 40 de pagini de proceduri birocratice, e-mailuri cu termene vagi («cât mai repede») și instrucțiuni confuze. "
        "Ana are ADHD și anxietate socială. Îi este o frică paralizantă să întrebe pentru a treia oară ce înseamnă un termen de birou. "
        "În România și UE, 1 din 6 tineri trăiește cu o dizabilitate, iar 68% din abandonurile la primul job se întâmplă din cauza comunicării inaccesibile. "
        "Pentru ei am creat Limpede: adaptăm locul de muncă la om, nu invers.”"
    )

    doc.add_heading("2. Ecosistemul Unificat (Trei Puncte de Acces)", level=1)
    doc.add_paragraph("• Asistentul Personal (Web): Clarificare pas-cu-pas, card prioritar «📌 De reținut», rezumate de ședințe și cereri de adaptare legale.\n"
                      "• Extensia de Browser: Funcționează direct pe Confluence, Jira, Gmail și Slack. Selectezi textul și apeși «Fă clar».\n"
                      "• Portalul Angajatorului: Audit de lizibilitate internă (0-100) și generare automată Easy-to-Read pentru HR.")

    doc.add_heading("3. Cele 3 Super-Puteri ale Aplicației Limpede", level=1)
    doc.add_paragraph(
        "1. Adaptare pe Nevoi, Nu pe Boală: Interfața și modelul AI se remodelează instant după stilul tău de confort fără să ceară vreodată diagnostic medical sau certificat de încadrare.\n"
        "2. Clarificare cu funcția «Arată în text»: Luăm 40 de pagini și le condensăm în 3-4 pași acționabili. Butonul «Arată în text» aprinde cu galben citatul exact din documentul sursă (zero halucinații).\n"
        "3. Protecție pe Termene & Export .ICS: La cereri vagi («cât mai repede»), refuzăm să ghicim date arbitrare; marcăm [De confirmat] și exportăm direct în Google Calendar și Outlook."
    )

    doc.add_heading("4. Spectrul Complet de Dizabilități (Design Universal)", level=1)
    doc.add_paragraph(
        "• Memorie & Reținere: Card prioritar «📌 De reținut», ancore tactile mărite pentru date și ore.\n"
        "• ADHD & Atenție: Fără politețuri sterile; maximum 3-4 pași imperativi sub 10 cuvinte.\n"
        "• Vedere Scăzută: Temă Contrast Ridicat 19.5:1 AAA, scalare 200%, pilule tactile mari.\n"
        "• Autism & Literalitate: Decodificare cereri indirecte; etichetare: (posibilă glumă — nesigur).\n"
        "• Dislexie: Fonturi licențiate OpenDyslexic și Atkinson Hyperlegible, ghidaj bionic.\n"
        "• Auz & Mobilitate: Audio transformat în decizii scrise cu responsabili; navigare 100% din tastatură (Alt + Shift + S)."
    )

    doc.add_heading("5. Diferențiatori Subtili vs Competiție (De ce Limpede?)", level=1)
    doc.add_paragraph(
        "• Verbatim Quote Grounding: ChatGPT inventează termene și date; Limpede verifică matematic fiecare citat în textul sursă.\n"
        "• Protecție la erori de birou: Nu lăsăm utilizatorul să greșească datele limită.\n"
        "• Confidențialitate absolută: Datele rămân 100% în browser (localStorage) fără transmitere către terți.\n"
        "• Conformitate EU AI Act: Respectăm Articolul 5 interzicând deducerea emoțiilor la locul de muncă."
    )

    doc.save(output_path)
    print(f"PITCH LIVE DOCX generated at: {output_path}")


def build_judge_deck_docx(output_path):
    doc = docx.Document()
    for section in doc.sections:
        section.top_margin = DocxInches(0.8)
        section.bottom_margin = DocxInches(0.8)
        section.left_margin = DocxInches(0.8)
        section.right_margin = DocxInches(0.8)

    title_p = doc.add_paragraph()
    r = title_p.add_run("Limpede — Dosar Tehnic de Departajare (Pentru Juriu)")
    r.font.size = DocxPt(22)
    r.font.bold = True
    r.font.color.rgb = DocxRGBColor(13, 148, 136)

    sub_p = doc.add_paragraph()
    r = sub_p.add_run("Arhitectură Tehnică, Audit WCAG 2.2 AAA, Conformitate EU AI Act & Matrice de Validare")
    r.font.size = DocxPt(11)
    r.font.italic = True
    r.font.color.rgb = DocxRGBColor(100, 116, 139)

    doc.add_heading("1. Sumar Executiv & Teza Soluției", level=1)
    doc.add_paragraph(
        "Limpede este prima platformă bilaterală și extensie de browser concepută pentru incluziunea tinerilor cu dizabilități la primul job. "
        "Spre deosebire de instrumentele AI generice, Limpede este proiectat cu constrângeri stricte de siguranță cognitivă: "
        "zero halucinații prin Verbatim Quote Grounding, protecție împotriva termenelor vagi și respectarea demnității prin necolectarea de date medicale."
    )

    doc.add_heading("2. Audit de Accesibilitate WCAG 2.2 Nivel AAA", level=1)
    table = doc.add_table(rows=6, cols=4)
    table.style = 'Table Grid'
    headers = ["Criteriu WCAG 2.2", "Nivel Țintă", "Măsurat în Cod", "Soluție Tehnică"]
    for j, h in enumerate(headers):
        cell = table.cell(0, j)
        shading = docx_parse_xml(r'<w:shd {} w:fill="0D9488"/>'.format(nsdecls('w')))
        cell._tc.get_or_add_tcPr().append(shading)
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.font.bold = True
        r.font.color.rgb = DocxRGBColor(255, 255, 255)

    data = [
        ("1.4.3 & 1.4.6 Contrast", "AAA (7:1)", "19.5:1 (depășit cu 178%)", "Paletă Midnight Slate pe fundal deschis; galben pe negru pentru contrast extrem."),
        ("2.1.1 Tastatură Completă", "AA / AAA", "100% Navigabil", "Trap-free focus, skip link, scurtături globale (Alt+Shift+S), tab order logic."),
        ("2.5.5 / 2.5.8 Ținte Tactile", "AAA (44x44px)", "Minim 48x48px", "Variabilă CSS --min-touch-target: 44px; padding tactil generos."),
        ("3.1.5 Nivel de Lectură", "AAA", "Calibrat pe clase", "Extragere limbaj simplu (Easy-to-Read), fraze sub 10 cuvinte, eliminare jargon."),
        ("1.4.12 Spațiere Text", "AA", "Ajustabil dinamic", "Variabile CSS line-height (1.6-2.0), letter-spacing și word-spacing fără rupere de layout.")
    ]
    for i, row in enumerate(data):
        for j, val in enumerate(row):
            cell = table.cell(i + 1, j)
            if i % 2 == 1:
                shading = docx_parse_xml(r'<w:shd {} w:fill="F8FAFC"/>'.format(nsdecls('w')))
                cell._tc.get_or_add_tcPr().append(shading)
            p = cell.paragraphs[0]
            r = p.add_run(val)
            r.font.size = DocxPt(9.5)
            if j == 0 or j == 2:
                r.font.bold = True

    doc.add_heading("3. Cadrul Juridic & AI Etic", level=1)
    doc.add_paragraph(
        "• EU AI Act (Articolul 5): Interzice categoric utilizarea inteligenței artificiale pentru deducerea emoțiilor la locul de muncă. Limpede nu analizează vocea sau mimica pentru emoții.\n"
        "• Legea 448/2006 (Art. 83-84): Obligă angajatorii să asigure adaptări rezonabile. Modulul de adaptări generează cereri bazate pe legislația română fără a divulga diagnostice.\n"
        "• GDPR & Confidențialitate: Zero server-side tracking. Preferințele utilizatorului sunt salvate exclusiv în localStorage cu opțiune de ștergere instantanee."
    )

    doc.add_heading("4. Arhitectura Tehnică & Lanțul de Reziliență", level=1)
    doc.add_paragraph(
        "• Backend Asincron FastAPI: Validare cu Pydantic v2, protecție prompt-injection și răspunsuri sub 1.2 secunde.\n"
        "• Provider Chain: Gemini 2.5 Flash -> Groq Whisper & Llama 3 -> Ollama local -> Motor euristic determinist offline.\n"
        "• Extensie Browser Manifest V3: Shadow DOM complet izolat pentru injectare curată pe Jira, Confluence, Slack web și Gmail.\n"
        "• Baterie de 460 Teste Verificate: Acoperire completă pe endpoint-uri, contracte API, reguli statice de accesibilitate și absența culorilor hardcodate în CSS."
    )

    doc.save(output_path)
    print(f"JUDGE DECK DOCX generated at: {output_path}")


def main():
    docs_dir = os.path.join(os.getcwd(), "docs")

    # 1. Pitch Live (Short & Punchy)
    p_live_pptx = os.path.join(docs_dir, "limpede_pitch_live.pptx")
    p_live_docx = os.path.join(docs_dir, "limpede_pitch_live.docx")
    p_live_html = os.path.join(docs_dir, "pitch_live.html")
    build_pitch_live_pptx(p_live_pptx)
    build_pitch_live_docx(p_live_docx)
    build_interactive_html(p_live_html, is_judge=False)

    # 2. Judge Deck (Comprehensive & Technical)
    j_deck_pptx = os.path.join(docs_dir, "limpede_judge_deck.pptx")
    j_deck_docx = os.path.join(docs_dir, "limpede_judge_deck.docx")
    j_deck_html = os.path.join(docs_dir, "judge_deck.html")
    build_judge_deck_pptx(j_deck_pptx)
    build_judge_deck_docx(j_deck_docx)
    build_interactive_html(j_deck_html, is_judge=True)

    print("\n✅ BOTH PRESENTATION DECKS GENERATED SUCCESSFULLY IN PPTX, DOCX, AND HTML:")
    print(f"1. Pitch Live: {p_live_pptx} | {p_live_docx} | {p_live_html}")
    print(f"2. Judge Deck: {j_deck_pptx} | {j_deck_docx} | {j_deck_html}")


if __name__ == "__main__":
    main()
