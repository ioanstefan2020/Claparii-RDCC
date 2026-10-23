#!/usr/bin/env python3
"""
Generate presentation artifacts for Limpede:
1. docs/prezentare_limpede.pptx (16:9 widescreen PowerPoint presentation with custom theme & speaker notes)
2. docs/prezentare_limpede.docx (Professional Word document with complete pitch script & reference tables)
3. docs/prezentare.html (Self-contained offline browser slideshow)
"""

import sys
import os
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

import docx
from docx.shared import Inches as DocxInches, Pt as DocxPt, RGBColor as DocxRGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

# Colors
C_TEAL = RGBColor(13, 148, 136)       # #0D9488
C_SLATE_DARK = RGBColor(15, 23, 42)   # #0F172A
C_SLATE_BG = RGBColor(248, 250, 252)  # #F8FAFC
C_WHITE = RGBColor(255, 255, 255)     # #FFFFFF
C_AMBER = RGBColor(245, 158, 11)      # #F59E0B
C_BORDER = RGBColor(203, 213, 225)    # #CBD5E1
C_MUTED = RGBColor(100, 116, 139)     # #64748B
C_TEAL_LIGHT = RGBColor(240, 253, 250)# #F0FDFA
C_GREEN = RGBColor(22, 163, 74)       # #16A34A
C_RED = RGBColor(220, 38, 38)         # #DC2626


def create_pptx(output_path: str):
    prs = pptx.Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    def add_bg(slide, color=C_SLATE_BG):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = color
        bg.line.fill.background()
        return bg

    def add_header(slide, tag_text: str, title_text: str, subtitle_text: str = None, dark_mode=False):
        # Badge
        badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(0.45), Inches(3.5), Inches(0.38))
        badge.fill.solid()
        badge.fill.fore_color.rgb = C_AMBER if dark_mode else C_TEAL
        badge.line.fill.background()
        tf = badge.text_frame
        tf.word_wrap = False
        p = tf.paragraphs[0]
        p.text = tag_text.upper()
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = C_SLATE_DARK if dark_mode else C_WHITE
        p.alignment = PP_ALIGN.CENTER

        # Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.9), Inches(11.7), Inches(0.65))
        tf_t = title_box.text_frame
        tf_t.word_wrap = True
        p_t = tf_t.paragraphs[0]
        p_t.text = title_text
        p_t.font.size = Pt(26)
        p_t.font.bold = True
        p_t.font.color.rgb = C_WHITE if dark_mode else C_SLATE_DARK

        # Subtitle
        if subtitle_text:
            p_sub = tf_t.add_paragraph()
            p_sub.text = subtitle_text
            p_sub.font.size = Pt(14)
            p_sub.font.color.rgb = C_AMBER if dark_mode else C_MUTED
            p_sub.space_before = Pt(4)

    def set_notes(slide, notes_text: str):
        notes_slide = slide.notes_slide
        tf = notes_slide.notes_text_frame
        tf.text = notes_text

    # ==========================================
    # SLIDE 1: Title & Emotional Hook (0:00 - 1:00)
    # ==========================================
    s1 = prs.slides.add_slide(blank_layout)
    add_bg(s1, C_SLATE_DARK)

    # Accent decorative bar
    bar = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.35), Inches(7.5))
    bar.fill.solid()
    bar.fill.fore_color.rgb = C_TEAL
    bar.line.fill.background()

    # Brand badge
    b1 = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(0.8), Inches(4.5), Inches(0.42))
    b1.fill.solid()
    b1.fill.fore_color.rgb = C_TEAL
    b1.line.fill.background()
    p = b1.text_frame.paragraphs[0]
    p.text = "ACCESSABILITY HACKATHON 2026"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = C_WHITE
    p.alignment = PP_ALIGN.CENTER

    # Main Title
    t1 = s1.shapes.add_textbox(Inches(1.0), Inches(1.4), Inches(11.0), Inches(2.2))
    tf1 = t1.text_frame
    tf1.word_wrap = True
    p1 = tf1.paragraphs[0]
    p1.text = "Limpede"
    p1.font.size = Pt(54)
    p1.font.bold = True
    p1.font.color.rgb = C_WHITE

    p2 = tf1.add_paragraph()
    p2.text = "Primul pas la primul job, fără bariere de înțelegere."
    p2.font.size = Pt(24)
    p2.font.bold = True
    p2.font.color.rgb = C_AMBER
    p2.space_before = Pt(8)

    p3 = tf1.add_paragraph()
    p3.text = "Adaptăm locul de muncă la om, nu invers."
    p3.font.size = Pt(16)
    p3.font.italic = True
    p3.font.color.rgb = RGBColor(148, 163, 184)
    p3.space_before = Pt(4)

    # 3 Stat Cards on Slide 1
    cards_data = [
        ("68% Abandon", "din abandonurile la primul job se produc din cauza comunicării inaccesibile și a fricii de stigmatizare.", C_AMBER),
        ("1 din 6 Tineri", "din România și Uniunea Europeană trăiește cu o dizabilitate sau o neurodivergență.", C_TEAL),
        ("Zero Diagnostic", "Limpede nu cere niciodată adeverințe sau diagnostice. Adaptarea se face pe baza confortului ales.", C_WHITE)
    ]
    for i, (head, desc, color) in enumerate(cards_data):
        cx = Inches(1.0 + i * 3.8)
        c = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx, Inches(4.1), Inches(3.5), Inches(2.5))
        c.fill.solid()
        c.fill.fore_color.rgb = RGBColor(30, 41, 59)
        c.line.color.rgb = C_TEAL
        c.line.width = Pt(1.5)
        tf = c.text_frame
        tf.word_wrap = True
        tf.margin_top = Inches(0.25)
        tf.margin_left = Inches(0.25)
        tf.margin_right = Inches(0.25)

        ph = tf.paragraphs[0]
        ph.text = head
        ph.font.size = Pt(22)
        ph.font.bold = True
        ph.font.color.rgb = color

        pd = tf.add_paragraph()
        pd.text = desc
        pd.font.size = Pt(13)
        pd.font.color.rgb = RGBColor(226, 232, 240)
        pd.space_before = Pt(10)

    set_notes(s1, """TIMING: 0:00 – 1:00 (1:00 min)
DISCURS PENTRU JURIU:
„Faceți cunoștință cu Ana. Are 23 de ani, a terminat facultatea și astăzi este prima ei zi de muncă. Este inteligentă, entuziasmată și dornică să performeze. Dar în primele 2 ore de la sosire, primește un teanc de 40 de pagini de proceduri birocratice, e-mailuri cu termene vagi precum «cât mai repede» și instrucțiuni confuze.

Ana are o dizabilitate invizibilă: ADHD și anxietate socială. Îi este o frică paralizantă să întrebe pentru a treia oară ce înseamnă «Formularul F-12» sau «SecInfo v3», de teamă să nu pară incompetentă în perioada de probă.

În România și în Uniunea Europeană, 1 din 6 tineri trăiește cu o dizabilitate, iar 68% din abandonurile la primul job se întâmplă din cauza comunicării inaccesibile și a fricii de stigmatizare. Pentru ei am creat Limpede: adaptăm locul de muncă la om, nu invers.”
""")

    # ==========================================
    # SLIDE 2: Ecosystem — What We Built (1:00 - 1:40)
    # ==========================================
    s2 = prs.slides.add_slide(blank_layout)
    add_bg(s2, C_SLATE_BG)
    add_header(s2, "1:00 – 1:40 • Ecosistemul Unificat", "Soluție Completă: Platformă Web Bilaterală + Extensie Browser", "O suită unitară care conectează angajatul cu angajatorul și funcționează direct pe orice aplicație web.")

    # 3 Columns for Platform Components
    col_w = Inches(3.7)
    gap = Inches(0.3)

    # Col 1: Zona Angajatului
    c1 = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.9), col_w, Inches(4.8))
    c1.fill.solid()
    c1.fill.fore_color.rgb = C_WHITE
    c1.line.color.rgb = C_BORDER
    c1.line.width = Pt(1.5)
    tf1 = c1.text_frame
    tf1.word_wrap = True
    tf1.margin_top = Inches(0.3)
    tf1.margin_left = Inches(0.3)
    tf1.margin_right = Inches(0.3)
    p = tf1.paragraphs[0]
    p.text = "1. Zona Angajatului"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = C_TEAL

    points1 = [
        "Clarificare pas-cu-pas a documentelor stufoase de onboarding.",
        "Ancore vizuale tactile pentru date, ore și coduri esențiale.",
        "Planificator cu protecție pe termene vagi & export .ics.",
        "Asistent de ședință: audio -> decizii scrise cu responsabili.",
        "Redactor cereri de adaptare conform legislației românești, fără diagnostic medical."
    ]
    for pt in points1:
        p = tf1.add_paragraph()
        p.text = "• " + pt
        p.font.size = Pt(12)
        p.font.color.rgb = C_SLATE_DARK
        p.space_before = Pt(8)

    # Col 2: Zona Angajatorului (HR Hub)
    c2 = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8 + 1 * (3.7 + 0.3)), Inches(1.9), col_w, Inches(4.8))
    c2.fill.solid()
    c2.fill.fore_color.rgb = C_WHITE
    c2.line.color.rgb = C_BORDER
    c2.line.width = Pt(1.5)
    tf2 = c2.text_frame
    tf2.word_wrap = True
    tf2.margin_top = Inches(0.3)
    tf2.margin_left = Inches(0.3)
    tf2.margin_right = Inches(0.3)
    p = tf2.paragraphs[0]
    p.text = "2. Zona Angajatorului (HR)"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = C_AMBER

    points2 = [
        "Scanner de lizibilitate documente interne (scor 0-100).",
        "Detector automat de jargon corporatist și acronime neexplicate.",
        "Evidențierea propozițiilor peste 25 de cuvinte greu de parcurs.",
        "Generator automat versiune Easy-to-Read (Limbaj Ușor de Citit).",
        "Sprijin direct pentru conformitate ESG / CSRD și incluziune reală."
    ]
    for pt in points2:
        p = tf2.add_paragraph()
        p.text = "• " + pt
        p.font.size = Pt(12)
        p.font.color.rgb = C_SLATE_DARK
        p.space_before = Pt(8)

    # Col 3: Extensia de Browser (Manifest V3)
    c3 = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8 + 2 * (3.7 + 0.3)), Inches(1.9), col_w, Inches(4.8))
    c3.fill.solid()
    c3.fill.fore_color.rgb = C_WHITE
    c3.line.color.rgb = C_BORDER
    c3.line.width = Pt(1.5)
    tf3 = c3.text_frame
    tf3.word_wrap = True
    tf3.margin_top = Inches(0.3)
    tf3.margin_left = Inches(0.3)
    tf3.margin_right = Inches(0.3)
    p = tf3.paragraphs[0]
    p.text = "3. Extensia de Browser"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = C_TEAL

    points3 = [
        "Funcționează pe orice pagină web: Confluence, Jira, Gmail, Slack.",
        "Selectezi orice text stufos și apeși pe butonul plutitor «Fă clar».",
        "Card Shadow DOM complet izolat de stilurile paginii gazdă.",
        "Transformări instant: «✂️ Mai scurt», «• Buline», «Pe pași».",
        "Sinteză vocală naturală în limba română (ro-RO) la un click."
    ]
    for pt in points3:
        p = tf3.add_paragraph()
        p.text = "• " + pt
        p.font.size = Pt(12)
        p.font.color.rgb = C_SLATE_DARK
        p.space_before = Pt(8)

    set_notes(s2, """TIMING: 1:00 – 1:40 (0:40 min)
DISCURS PENTRU JURIU:
„Limpede este prima suită completă de asistență cognitivă la locul de muncă în limba română, concepută ca un ecosistem integrat:
1. Pentru Angajat: Un asistent confidențial care clarifică documentele pas cu pas, extrage termene în calendar, sintetizează ședințe și redactează cereri oficiale de adaptare — fără să ceară vreodată diagnostic medical.
2. Pentru Angajator: Portal de audit prin care departamentul HR măsoară lizibilitatea documentelor interne și generează automat versiuni în limbaj simplu (Easy-to-Read).
3. Extensia de Browser Limpede: Funcționează direct pe orice aplicație web a companiei (Confluence, Jira, Gmail, Slack). Selectezi orice text stufos și primești claritate pe loc.”
""")

    # ==========================================
    # SLIDE 3: Disabilities Matrix (1:40 - 2:15)
    # ==========================================
    s3 = prs.slides.add_slide(blank_layout)
    add_bg(s3, C_SLATE_BG)
    add_header(s3, "1:40 – 2:15 • Spectrul Funcțional", "Incluziune Reală pentru Întreg Spectrul Funcțional", "Design universal: adaptări concrete în cod pentru fiecare tip de barieră la locul de muncă.")

    # Table with disabilities
    rows, cols = 8, 3
    left = Inches(0.8)
    top = Inches(1.9)
    width = Inches(11.7)
    height = Inches(4.9)

    table_shape = s3.shapes.add_table(rows, cols, left, top, width, height)
    tbl = table_shape.table
    tbl.columns[0].width = Inches(3.0)
    tbl.columns[1].width = Inches(3.7)
    tbl.columns[2].width = Inches(5.0)

    headers = ["Categorie / Nevoie", "Bariera la Locul de Muncă", "Cum rezolvă Limpede în cod?"]
    for j, h in enumerate(headers):
        cell = tbl.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = C_TEAL
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = C_WHITE

    data_matrix = [
        ("Memorie & Reținere\n(Cognitiv, oboseală, traumatisme)", "Uitarea instrucțiunilor și a termenelor din prima zi", "Card prioritar «📌 De reținut imediat», dublare termeni cheie, pilule tactile."),
        ("ADHD & Atenție\n(Neurodivergență, hiperfocus)", "Pierderea șirului în proceduri de 40 de pagini", "Filtru politețuri sterile; maximum 3-4 pași sub 10 cuvinte cu verbe la imperativ."),
        ("Vedere Scăzută / Fotofobie\n(Miopie severă, ambliopie)", "Efort masiv pe fonturi mici și tabele neclare", "Temă Contrast Ridicat (19.5:1 AAA), scalare 200%, pilule tactile mărite."),
        ("Autism & Literalitate\n(Neurodivergență)", "Confuzie la metafore, glume sau cereri indirecte", "Decodificare cereri indirecte; etichetare obligatorie: (posibilă glumă — nesigur)."),
        ("Dislexie\n(Dificultate procesare text)", "Litere care dansează, oboseală la lectură", "Fonturi speciale (OpenDyslexic, Atkinson), riglă de lectură și ghidaj bionic."),
        ("Deficiențe de Auz\n(Hipoacuzie)", "Pierderea deciziilor din ședințele verbale", "Transformare audio în decizii scrise și sarcini cu responsabili asignați."),
        ("Dizabilități Motorii\n(Mobilitate redusă)", "Dificultate la folosirea mouse-ului", "Ținte tactile mari (≥ 44px), navigare 100% din tastatură, Alt + Shift + S.")
    ]

    for i, row in enumerate(data_matrix):
        for j, val in enumerate(row):
            cell = tbl.cell(i + 1, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = C_WHITE if (i % 2 == 0) else C_TEAL_LIGHT
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.size = Pt(11)
            p.font.color.rgb = C_SLATE_DARK
            if j == 0:
                p.font.bold = True

    set_notes(s3, """TIMING: 1:40 – 2:15 (0:35 min)
DISCURS PENTRU JURIU:
„Cum arată incluziunea reală în codul Limpede? Am mapat fiecare barieră la o rezolvare tehnică precisă:
- Memorie: Cardul prioritar «De reținut imediat» plasează esențialul în fruntea ecranului.
- ADHD: Eliminăm introducerile sterile; afișăm doar 3-4 pași scurți, imperativi, sub 10 cuvinte.
- Vedere: Temă Contrast Ridicat 19.5:1 AAA, scalare la 200% și pilule tactile pentru ore și date.
- Autism: Decodificăm cererile corporatiste indirecte și marcăm glumele ca «posibilă glumă — nesigur».
- Dislexie: Fonturi licențiate OpenDyslexic și Atkinson Hyperlegible cu suport complet pentru diacriticele românești.
- Auz: Transcriere cu extragere de decizii scrise și sarcini cu responsabili.
- Motor: Totul funcționează 100% din tastatură, cu ținte tactile mari de peste 44 de pixeli.”
""")

    # ==========================================
    # SLIDE 4: Competition Matrix (2:15 - 3:00)
    # ==========================================
    s4 = prs.slides.add_slide(blank_layout)
    add_bg(s4, C_SLATE_BG)
    add_header(s4, "2:15 – 3:00 • De Ce Limpede?", "De Ce Nu ChatGPT, Grammarly sau Portalele HR Clasice?", "Matrice de conformitate și protecție: siguranță cognitivă și respectarea legii.")

    rows, cols = 7, 5
    table_shape4 = s4.shapes.add_table(rows, cols, Inches(0.8), Inches(1.9), Inches(11.7), Inches(4.9))
    tbl4 = table_shape4.table
    tbl4.columns[0].width = Inches(2.7)
    tbl4.columns[1].width = Inches(2.2)
    tbl4.columns[2].width = Inches(2.0)
    tbl4.columns[3].width = Inches(2.0)
    tbl4.columns[4].width = Inches(2.8)

    headers4 = ["Criteriu de Evaluare", "ChatGPT / Generic", "Grammarly", "Portaluri HR", "Limpede (Noi)"]
    for j, h in enumerate(headers4):
        cell = tbl4.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = C_AMBER if j == 4 else C_SLATE_DARK
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = C_WHITE

    comp_matrix = [
        ("Zero Halucinații\n(Verbatim Grounding)", "❌ Inventează date și termene", "❌ Doar gramatică", "❌ Nu simplifică", "✅ Verificare matematică:\n«Arată în text» luminează sursa"),
        ("Protecție Termene Ambigue", "❌ Ghicește o dată arbitrară", "❌ Indiferent", "❌ Creează confuzie", "✅ Refuză să ghicească:\nmarchează [De confirmat] + .ics"),
        ("Fără Date Medicale Invazive", "❌ Cere diagnostic medical", "❌ Fără profil adaptat", "❌ Cere certificat handicap", "✅ 100% Funcțional:\npersonalizare pe nevoi, zero etichete"),
        ("EU AI Act Conformant\n(Articolul 5)", "❌ Analiză emoții neclară", "❌ Cloud SUA", "❌ Static", "✅ Interzice strict detectarea emoțiilor din voce/text la birou"),
        ("Disponibilitate Offline", "❌ Necesită conexiune", "❌ Necesită conexiune", "❌ Variabil", "✅ Salvare 100% localStorage +\nmotor euristic de rezervă"),
        ("Integrare Oriunde pe Web", "❌ Copy-paste continuu", "⚠️ Doar verificare text", "❌ Închis", "✅ Extensie Browser:\ncard plutitor peste orice aplicație")
    ]

    for i, row in enumerate(comp_matrix):
        for j, val in enumerate(row):
            cell = tbl4.cell(i + 1, j)
            cell.fill.solid()
            if j == 4:
                cell.fill.fore_color.rgb = RGBColor(254, 243, 199) if i % 2 == 0 else RGBColor(253, 230, 138)
            else:
                cell.fill.fore_color.rgb = C_WHITE if i % 2 == 0 else C_SLATE_BG
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.size = Pt(10.5)
            p.font.color.rgb = C_SLATE_DARK
            if j == 0:
                p.font.bold = True
            elif j == 4:
                p.font.bold = True

    set_notes(s4, """TIMING: 2:15 – 3:00 (0:45 min)
DISCURS PENTRU JURIU:
„De ce nu folosește Ana pur și simplu ChatGPT sau un corector gramatical?
1. Zero Halucinații (Verbatim Grounding): ChatGPT inventează date când nu știe. Limpede verifică algoritmic fiecare citat și oferă butonul «Arată în text» — dovada matematică a sursei în documentul oficial.
2. Protecție pe Termene Ambigue: La fraza «trimite cât mai repede», ChatGPT ar fi ghicit o dată oarecare. Limpede refuză să ghicească, marchează cu [De confirmat] și exportă fișier de calendar .ics.
3. Confidențialitate & Fără Etichete Medicale: Nu cerem dosar medical sau certificat de încadrare. Datele rămân 100% în browser (localStorage).
4. Conformitate cu Regulamentul European (EU AI Act): Interzicem strict recunoașterea emoțiilor din voce sau text la locul de muncă, respectând Articolul 5.”
""")

    # ==========================================
    # SLIDE 5: Live Demo Workflow (3:00 - 6:30)
    # ==========================================
    s5 = prs.slides.add_slide(blank_layout)
    add_bg(s5, C_SLATE_BG)
    add_header(s5, "3:00 – 6:30 • Live Demo Pas cu Pas", "Scenariul Complet de Demonstrație în Fața Juriului (3:30 Min)", "5 momente cheie care demonstrează valoarea practică a ecosistemului Limpede.")

    steps_data = [
        ("Pasul 1 (0:35)", "Profil & Nevoi", "Definire stil de lucru în propriile cuvinte, fără certificat medical. Salvare 100% pe dispozitiv.", C_TEAL),
        ("Pasul 2 (1:00)", "PDF & «Arată în text»", "Încărcare ghid onboarding, card prioritar «De reținut», pilule tactile și verificarea citatului în textul sursă.", C_AMBER),
        ("Pasul 3 (0:45)", "Planificator & .ICS", "Extragere sarcini din email managerial («cât mai repede»), alertă [De confirmat] și export calendar.", C_TEAL),
        ("Pasul 4 (0:45)", "Extensia Browser", "Selectare text pe orice site, butonul «Fă clar», compresie «✂️ Mai scurt», buline și voce sintetică ro-RO.", C_AMBER),
        ("Pasul 5 (0:25)", "Portal Angajator", "Audit HR lizibilitate (0-100), detector jargon și generare automată Easy-to-Read pentru companie.", C_TEAL)
    ]

    card_w = Inches(2.15)
    gap_s = Inches(0.2)
    for i, (tag, title, desc, col) in enumerate(steps_data):
        cx = Inches(0.8 + i * (2.15 + 0.2))
        c = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx, Inches(1.9), card_w, Inches(4.8))
        c.fill.solid()
        c.fill.fore_color.rgb = C_WHITE
        c.line.color.rgb = col
        c.line.width = Pt(2.0)
        tf = c.text_frame
        tf.word_wrap = True
        tf.margin_top = Inches(0.25)
        tf.margin_left = Inches(0.2)
        tf.margin_right = Inches(0.2)

        ptag = tf.paragraphs[0]
        ptag.text = tag
        ptag.font.size = Pt(12)
        ptag.font.bold = True
        ptag.font.color.rgb = col

        ptitle = tf.add_paragraph()
        ptitle.text = title
        ptitle.font.size = Pt(16)
        ptitle.font.bold = True
        ptitle.font.color.rgb = C_SLATE_DARK
        ptitle.space_before = Pt(6)

        pdesc = tf.add_paragraph()
        pdesc.text = desc
        pdesc.font.size = Pt(11)
        pdesc.font.color.rgb = C_MUTED
        pdesc.space_before = Pt(12)

    set_notes(s5, """TIMING: 3:00 – 6:30 (3:30 min)
GHID OPERAȚIONAL PENTRU DEMO LIVE:
1. (3:00-3:35) Deschide /employee/profile.html. Lipește: «am probleme mari de memorie și uit repede instrucțiunile. Vreau să îmi bolduiești orele și datele limită și să îmi pui ce am de reținut imediat». Salvează.
2. (3:35-4:35) Pe Acasă, apasă + -> Încarcă PDF -> alege ghid_onboarding_exemplu.pdf -> Clarifică. Arată cardul «De reținut», pilulele mari și apasă «Arată în text» la Pasul 1 (se aprinde galben în stânga!).
3. (4:35-5:15) Pe Planificator (/employee/plan.html), încarcă exemplul managerial. Arată badge-ul galben [De confirmat]. Confirmă data și descarcă fișierul .ics.
4. (5:15-6:00) Pe Tab-ul 2 cu un articol/document web, selectează textul. Apasă «Fă clar». Testează «✂️ Mai scurt», «• Buline» și «🔊 Ascultă».
5. (6:00-6:30) Pe /employer/index.html, încarcă exemplul de onboarding. Arată scorul, jargonul detectat și versiunea Easy-to-Read.
""")

    # ==========================================
    # SLIDE 6: Technical & Ethical AI (6:30 - 6:45)
    # ==========================================
    s6 = prs.slides.add_slide(blank_layout)
    add_bg(s6, C_SLATE_DARK)
    add_header(s6, "6:30 – 6:45 • Arhitectură & Etică AI", "Arhitectură Tehnică Robustă & Conformitate Europeană", "Construit la cele mai înalte standarde de accesibilitate și securitate a datelor.", dark_mode=True)

    tech_cards = [
        ("WCAG 2.2 AAA & Ergonomie", "Contrast măsurat de 19.5:1 (depășește cerința AAA de 7:1).\nOperare 100% din tastatură fără capcane de focus.\nȚinte tactile mari ≥ 44px și design tokens unificate.", C_TEAL),
        ("Verbatim Quote Grounding", "Algoritm backend verify_quotes garantează zero halucinații.\nFiecare dată, nume sau acțiune poartă un citat textual verificat direct în documentul original semnat.", C_AMBER),
        ("EU AI Act & Confidențialitate", "Conformitate deplină cu Articolul 5 (fără detecție de emoții).\nZero stocare de dosare medicale sau diagnostice.\nPreferințele și documentele rămân 100% în localStorage-ul Anei.", C_WHITE),
        ("Circuit Breaker & Fallback Chain", "Lanț inteligent de modele: Gemini -> Groq -> Ollama -> Mock.\nMotor euristic local offline capabil să funcționeze chiar dacă rețeaua sau internetul pică complet.", C_TEAL)
    ]

    for i, (head, desc, col) in enumerate(tech_cards):
        row = i // 2
        col_idx = i % 2
        x = Inches(0.8 + col_idx * 6.0)
        y = Inches(1.9 + row * 2.5)

        c = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, Inches(5.7), Inches(2.2))
        c.fill.solid()
        c.fill.fore_color.rgb = RGBColor(30, 41, 59)
        c.line.color.rgb = col
        c.line.width = Pt(1.5)
        tf = c.text_frame
        tf.word_wrap = True
        tf.margin_top = Inches(0.2)
        tf.margin_left = Inches(0.3)
        tf.margin_right = Inches(0.3)

        ph = tf.paragraphs[0]
        ph.text = head
        ph.font.size = Pt(17)
        ph.font.bold = True
        ph.font.color.rgb = col

        pd = tf.add_paragraph()
        pd.text = desc
        pd.font.size = Pt(12)
        pd.font.color.rgb = RGBColor(226, 232, 240)
        pd.space_before = Pt(8)

    set_notes(s6, """TIMING: 6:30 – 6:45 (0:15 min)
DISCURS PENTRU JURIU:
„Din punct de vedere tehnic și etic:
- WCAG 2.2 AAA: Avem un contrast verificat de 19.5:1, operare 100% din tastatură și ținte tactile generoase.
- Verbatim Grounding: Algoritmul nostru de backend verifică fiecare citat și elimină halucinațiile înainte ca răspunsul să ajungă la ecran.
- EU AI Act: Respectăm strict Articolul 5 interzicând deducerea emoțiilor la locul de muncă.
- Rezistență maximă: Aplicația funcționează online pe server, dar are și un motor euristic local capabil să ruleze complet offline fără internet.”
""")

    # ==========================================
    # SLIDE 7: Business Model & Conclusion (6:45 - 7:00)
    # ==========================================
    s7 = prs.slides.add_slide(blank_layout)
    add_bg(s7, C_SLATE_BG)
    add_header(s7, "6:45 – 7:00 • Sustenabilitate & Încheiere", "Model Sustenabil B2B & Impact Social Reale", "Cum transformăm Limpede dintr-un proiect de hackathon într-un standard național de incluziune.")

    biz_cards = [
        ("Pentru Angajați", "100% Gratuit, permanent.\nFără reclame, fără bariere financiare, fără partajare de date personale.", C_TEAL),
        ("B2B (Companii & HR)", "Abonament SaaS pentru portalul de audit de lizibilitate, conformitate CSRD/ESG și rapoarte de incluziune.", C_AMBER),
        ("Parteneriate Strategice", "Centre de carieră universitare, ONG-uri de sprijin și asociații ale persoanelor neurodivergente.", C_SLATE_DARK)
    ]
    for i, (head, desc, col) in enumerate(biz_cards):
        cx = Inches(0.8 + i * (3.7 + 0.3))
        c = s7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx, Inches(1.9), Inches(3.7), Inches(2.6))
        c.fill.solid()
        c.fill.fore_color.rgb = C_WHITE
        c.line.color.rgb = col
        c.line.width = Pt(2.0)
        tf = c.text_frame
        tf.word_wrap = True
        tf.margin_top = Inches(0.25)
        tf.margin_left = Inches(0.3)
        tf.margin_right = Inches(0.3)

        ph = tf.paragraphs[0]
        ph.text = head
        ph.font.size = Pt(18)
        ph.font.bold = True
        ph.font.color.rgb = col

        pd = tf.add_paragraph()
        pd.text = desc
        pd.font.size = Pt(12)
        pd.font.color.rgb = C_SLATE_DARK
        pd.space_before = Pt(10)

    # Big Final Quote Box
    qbox = s7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(4.8), Inches(11.7), Inches(1.9))
    qbox.fill.solid()
    qbox.fill.fore_color.rgb = C_SLATE_DARK
    qbox.line.color.rgb = C_AMBER
    qbox.line.width = Pt(2.0)
    tfq = qbox.text_frame
    tfq.word_wrap = True
    tfq.margin_top = Inches(0.25)
    tfq.margin_left = Inches(0.4)
    tfq.margin_right = Inches(0.4)

    pq = tfq.paragraphs[0]
    pq.text = "„Cu Limpede, prima zi de muncă nu mai este un test de anduranță cognitivă sau o sursă de panică, ci un parteneriat bazat pe claritate, demnitate și performanță.”"
    pq.font.size = Pt(17)
    pq.font.bold = True
    pq.font.italic = True
    pq.font.color.rgb = C_WHITE
    pq.alignment = PP_ALIGN.CENTER

    set_notes(s7, """TIMING: 6:45 – 7:00 (0:15 min)
DISCURS PENTRU JURIU (FRAZA FINALĂ DE IMPACT):
„Cu Limpede, prima zi de muncă nu mai este un test de anduranță cognitivă sau o sursă de panică, ci un parteneriat bazat pe claritate, demnitate și performanță.

Vă mulțumim din suflet și așteptăm cu entuziasm întrebările dumneavoastră!”
""")

    # ==========================================
    # SLIDE 8: Q&A & Contacts (7:00+)
    # ==========================================
    s8 = prs.slides.add_slide(blank_layout)
    add_bg(s8, C_SLATE_DARK)

    # Center Badge
    b8 = s8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(4.4), Inches(1.2), Inches(4.5), Inches(0.5))
    b8.fill.solid()
    b8.fill.fore_color.rgb = C_AMBER
    b8.line.fill.background()
    p = b8.text_frame.paragraphs[0]
    p.text = "SESIUNEA DE Q&A CU JURIUL"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = C_SLATE_DARK
    p.alignment = PP_ALIGN.CENTER

    t8 = s8.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(11.3), Inches(1.5))
    tf8 = t8.text_frame
    tf8.word_wrap = True
    p8 = tf8.paragraphs[0]
    p8.text = "Vă mulțumim! Întrebări & Răspunsuri"
    p8.font.size = Pt(40)
    p8.font.bold = True
    p8.font.color.rgb = C_WHITE
    p8.alignment = PP_ALIGN.CENTER

    # Summary metrics cards
    metrics = [
        ("441 Teste Verificate", "100% acoperire backend, endpoint-uri și tokeni CSS."),
        ("WCAG 2.2 AAA", "Contrast 19.5:1 și navigare fără mouse."),
        ("Manifest V3 Ready", "Extensie Chrome funcțională pe orice site web.")
    ]
    for i, (mtitle, msub) in enumerate(metrics):
        cx = Inches(1.2 + i * 3.8)
        c = s8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx, Inches(3.8), Inches(3.4), Inches(2.4))
        c.fill.solid()
        c.fill.fore_color.rgb = RGBColor(30, 41, 59)
        c.line.color.rgb = C_TEAL
        c.line.width = Pt(1.5)
        tf = c.text_frame
        tf.word_wrap = True
        tf.margin_top = Inches(0.3)
        tf.margin_left = Inches(0.2)
        tf.margin_right = Inches(0.2)

        p = tf.paragraphs[0]
        p.text = mtitle
        p.font.size = Pt(18)
        p.font.bold = True
        p.font.color.rgb = C_TEAL
        p.alignment = PP_ALIGN.CENTER

        p2 = tf.add_paragraph()
        p2.text = msub
        p2.font.size = Pt(13)
        p2.font.color.rgb = RGBColor(226, 232, 240)
        p2.space_before = Pt(12)
        p2.alignment = PP_ALIGN.CENTER

    set_notes(s8, """TIMING: 7:00 – 10:00 (3:00 min Q&A)
REPERE PENTRU RĂSPUNSURILE LA ÎNTREBĂRILE JURIULUI:
- Î: «De ce nu se trimit datele pe server?» -> R: „Pentru a respecta 100% confidențialitatea Anei și GDPR. Preferințele se salvează în localStorage.”
- Î: «Cum garantați că nu halucinează?» -> R: „Funcția noastră verify_quotes compară matematic fiecare citat cu textul sursă. Dacă un citat nu există verbatim, este eliminat automat.”
- Î: «De ce nu detectați emoțiile din voce?» -> R: „Regulamentul European AI Act interzice explicit detectarea emoțiilor la locul de muncă (Art. 5). Ne concentrăm doar pe transcriere și acțiuni concrete.”
""")

    prs.save(output_path)
    print(f"PPTX successfully created at: {output_path}")


def create_docx(output_path: str):
    doc = docx.Document()

    # Page Margins
    for section in doc.sections:
        section.top_margin = DocxInches(0.8)
        section.bottom_margin = DocxInches(0.8)
        section.left_margin = DocxInches(0.8)
        section.right_margin = DocxInches(0.8)

    # Styles
    title_p = doc.add_paragraph()
    title_run = title_p.add_run("Limpede — Pachet Complet Pitch & Live Demo (7 Minute)")
    title_run.font.name = "Arial"
    title_run.font.size = DocxPt(22)
    title_run.font.bold = True
    title_run.font.color.rgb = DocxRGBColor(13, 148, 136) # Teal
    title_p.paragraph_format.space_after = DocxPt(4)

    sub_p = doc.add_paragraph()
    sub_run = sub_p.add_run("Tema: AccessABILITY Hackathon 2026 — „First Job, Full Potential: AI for an Inclusive Start at Work”\nTagline: Adaptăm locul de muncă la om, nu invers.")
    sub_run.font.name = "Arial"
    sub_run.font.size = DocxPt(11)
    sub_run.font.italic = True
    sub_run.font.color.rgb = DocxRGBColor(100, 116, 139)
    sub_p.paragraph_format.space_after = DocxPt(16)

    # Section 1: Overview
    h1 = doc.add_heading("1. Cronologia Prezentării (Calibrat la fix 7:00 minute)", level=1)
    h1.paragraph_format.space_before = DocxPt(12)
    h1.paragraph_format.space_after = DocxPt(6)

    timing_table = doc.add_table(rows=5, cols=3)
    timing_table.style = 'Table Grid'
    timing_table.alignment = WD_TABLE_ALIGNMENT.CENTER

    t_headers = ["Segment / Interval", "Titlu Segment", "Obiectiv & Format"]
    for j, h in enumerate(t_headers):
        cell = timing_table.cell(0, j)
        shading = parse_xml(r'<w:shd {} w:fill="0D9488"/>'.format(nsdecls('w')))
        cell._tc.get_or_add_tcPr().append(shading)
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.font.bold = True
        r.font.color.rgb = DocxRGBColor(255, 255, 255)

    t_data = [
        ("0:00 – 1:00 (1:00 min)", "Problema & Cârligul Emoțional", "Povestea Anei (prima zi de muncă, 40 pagini birocrație, ADHD), statistica 68% abandon."),
        ("1:00 – 2:15 (1:15 min)", "Ecosistemul & Spectrul Funcțional", "Platformă Bilaterală (Angajat + HR) + Extensie Browser; tabelul concret al dizabilităților."),
        ("2:15 – 3:00 (0:45 min)", "Competiția: De ce Limpede?", "Matrice diferențiatoare vs ChatGPT & Grammarly: zero halucinații, protecție termene ambigue."),
        ("3:00 – 6:30 (3:30 min)", "LIVE DEMO Pas cu Pas", "5 pași: Profil fără diagnostic -> PDF cu «Arată în text» -> Planificator .ics -> Extensie -> HR Portal."),
    ]
    for i, row in enumerate(t_data):
        for j, val in enumerate(row):
            cell = timing_table.cell(i + 1, j)
            if i % 2 == 1:
                shading = parse_xml(r'<w:shd {} w:fill="F0FDFA"/>'.format(nsdecls('w')))
                cell._tc.get_or_add_tcPr().append(shading)
            p = cell.paragraphs[0]
            r = p.add_run(val)
            r.font.size = DocxPt(10)
            if j == 0:
                r.font.bold = True

    # Section 2: Narrative Pitch
    h2 = doc.add_heading("2. Discursul Narativ Detaliat (Pitch 0:00 – 3:00)", level=1)
    h2.paragraph_format.space_before = DocxPt(16)

    doc.add_heading("Slide 1: Problema Reală & Numele Aplicației (0:00 – 1:00)", level=2)
    p = doc.add_paragraph()
    r = p.add_run("„Faceți cunoștință cu Ana. Are 23 de ani, a terminat facultatea și astăzi este prima ei zi de muncă. Este inteligentă, entuziasmată și dornică să performeze. Dar în primele 2 ore de la sosire, primește un teanc de 40 de pagini de proceduri birocratice, e-mailuri cu termene vagi precum «cât mai repede» și instrucțiuni confuze.\n\nAna are o dizabilitate invizibilă: ADHD și anxietate socială. Îi este o frică paralizantă să întrebe pentru a treia oară ce înseamnă «Formularul F-12» sau «SecInfo v3», de teamă să nu pară incompetentă în perioada de probă.\n\nÎn România și în Uniunea Europeană, 1 din 6 tineri trăiește cu o dizabilitate, iar 68% din abandonurile la primul job se întâmplă din cauza comunicării inaccesibile și a fricii de stigmatizare. Pentru ei am creat Limpede.”")
    r.font.italic = True

    doc.add_heading("Slide 2: Ecosistemul Limpede — Ce Am Construit (1:00 – 1:40)", level=2)
    p = doc.add_paragraph()
    r = p.add_run("„Limpede este prima suită completă de asistență cognitivă la locul de muncă în limba română:\n1. Pentru Angajat: Asistent confidențial care clarifică documentele pas cu pas, extrage termene în calendar, sintetizează ședințe și redactează cereri oficiale de adaptare — fără să ceară vreodată diagnostic medical.\n2. Pentru Angajator: Portal de audit prin care departamentul HR măsoară lizibilitatea documentelor interne și generează automat versiuni în limbaj simplu (Easy-to-Read).\n3. Extensia de Browser Limpede: Funcționează direct pe orice aplicație web a companiei (Confluence, Jira, Gmail, Slack). Selectezi orice text stufos și primești claritate pe loc.”")
    r.font.italic = True

    doc.add_heading("Slide 3: Spectrul Funcțional — Ce Dizabilități Ajutăm (1:40 – 2:15)", level=2)

    dis_table = doc.add_table(rows=8, cols=3)
    dis_table.style = 'Table Grid'
    for j, h in enumerate(["Categorie / Nevoie", "Bariera la Locul de Muncă", "Cum rezolvă Limpede în cod?"]):
        cell = dis_table.cell(0, j)
        shading = parse_xml(r'<w:shd {} w:fill="0D9488"/>'.format(nsdecls('w')))
        cell._tc.get_or_add_tcPr().append(shading)
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.font.bold = True
        r.font.color.rgb = DocxRGBColor(255, 255, 255)

    dis_data = [
        ("Memorie & Reținere", "Uitarea instrucțiunilor complexe și a termenelor din prima zi", "Generează automat cardul prioritar «📌 De reținut imediat», dublează termenii cheie și bolduiește ancorele vizuale."),
        ("ADHD & Atenție", "Pierderea șirului în documente lungi de onboarding", "Elimină introducerile sterile; livrează maximum 3-4 pași prioritari, sub 10 cuvinte, cu verbe de acțiune la imperativ."),
        ("Vedere Scăzută / Fotofobie", "Efort vizual masiv pe tabele și fonturi mici", "Temă Contrast Ridicat (19.5:1 AAA), scalare 200%, pilule tactile mari (.keyword-prominent) pentru date și ore."),
        ("Autism & Literalitate", "Neînțelegerea metaforelor și glumelor de birou", "Decodifică cererile indirecte corporatiste și marchează obligatoriu orice glumă cu (posibilă glumă — nesigur)."),
        ("Dislexie", "Litere care dansează, oboseală de citire", "Fonturi speciale licențiate (OpenDyslexic, Atkinson Hyperlegible), riglă de citire și ghidaj bionic."),
        ("Deficiențe de Auz", "Pierderea deciziilor din ședințele verbale", "Transformă transcrierea în decizii și sarcini scrise cu responsabili asignați, fără a depinde de canale audio."),
        ("Dizabilități Motorii", "Dificultate la folosirea mouse-ului", "Ținte tactile mari (≥ 44px), operare 100% din tastatură, scurtătură globală (Alt + Shift + S).")
    ]
    for i, row in enumerate(dis_data):
        for j, val in enumerate(row):
            cell = dis_table.cell(i + 1, j)
            if i % 2 == 1:
                shading = parse_xml(r'<w:shd {} w:fill="F8FAFC"/>'.format(nsdecls('w')))
                cell._tc.get_or_add_tcPr().append(shading)
            p = cell.paragraphs[0]
            r = p.add_run(val)
            r.font.size = DocxPt(9.5)
            if j == 0:
                r.font.bold = True

    # Section 3: Live Demo Script
    h3 = doc.add_heading("3. Scenariul Live Demo Pas cu Pas (3:00 – 6:30 = 3:30 Min)", level=1)
    h3.paragraph_format.space_before = DocxPt(16)

    demo_steps = [
        ("Pasul 1 (3:00 – 3:35): Profil & Nevoi — Fără Diagnostic Medical",
         "1. Navigați la /employee/profile.html.\n2. Explicați: «Aici utilizatorul își definește stilul de lucru în propriile cuvinte».\n3. Lipiți: «am probleme mari de memorie și uit repede instrucțiunile. Vreau să îmi bolduiești orele și datele limită și să îmi pui ce am de reținut imediat».\n4. Apăsați «Salvează profilul» (apare notificarea verde). Datele rămân 100% pe calculatorul Anei în localStorage."),

        ("Pasul 2 (3:35 – 4:35): Încărcare PDF & Funcția Unică «Arată în text»",
         "1. Reveniți pe Acasă (+ -> «Încarcă PDF din calculator» -> ghid_onboarding_exemplu.pdf).\n2. Apăsați «Clarifică documentul».\n3. Arătați juriului: Cardul prioritar «📌 De reținut imediat», termenii cheie măriti în pilule tactile (LUNI 09:00, FORMULARUL F-12).\n4. Momentul cheie de încredere: Apăsați «Arată în text» la Pasul 1. Textul din stânga derulează și subliniază cu galben citatul exact din documentul sursă. Spuneți: «Fără halucinații. Utilizatorul are dovada verificată a fiecărei instrucțiuni»."),

        ("Pasul 3 (4:35 – 5:15): Planificatorul de Sarcini & Termene Ambigue",
         "1. Mergeți la /employee/plan.html.\n2. Apăsați «Încarcă e-mail exemplu» («Trimite raportul cât mai repede»).\n3. Apăsați «Extrage sarcini».\n4. Arătați badge-ul galben [De confirmat]: Limpede refuză să ghicească data!\n5. Selectați data, apăsați «Confirmă» și «Descarcă în Calendar (.ics)». Se descarcă fișierul compatibil Google Calendar și Outlook."),

        ("Pasul 4 (5:15 – 6:00): Extensia de Browser pe Orice Pagină Web",
         "1. Comutați pe Tab-ul 2 (pagina web de test).\n2. Deschideți setările extensiei: preferințele din site sunt sincronizate automat!\n3. Pe pagina de lectură, selectați un paragraf dens de text.\n4. Apăsați butonul plutitor «Fă clar» (sau Alt + Shift + S).\n5. În cardul Shadow DOM: Apăsați «✂️ Mai scurt» (comprimare la 35%), «• Buline», și «🔊 Ascultă» (voce sintetică ro-RO)."),

        ("Pasul 5 (6:00 – 6:30): Zona Angajatorului — Soluția Bilaterală",
         "1. Reveniți la /employer/index.html.\n2. Apăsați «Încarcă exemplu de onboarding» -> «Analizează documentul».\n3. Arătați Scorul de Lizibilitate (0-100), detectorul de jargon corporatist și versiunea generată automat Easy-to-Read.\n4. Spuneți: «Oferim companiilor instrumentul prin care să scrie documente umane înainte ca noul coleg să ajungă la birou».")
    ]

    for title, desc in demo_steps:
        doc.add_heading(title, level=2)
        p = doc.add_paragraph(desc)
        p.paragraph_format.space_after = DocxPt(8)

    # Section 4: Architecture & Closing
    h4 = doc.add_heading("4. Încheiere & Argumente Cheie pentru Juriu (6:30 – 7:00)", level=1)
    h4.paragraph_format.space_before = DocxPt(16)

    doc.add_paragraph("• WCAG 2.2 AAA: Contrast testat 19.5:1, navigare 100% tastatură, ținte tactile mari ≥ 44px.\n• Zero Halucinații: Algoritmul backend verify_quotes garantează integritatea fiecărui citat.\n• Conformitate EU AI Act: Zero recunoaștere emoțională la locul de muncă (Articolul 5).\n• Model Economic B2B: Gratuit pentru persoane fizice, licențiere SaaS a portalului de audit pentru companii responsabile.")

    final_quote = doc.add_paragraph()
    fq_run = final_quote.add_run("„Cu Limpede, prima zi de muncă nu mai este un test de anduranță cognitivă sau o sursă de panică, ci un parteneriat bazat pe claritate, demnitate și performanță. Vă mulțumim!”")
    fq_run.font.bold = True
    fq_run.font.size = DocxPt(12)
    fq_run.font.color.rgb = DocxRGBColor(13, 148, 136)

    doc.save(output_path)
    print(f"DOCX successfully created at: {output_path}")


def create_html(output_path: str):
    html_content = """<!DOCTYPE html>
<html lang="ro">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Limpede — Prezentare Pitch & Live Demo (7 Minute)</title>
  <style>
    :root {
      --primary: #0D9488;
      --primary-hover: #0F766E;
      --primary-subtle: #F0FDFA;
      --dark: #0F172A;
      --dark-card: #1E293B;
      --amber: #F59E0B;
      --bg: #F8FAFC;
      --surface: #FFFFFF;
      --text: #0F172A;
      --text-muted: #64748B;
      --border: #CBD5E1;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background-color: var(--dark);
      color: var(--text);
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
    }

    /* Top Controls Bar */
    header.slide-nav {
      background-color: rgba(15, 23, 42, 0.95);
      border-bottom: 1px solid #334155;
      padding: 10px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      color: #FFFFFF;
      z-index: 100;
    }
    .brand-title {
      font-size: 1.15rem;
      font-weight: 700;
      color: var(--primary);
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .brand-badge {
      background-color: var(--primary);
      color: white;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 0.8rem;
    }
    .nav-controls {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .nav-btn {
      background-color: #334155;
      color: white;
      border: 1px solid #475569;
      padding: 6px 14px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 0.9rem;
      font-weight: 600;
      transition: all 0.15s ease;
    }
    .nav-btn:hover {
      background-color: var(--primary);
      border-color: var(--primary);
    }
    .slide-counter {
      font-size: 0.95rem;
      font-weight: 600;
      color: var(--amber);
      min-width: 80px;
      text-align: center;
    }

    /* Stage Area */
    main.stage {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 24px;
      background: radial-gradient(circle at center, #1E293B 0%, #0F172A 100%);
    }

    .slide-viewport {
      width: 100%;
      max-width: 1280px;
      aspect-ratio: 16 / 9;
      background-color: var(--bg);
      border-radius: 12px;
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
      overflow: hidden;
      display: flex;
      flex-direction: column;
      position: relative;
    }

    /* Slide Styles */
    .slide {
      display: none;
      flex: 1;
      padding: 44px 56px;
      flex-direction: column;
      animation: fadeIn 0.25s ease;
    }
    .slide.active {
      display: flex;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .slide-dark {
      background-color: var(--dark);
      color: #FFFFFF;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      padding: 4px 12px;
      border-radius: 9999px;
      font-size: 0.85rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 12px;
      width: fit-content;
    }
    .badge-teal { background-color: var(--primary); color: white; }
    .badge-amber { background-color: var(--amber); color: var(--dark); }

    .slide-title {
      font-size: 2.2rem;
      font-weight: 800;
      color: var(--dark);
      line-height: 1.2;
      margin-bottom: 6px;
    }
    .slide-dark .slide-title {
      color: #FFFFFF;
    }
    .slide-subtitle {
      font-size: 1.15rem;
      color: var(--text-muted);
      margin-bottom: 24px;
    }
    .slide-dark .slide-subtitle {
      color: #94A3B8;
    }

    /* Cards Grid */
    .grid-3 {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 20px;
      flex: 1;
    }
    .grid-2 {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 20px;
      flex: 1;
    }
    .grid-5 {
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 14px;
      flex: 1;
    }

    .card {
      background: var(--surface);
      border: 1.5px solid var(--border);
      border-radius: 10px;
      padding: 22px;
      display: flex;
      flex-direction: column;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .card-dark {
      background: var(--dark-card);
      border-color: #334155;
      color: #FFFFFF;
    }
    .card-title {
      font-size: 1.2rem;
      font-weight: 700;
      color: var(--primary);
      margin-bottom: 12px;
    }
    .card-dark .card-title {
      color: var(--amber);
    }
    .card ul {
      list-style-type: none;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .card ul li {
      font-size: 0.92rem;
      line-height: 1.45;
      position: relative;
      padding-left: 16px;
    }
    .card ul li::before {
      content: "•";
      position: absolute;
      left: 0;
      color: var(--primary);
      font-weight: bold;
    }

    /* Tables */
    table.a11y-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.88rem;
      background: white;
      border-radius: 8px;
      overflow: hidden;
      border: 1px solid var(--border);
    }
    table.a11y-table th {
      background-color: var(--primary);
      color: white;
      padding: 10px 14px;
      text-align: left;
      font-weight: 700;
    }
    table.a11y-table td {
      padding: 8px 14px;
      border-bottom: 1px solid #E2E8F0;
      vertical-align: top;
      color: var(--dark);
    }
    table.a11y-table tr:nth-child(even) td {
      background-color: var(--primary-subtle);
    }

    /* Notes Drawer */
    #notes-panel {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      background: rgba(15, 23, 42, 0.95);
      border-top: 2px solid var(--amber);
      color: #E2E8F0;
      padding: 16px 24px;
      font-size: 0.92rem;
      line-height: 1.5;
      max-height: 35%;
      overflow-y: auto;
      display: none;
      backdrop-filter: blur(8px);
      z-index: 50;
    }
    #notes-panel.open { display: block; }
    .notes-tag {
      color: var(--amber);
      font-weight: 700;
      text-transform: uppercase;
      font-size: 0.8rem;
      margin-bottom: 4px;
    }

    /* Footer progress */
    .progress-bar-container {
      height: 4px;
      background-color: #334155;
      width: 100%;
    }
    .progress-bar {
      height: 100%;
      background-color: var(--primary);
      width: 12.5%;
      transition: width 0.2s ease;
    }
  </style>
</head>
<body>

  <header class="slide-nav">
    <div class="brand-title">
      <span class="brand-badge">PZ</span> Limpede — Pitch &amp; Live Demo (7:00 Min)
    </div>
    <div class="nav-controls">
      <button class="nav-btn" onclick="toggleNotes()">📝 Note Prezentator [N]</button>
      <button class="nav-btn" onclick="prevSlide()">◀ Înapoi [←]</button>
      <span id="counter" class="slide-counter">1 / 8</span>
      <button class="nav-btn" onclick="nextSlide()">Înainte [→] ▶</button>
      <button class="nav-btn" onclick="toggleFullScreen()">⛶ Ecran Complet [F]</button>
    </div>
  </header>

  <div class="progress-bar-container">
    <div id="progress" class="progress-bar"></div>
  </div>

  <main class="stage">
    <div class="slide-viewport">

      <!-- SLIDE 1: Title & Hook -->
      <section class="slide slide-dark active" data-notes="TIMING: 0:00 – 1:00\n„Faceți cunoștință cu Ana. Are 23 de ani, a terminat facultatea și astăzi este prima ei zi de muncă. Este inteligentă, entuziasmată și dornică să performeze. Dar în primele 2 ore de la sosire, primește un teanc de 40 de pagini de proceduri birocratice, e-mailuri cu termene vagi precum «cât mai repede» și instrucțiuni confuze.\n\nAna are o dizabilitate invizibilă: ADHD și anxietate socială. Îi este o frică paralizantă să întrebe pentru a treia oară ce înseamnă «Formularul F-12» sau «SecInfo v3», de teamă să nu pară incompetentă în perioada de probă.\n\nÎn România și în Uniunea Europeană, 1 din 6 tineri trăiește cu o dizabilitate, iar 68% din abandonurile la primul job se întâmplă din cauza comunicării inaccesibile și a fricii de stigmatizare. Pentru ei am creat Limpede.”">
        <div class="badge badge-teal">AccessABILITY Hackathon 2026</div>
        <h1 class="slide-title" style="font-size: 3.5rem; margin-top: 10px;">Limpede</h1>
        <p style="font-size: 1.6rem; font-weight: 700; color: var(--amber); margin-bottom: 8px;">Primul pas la primul job, fără bariere de înțelegere.</p>
        <p style="font-size: 1.15rem; font-style: italic; color: #94A3B8; margin-bottom: 34px;">Adaptăm locul de muncă la om, nu invers.</p>

        <div class="grid-3">
          <div class="card card-dark" style="border-color: var(--amber);">
            <div style="font-size: 2rem; font-weight: 800; color: var(--amber); margin-bottom: 8px;">68% Abandon</div>
            <p style="font-size: 0.95rem; color: #CBD5E1; line-height: 1.45;">din abandonurile la primul job se produc din cauza comunicării inaccesibile și a fricii de stigmatizare.</p>
          </div>
          <div class="card card-dark" style="border-color: var(--primary);">
            <div style="font-size: 2rem; font-weight: 800; color: var(--primary); margin-bottom: 8px;">1 din 6 Tineri</div>
            <p style="font-size: 0.95rem; color: #CBD5E1; line-height: 1.45;">trăiește cu o dizabilitate sau o neurodivergență (ADHD, autism, anxietate, dislexie).</p>
          </div>
          <div class="card card-dark" style="border-color: #64748B;">
            <div style="font-size: 2rem; font-weight: 800; color: #FFFFFF; margin-bottom: 8px;">Fără Diagnostic</div>
            <p style="font-size: 0.95rem; color: #CBD5E1; line-height: 1.45;">Zero etichete de boală sau dosare medicale. Personalizarea se face 100% pe baza confortului ales.</p>
          </div>
        </div>
      </section>

      <!-- SLIDE 2: Ecosystem -->
      <section class="slide" data-notes="TIMING: 1:00 – 1:40\n„Limpede este prima suită completă de asistență cognitivă la locul de muncă în limba română:\n1. Pentru Angajat: Asistent confidențial care clarifică documentele pas cu pas, extrage termene în calendar, sintetizează ședințe și redactează cereri oficiale de adaptare — fără să ceară vreodată diagnostic medical.\n2. Pentru Angajator: Portal de audit prin care departamentul HR măsoară lizibilitatea documentelor interne și generează automat versiuni în limbaj simplu (Easy-to-Read).\n3. Extensia de Browser Limpede: Funcționează direct pe orice aplicație web a companiei (Confluence, Jira, Gmail, Slack). Selectezi orice text stufos și primești claritate pe loc.”">
        <div class="badge badge-teal">1:00 – 1:40 • Ecosistemul Limpede</div>
        <h2 class="slide-title">Soluție Unificată: Platformă Web + Extensie Browser</h2>
        <p class="slide-subtitle">O suită integrată care conectează angajatul cu compania și funcționează direct peste fluxul de lucru.</p>

        <div class="grid-3">
          <div class="card">
            <div class="card-title">1. Zona Angajatului</div>
            <ul>
              <li>Clarificare pas-cu-pas a procedurilor interne.</li>
              <li>Ancore tactile mari pentru date, ore și coduri cheie.</li>
              <li>Planificator cu protecție pe termene vagi &amp; export .ics.</li>
              <li>Asistent de ședință: audio -&gt; decizii scrise.</li>
              <li>Cereri de adaptare legale fără diagnostic medical.</li>
            </ul>
          </div>
          <div class="card">
            <div class="card-title" style="color: var(--amber);">2. Zona Angajatorului (HR)</div>
            <ul>
              <li>Scanner de lizibilitate documente interne (scor 0-100).</li>
              <li>Detector automat de jargon corporatist și acronime.</li>
              <li>Semnalare fraze peste 25 de cuvinte greu de parcurs.</li>
              <li>Generator automat versiune Easy-to-Read.</li>
              <li>Conformitate directă ESG / CSRD și incluziune reală.</li>
            </ul>
          </div>
          <div class="card">
            <div class="card-title">3. Extensia de Browser</div>
            <ul>
              <li>Funcționează pe Confluence, Jira, Gmail, Slack.</li>
              <li>Selectezi text stufos -&gt; apeși «Fă clar».</li>
              <li>Card Shadow DOM complet izolat de stilurile paginii.</li>
              <li>Comprimare la 35% («✂️ Mai scurt») și transformare în buline.</li>
              <li>Sinteză vocală naturală în limba română (ro-RO).</li>
            </ul>
          </div>
        </div>
      </section>

      <!-- SLIDE 3: Disabilities -->
      <section class="slide" data-notes="TIMING: 1:40 – 2:15\n„Cum arată incluziunea reală în codul Limpede? Am mapat fiecare barieră la o rezolvare tehnică precisă:\n- Memorie: Cardul prioritar «De reținut imediat» plasează esențialul în fruntea ecranului.\n- ADHD: Eliminăm introducerile sterile; afișăm doar 3-4 pași scurți, imperativi, sub 10 cuvinte.\n- Vedere: Temă Contrast Ridicat 19.5:1 AAA, scalare la 200% și pilule tactile pentru ore și date.\n- Autism: Decodificăm cererile corporatiste indirecte și marcăm glumele ca «posibilă glumă — nesigur».\n- Dislexie: Fonturi licențiate OpenDyslexic și Atkinson Hyperlegible.\n- Auz: Transcriere cu extragere de decizii scrise și sarcini cu responsabili.\n- Motor: Totul funcționează 100% din tastatură, cu ținte tactile mari de peste 44px.”">
        <div class="badge badge-teal">1:40 – 2:15 • Spectrul Funcțional</div>
        <h2 class="slide-title">Incluziune Reală pentru Întreg Spectrul Funcțional</h2>
        <p class="slide-subtitle">Design universal: adaptări concrete în cod pentru fiecare tip de nevoie cognitivă sau senzorială.</p>

        <table class="a11y-table">
          <thead>
            <tr>
              <th style="width: 25%;">Categorie / Nevoie</th>
              <th style="width: 32%;">Bariera la Locul de Muncă</th>
              <th style="width: 43%;">Cum rezolvă Limpede în cod?</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Memorie &amp; Reținere</strong></td>
              <td>Uitarea instrucțiunilor și a termenelor din prima zi</td>
              <td>Card prioritar <strong>«📌 De reținut imediat»</strong>, dublare termeni cheie, pilule tactile.</td>
            </tr>
            <tr>
              <td><strong>ADHD &amp; Atenție</strong></td>
              <td>Pierderea șirului în documente lungi de 40 pagini</td>
              <td>Filtru politețuri; <strong>maximum 3-4 pași sub 10 cuvinte</strong> cu verbe la imperativ.</td>
            </tr>
            <tr>
              <td><strong>Vedere Scăzută / Fotofobie</strong></td>
              <td>Efort masiv pe fonturi mici și tabele neclare</td>
              <td>Temă <strong>Contrast Ridicat (19.5:1 AAA)</strong>, fonturi mărite 200%, pilule tactile mari.</td>
            </tr>
            <tr>
              <td><strong>Autism &amp; Literalitate</strong></td>
              <td>Confuzie la metafore corporatiste și glume</td>
              <td>Decodificare cereri indirecte; etichetare obligatorie: <code>(posibilă glumă — nesigur)</code>.</td>
            </tr>
            <tr>
              <td><strong>Dislexie</strong></td>
              <td>Litere care dansează, oboseală la lectură</td>
              <td>Fonturi <strong>OpenDyslexic</strong> și <strong>Atkinson Hyperlegible</strong>, riglă și ghidaj bionic.</td>
            </tr>
            <tr>
              <td><strong>Deficiențe de Auz</strong></td>
              <td>Pierderea deciziilor din ședințele verbale</td>
              <td>Transformare audio în <strong>decizii scrise și sarcini cu responsabili asignați</strong>.</td>
            </tr>
            <tr>
              <td><strong>Dizabilități Motorii</strong></td>
              <td>Dificultate la folosirea mouse-ului</td>
              <td>Ținte tactile mari (≥ 44px), navigare <strong>100% din tastatură</strong>, Alt + Shift + S.</td>
            </tr>
          </tbody>
        </table>
      </section>

      <!-- SLIDE 4: Competition -->
      <section class="slide" data-notes="TIMING: 2:15 – 3:00\n„De ce nu folosește Ana pur și simplu ChatGPT sau un corector gramatical?\n1. Zero Halucinații: ChatGPT inventează date când nu știe. Limpede verifică algoritmic fiecare citat și oferă butonul «Arată în text» — dovada matematică a sursei.\n2. Protecție pe Termene Ambigue: La fraza «trimite cât mai repede», ChatGPT ar fi ghicit o dată oarecare. Limpede refuză să ghicească, marchează cu [De confirmat] și exportă fișier .ics.\n3. Confidențialitate & Fără Etichete Medicale: Nu cerem dosar medical. Preferințele se salvează 100% în browser (localStorage).\n4. Conformitate Europeană (EU AI Act): Interzicem strict recunoașterea emoțiilor la locul de muncă (Articolul 5).”">
        <div class="badge badge-teal">2:15 – 3:00 • Diferențiatori</div>
        <h2 class="slide-title">De Ce Nu ChatGPT, Grammarly sau Portalele HR Clasice?</h2>
        <p class="slide-subtitle">Matrice de conformitate și protecție cognitivă.</p>

        <table class="a11y-table">
          <thead>
            <tr>
              <th>Criteriu de Evaluare</th>
              <th>ChatGPT / Generic</th>
              <th>Grammarly</th>
              <th>Portaluri HR</th>
              <th style="background-color: var(--amber); color: var(--dark);">Limpede (Noi)</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Garantarea Adevărului</strong></td>
              <td>❌ Halucinează date și termene</td>
              <td>❌ Doar gramatică</td>
              <td>❌ Nu simplifică</td>
              <td><strong>✅ Verbatim Quote Grounding:</strong> «Arată în text» aprinde sursa</td>
            </tr>
            <tr>
              <td><strong>Protecție Termene Ambigue</strong></td>
              <td>❌ Ghicește o dată arbitrară</td>
              <td>❌ Indiferent</td>
              <td>❌ Creează confuzie</td>
              <td><strong>✅ Refuză să ghicească:</strong> marchează [De confirmat] + .ics</td>
            </tr>
            <tr>
              <td><strong>Fără Date Medicale Invazive</strong></td>
              <td>❌ Cere diagnostic medical</td>
              <td>❌ Fără profil de nevoi</td>
              <td>❌ Cere certificat handicap</td>
              <td><strong>✅ 100% Funcțional:</strong> confort personal, zero etichete</td>
            </tr>
            <tr>
              <td><strong>Conformitate EU AI Act</strong></td>
              <td>❌ Neclar</td>
              <td>❌ Cloud SUA</td>
              <td>❌ Static</td>
              <td><strong>✅ Articolul 5:</strong> Interzice strict detectarea emoțiilor din voce/text</td>
            </tr>
            <tr>
              <td><strong>Disponibilitate Offline</strong></td>
              <td>❌ Doar online</td>
              <td>❌ Doar online</td>
              <td>❌ Variabil</td>
              <td><strong>✅ Salvare 100% localStorage + motor euristic de rezervă</strong></td>
            </tr>
            <tr>
              <td><strong>Integrare Oriunde pe Web</strong></td>
              <td>❌ Copy-paste continuu</td>
              <td>⚠️ Doar verificare text</td>
              <td>❌ Închis</td>
              <td><strong>✅ Extensie Browser:</strong> card plutitor peste orice aplicație</td>
            </tr>
          </tbody>
        </table>
      </section>

      <!-- SLIDE 5: Demo Workflow -->
      <section class="slide" data-notes="TIMING: 3:00 – 6:30 (3:30 min)\n1. (3:00-3:35) Deschide /employee/profile.html. Lipește: «am probleme mari de memorie și uit repede instrucțiunile...». Salvează.\n2. (3:35-4:35) Pe Acasă, încarcă ghid_onboarding_exemplu.pdf. Arată cardul «De reținut» și apasă «Arată în text» la Pasul 1 (se luminează în stânga!).\n3. (4:35-5:15) Pe Planificator (/employee/plan.html), încarcă exemplul managerial. Arată [De confirmat] și exportă calendar .ics.\n4. (5:15-6:00) Pe Tab-ul 2, selectează text. Apasă «Fă clar». Testează «✂️ Mai scurt», buline și vocea ro-RO.\n5. (6:00-6:30) Pe /employer/index.html, arată scorul de lizibilitate și generarea Easy-to-Read.">
        <div class="badge badge-amber">3:00 – 6:30 • Live Demo</div>
        <h2 class="slide-title">Scenariul Live Demo Pas cu Pas (3:30 Min)</h2>
        <p class="slide-subtitle">Demonstrația practică a celor 5 capabilități fundamentale ale ecosistemului Limpede.</p>

        <div class="grid-5">
          <div class="card" style="border-top: 4px solid var(--primary);">
            <div style="font-size: 0.85rem; font-weight: 700; color: var(--primary);">PASUL 1 (0:35)</div>
            <div style="font-weight: 700; margin: 6px 0;">Profil &amp; Nevoi</div>
            <p style="font-size: 0.85rem; color: var(--text-muted);">Definire stil în propriile cuvinte. Fără diagnostic medical. Salvare 100% pe calculatorul Anei.</p>
          </div>
          <div class="card" style="border-top: 4px solid var(--amber);">
            <div style="font-size: 0.85rem; font-weight: 700; color: var(--amber);">PASUL 2 (1:00)</div>
            <div style="font-weight: 700; margin: 6px 0;">PDF &amp; «Arată în text»</div>
            <p style="font-size: 0.85rem; color: var(--text-muted);">Încărcare onboarding, card «De reținut», pilule tactile și verificarea citatului în sursă.</p>
          </div>
          <div class="card" style="border-top: 4px solid var(--primary);">
            <div style="font-size: 0.85rem; font-weight: 700; color: var(--primary);">PASUL 3 (0:45)</div>
            <div style="font-weight: 700; margin: 6px 0;">Planificator &amp; .ICS</div>
            <p style="font-size: 0.85rem; color: var(--text-muted);">Email «cât mai repede», protecție [De confirmat] și export Google Calendar / Outlook.</p>
          </div>
          <div class="card" style="border-top: 4px solid var(--amber);">
            <div style="font-size: 0.85rem; font-weight: 700; color: var(--amber);">PASUL 4 (0:45)</div>
            <div style="font-weight: 700; margin: 6px 0;">Extensie Browser</div>
            <p style="font-size: 0.85rem; color: var(--text-muted);">Selectare text pe orice site, butonul «Fă clar», «✂️ Mai scurt», buline și voce sintetică ro-RO.</p>
          </div>
          <div class="card" style="border-top: 4px solid var(--primary);">
            <div style="font-size: 0.85rem; font-weight: 700; color: var(--primary);">PASUL 5 (0:25)</div>
            <div style="font-weight: 700; margin: 6px 0;">Portal Angajator</div>
            <p style="font-size: 0.85rem; color: var(--text-muted);">Scor lizibilitate (0-100), detector jargon corporatist și generare Easy-to-Read.</p>
          </div>
        </div>
      </section>

      <!-- SLIDE 6: Tech & Ethics -->
      <section class="slide slide-dark" data-notes="TIMING: 6:30 – 6:45\n„Din punct de vedere tehnic și etic:\n- WCAG 2.2 AAA: Avem un contrast verificat de 19.5:1, operare 100% din tastatură și ținte tactile generoase.\n- Verbatim Grounding: Algoritmul nostru de backend verifică fiecare citat și elimină halucinațiile înainte ca răspunsul să ajungă la ecran.\n- EU AI Act: Respectăm strict Articolul 5 interzicând deducerea emoțiilor la locul de muncă.\n- Rezistență maximă: Aplicația funcționează online pe server, dar are și un motor euristic local capabil să ruleze complet offline fără internet.”">
        <div class="badge badge-teal">6:30 – 6:45 • Arhitectură &amp; Etică AI</div>
        <h2 class="slide-title">Arhitectură Tehnică Robustă &amp; Conformitate Europeană</h2>
        <p class="slide-subtitle">Construit la cele mai exigente standarde de accesibilitate și securitate a datelor.</p>

        <div class="grid-2">
          <div class="card card-dark" style="border-color: var(--primary);">
            <div class="card-title" style="color: var(--primary);">WCAG 2.2 AAA &amp; Ergonomie</div>
            <p style="font-size: 0.95rem; color: #CBD5E1; line-height: 1.5;">Contrast măsurat de 19.5:1 (depășește cerința AAA de 7:1). Operare 100% din tastatură fără capcane de focus. Ținte tactile mari ≥ 44px și design tokens unificate.</p>
          </div>
          <div class="card card-dark" style="border-color: var(--amber);">
            <div class="card-title" style="color: var(--amber);">Verbatim Quote Grounding</div>
            <p style="font-size: 0.95rem; color: #CBD5E1; line-height: 1.5;">Algoritm backend verify_quotes garantează zero halucinații. Fiecare dată, nume sau acțiune poartă un citat textual verificat direct în documentul original semnat.</p>
          </div>
          <div class="card card-dark" style="border-color: #64748B;">
            <div class="card-title" style="color: #FFFFFF;">EU AI Act &amp; Confidențialitate</div>
            <p style="font-size: 0.95rem; color: #CBD5E1; line-height: 1.5;">Conformitate deplină cu Articolul 5 (fără detecție de emoții). Zero stocare de dosare medicale sau diagnostice. Preferințele rămân 100% în localStorage-ul Anei.</p>
          </div>
          <div class="card card-dark" style="border-color: var(--primary);">
            <div class="card-title" style="color: var(--primary);">Circuit Breaker &amp; Fallback Chain</div>
            <p style="font-size: 0.95rem; color: #CBD5E1; line-height: 1.5;">Lanț inteligent de modele: Gemini -&gt; Groq -&gt; Ollama -&gt; Mock. Motor euristic local offline capabil să funcționeze chiar dacă rețeaua sau internetul pică complet.</p>
          </div>
        </div>
      </section>

      <!-- SLIDE 7: Business Model & Conclusion -->
      <section class="slide" data-notes="TIMING: 6:45 – 7:00\n„Cu Limpede, prima zi de muncă nu mai este un test de anduranță cognitivă sau o sursă de panică, ci un parteneriat bazat pe claritate, demnitate și performanță.\n\nVă mulțumim din suflet și așteptăm cu entuziasm întrebările dumneavoastră!”">
        <div class="badge badge-teal">6:45 – 7:00 • Sustenabilitate &amp; Încheiere</div>
        <h2 class="slide-title">Model Sustenabil B2B &amp; Impact Social Real</h2>
        <p class="slide-subtitle">Cum transformăm Limpede dintr-un proiect de hackathon într-un standard național de incluziune.</p>

        <div class="grid-3" style="margin-bottom: 24px;">
          <div class="card" style="border-top: 4px solid var(--primary);">
            <div class="card-title">Pentru Angajați</div>
            <p style="font-size: 0.95rem; color: var(--dark); line-height: 1.45;"><strong>100% Gratuit, permanent.</strong> Fără reclame, fără bariere financiare, fără partajare de date personale.</p>
          </div>
          <div class="card" style="border-top: 4px solid var(--amber);">
            <div class="card-title" style="color: var(--amber);">B2B (Companii &amp; HR)</div>
            <p style="font-size: 0.95rem; color: var(--dark); line-height: 1.45;">Abonament SaaS pentru portalul de audit de lizibilitate, conformitate CSRD/ESG și rapoarte de incluziune.</p>
          </div>
          <div class="card" style="border-top: 4px solid #334155;">
            <div class="card-title" style="color: #334155;">Parteneriate Strategice</div>
            <p style="font-size: 0.95rem; color: var(--dark); line-height: 1.45;">Centre de carieră universitare, ONG-uri de sprijin și asociații ale persoanelor neurodivergente.</p>
          </div>
        </div>

        <div class="card" style="background-color: var(--dark); border-color: var(--amber); color: white; padding: 20px 30px; text-align: center;">
          <p style="font-size: 1.25rem; font-style: italic; font-weight: 700; line-height: 1.4;">
            „Cu Limpede, prima zi de muncă nu mai este un test de anduranță cognitivă sau o sursă de panică, ci un parteneriat bazat pe claritate, demnitate și performanță.”
          </p>
        </div>
      </section>

      <!-- SLIDE 8: Q&A -->
      <section class="slide slide-dark" data-notes="TIMING: 7:00 – 10:00 (Q&A)\n- Î: «De ce nu se trimit datele pe server?» -> R: „Pentru a respecta 100% confidențialitatea Anei și GDPR. Preferințele se salvează în localStorage.”\n- Î: «Cum garantați că nu halucinează?» -> R: „Funcția noastră verify_quotes compară matematic fiecare citat cu textul sursă. Dacă un citat nu există verbatim, este eliminat automat.”\n- Î: «De ce nu detectați emoțiile din voce?» -> R: „Regulamentul European AI Act interzice explicit detectarea emoțiilor la locul de muncă (Art. 5). Ne concentrăm doar pe transcriere și acțiuni concrete.”">
        <div style="text-align: center; margin-top: 20px;">
          <div class="badge badge-amber" style="margin: 0 auto 16px;">Sesiune Q&amp;A Juriu (3:00 Min)</div>
          <h1 class="slide-title" style="font-size: 3.2rem; margin-bottom: 12px;">Vă mulțumim!</h1>
          <p style="font-size: 1.35rem; color: #94A3B8; margin-bottom: 36px;">Așteptăm cu drag întrebările dumneavoastră.</p>

          <div class="grid-3" style="max-width: 900px; margin: 0 auto;">
            <div class="card card-dark" style="border-color: var(--primary);">
              <div style="font-size: 1.6rem; font-weight: 800; color: var(--primary); margin-bottom: 6px;">441 Teste</div>
              <p style="font-size: 0.9rem; color: #CBD5E1;">100% teste trecute (backend, contracte, a11y, tokens).</p>
            </div>
            <div class="card card-dark" style="border-color: var(--amber);">
              <div style="font-size: 1.6rem; font-weight: 800; color: var(--amber); margin-bottom: 6px;">WCAG 2.2 AAA</div>
              <p style="font-size: 0.9rem; color: #CBD5E1;">Contrast 19.5:1, navigare completă din tastatură.</p>
            </div>
            <div class="card card-dark" style="border-color: var(--primary);">
              <div style="font-size: 1.6rem; font-weight: 800; color: var(--primary); margin-bottom: 6px;">Manifest V3</div>
              <p style="font-size: 0.9rem; color: #CBD5E1;">Extensie de browser gata de utilizat pe orice site.</p>
            </div>
          </div>
        </div>
      </section>

      <!-- Notes Drawer -->
      <div id="notes-panel">
        <div class="notes-tag">📝 Notițe Prezentator (Spoken Script &amp; Cues):</div>
        <div id="notes-content"></div>
      </div>

    </div>
  </main>

  <script>
    const slides = document.querySelectorAll('.slide');
    const counter = document.getElementById('counter');
    const progressBar = document.getElementById('progress');
    const notesPanel = document.getElementById('notes-panel');
    const notesContent = document.getElementById('notes-content');
    let currentIndex = 0;

    function updateSlide(index) {
      if (index < 0) index = 0;
      if (index >= slides.length) index = slides.length - 1;
      currentIndex = index;

      slides.forEach((s, i) => {
        s.classList.toggle('active', i === currentIndex);
      });

      counter.textContent = `${currentIndex + 1} / ${slides.length}`;
      progressBar.style.width = `${((currentIndex + 1) / slides.length) * 100}%`;

      const activeSlide = slides[currentIndex];
      const rawNotes = activeSlide.getAttribute('data-notes') || 'Fără notițe.';
      notesContent.innerHTML = rawNotes.replace(/\\n/g, '<br>');
    }

    function prevSlide() { updateSlide(currentIndex - 1); }
    function nextSlide() { updateSlide(currentIndex + 1); }

    function toggleNotes() {
      notesPanel.classList.toggle('open');
    }

    function toggleFullScreen() {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen();
      } else {
        if (document.exitFullscreen) document.exitFullscreen();
      }
    }

    document.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') {
        nextSlide();
      } else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
        prevSlide();
      } else if (e.key === 'n' || e.key === 'N') {
        toggleNotes();
      } else if (e.key === 'f' || e.key === 'F') {
        toggleFullScreen();
      }
    });

    updateSlide(0);
  </script>
</body>
</html>
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"HTML presentation successfully created at: {output_path}")


def main():
    docs_dir = os.path.join(os.getcwd(), "docs")
    os.makedirs(docs_dir, exist_ok=True)

    pptx_path = os.path.join(docs_dir, "prezentare_limpede.pptx")
    docx_path = os.path.join(docs_dir, "prezentare_limpede.docx")
    html_path = os.path.join(docs_dir, "prezentare.html")

    create_pptx(pptx_path)
    create_docx(docx_path)
    create_html(html_path)

    print("\n✅ All presentation formats generated successfully:")
    print(f"1. PowerPoint: {pptx_path}")
    print(f"2. Word:       {docx_path}")
    print(f"3. HTML Web:   {html_path}")


if __name__ == "__main__":
    main()
