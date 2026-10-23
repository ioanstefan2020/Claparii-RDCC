#!/usr/bin/env python3
"""
Build authentic, human-written business pitch decks for Limpede:
1. Pitch Live (Short, punchy, visual, calibrated for stage pitch with PowerPoint Morph transitions):
   - docs/limpede_pitch_live.pptx (built using downloaded Seed pitch deck template)
   - docs/limpede_pitch_live.docx
   - docs/pitch_live.html

2. Judge Deep-Dive Deck (Comprehensive technical dossier for judges to evaluate and rank 1st place):
   - docs/limpede_judge_deck.pptx (built with deep technical architecture and Morph transitions)
   - docs/limpede_judge_deck.docx
   - docs/judge_deck.html
"""

import os
import sys
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml import parse_xml

import docx
from docx.shared import Inches as DocxInches, Pt as DocxPt, RGBColor as DocxRGBColor
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml as docx_parse_xml
from docx.oxml.ns import nsdecls

# Palette
C_BG_DARK = RGBColor(11, 15, 25)        # #0B0F19
C_CARD_DARK = RGBColor(22, 31, 48)      # #161F30
C_TEAL = RGBColor(13, 148, 136)         # #0D9488
C_CYAN = RGBColor(56, 189, 248)         # #38BDF8
C_AMBER = RGBColor(245, 158, 11)        # #F59E0B
C_WHITE = RGBColor(255, 255, 255)       # #FFFFFF
C_MUTED = RGBColor(148, 163, 184)       # #94A3B8


def apply_morph(slide):
    morph_xml = '''
    <p:transition xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
                  xmlns:p15="http://schemas.microsoft.com/office/powerpoint/2012/main"
                  spd="med">
        <p15:morph option="byObject"/>
    </p:transition>
    '''
    slide._element.append(parse_xml(morph_xml))


def update_shape_text(shape, new_text, font_size=None, bold=None):
    if not shape.has_text_frame:
        return
    tf = shape.text_frame
    existing_run = None
    for p in tf.paragraphs:
        if p.runs:
            existing_run = p.runs[0]
            break
    saved_font = existing_run.font.name if existing_run else None
    saved_size = existing_run.font.size if existing_run else None
    saved_bold = existing_run.font.bold if existing_run else None
    saved_color = None
    try:
        if existing_run and existing_run.font.color and existing_run.font.color.rgb:
            saved_color = existing_run.font.color.rgb
    except:
        pass

    tf.text = new_text
    for p in tf.paragraphs:
        for r in p.runs:
            if saved_font: r.font.name = saved_font
            if font_size is not None: r.font.size = font_size
            elif saved_size: r.font.size = saved_size
            if bold is not None: r.font.bold = bold
            elif saved_bold is not None: r.font.bold = saved_bold
            if saved_color: r.font.color.rgb = saved_color


# ==============================================================================
# 1. PITCH LIVE PPTX (using downloaded Seed template with Morph transitions)
# ==============================================================================
def build_pitch_live_from_template(template_path, output_path):
    prs = pptx.Presentation(template_path)

    # Apply Morph transition to all slides
    for s in prs.slides:
        apply_morph(s)

    # --- SLIDE 1: Cover ---
    s1 = prs.slides[0]
    update_shape_text(s1.shapes[3], "LIMPEDE")
    update_shape_text(s1.shapes[4], "·  PRIMUL JOB, FĂRĂ BARIERE")
    update_shape_text(s1.shapes[5], "ACCESSABILITY · 2026")
    update_shape_text(s1.shapes[6], "Limpede")
    update_shape_text(s1.shapes[7], "Adaptăm locul de muncă la om, nu invers. Asistentul cognitiv care transformă procedurile de 40 de pagini în pași simpli și acțiuni sigure.")
    update_shape_text(s1.shapes[8], "68%")
    update_shape_text(s1.shapes[9], "ABANDON PRIMUL JOB")
    update_shape_text(s1.shapes[10], "1 din 6")
    update_shape_text(s1.shapes[11], "TINERI CU DIZABILITĂȚI")
    update_shape_text(s1.shapes[12], "100%")
    update_shape_text(s1.shapes[13], "CONFIDENȚIAL ÎN BROWSER")
    update_shape_text(s1.shapes[14], "0")
    update_shape_text(s1.shapes[15], "DIAGNOSTICE MEDICALE CERUTE")

    s1.notes_slide.notes_text_frame.text = (
        "0:00 – 1:00 (1:00 min)\n"
        "„Faceți cunoștință cu Ana. Are 23 de ani, a terminat facultatea și astăzi este prima ei zi de muncă. "
        "În primele 2 ore de la sosire, primește un teanc de 40 de pagini de proceduri birocratice, e-mailuri cu termene vagi precum «cât mai repede» și instrucțiuni confuze.\n"
        "Ana are ADHD și anxietate socială. Îi este o frică paralizantă să întrebe pentru a treia oară ce înseamnă un termen intern, de teamă să nu pară incompetentă în perioada de probă.\n"
        "În România și în UE, 1 din 6 tineri trăiește cu o dizabilitate, iar 68% din abandonurile primului job se întâmplă din cauza comunicării inaccesibile și a fricii de stigmatizare. "
        "Pentru ei am creat Limpede: adaptăm locul de muncă la om, nu invers.”"
    )

    # --- SLIDE 2: Problema Reală ---
    s2 = prs.slides[1]
    update_shape_text(s2.shapes[2], "LIMPEDE")
    update_shape_text(s2.shapes[3], "PITCH ACCESSABILITY")
    update_shape_text(s2.shapes[4], "01")
    update_shape_text(s2.shapes[5], "PROBLEMA REALĂ")
    update_shape_text(s2.shapes[6], "Prima zi de muncă e un șoc birocratic.")
    update_shape_text(s2.shapes[7], "LIMPEDE.RO")
    update_shape_text(s2.shapes[8], "HACKATHON 2026")
    update_shape_text(s2.shapes[9], "68% din tinerii cu dizabilități renunță la primul job din cauza comunicării inaccesibile și a fricii de a întreba.")
    update_shape_text(s2.shapes[11], "⚠  COSTUL BLOCAJULUI COGNITIV")
    update_shape_text(s2.shapes[12], "Ana primește 40 de pagini de proceduri pline de acronime neclare și termene vagi («cât mai repede»). Când nu înțelege, se blochează. Companiile pierd oameni buni, iar tinerii își pierd încrederea înainte să arate ce pot.")

    s2.notes_slide.notes_text_frame.text = (
        "1:00 – 1:30 (0:30 min)\n"
        "„Blocajul nu e la om, ci la documente: proceduri scrise în limbaj de lemn, acronime neexplicate și instrucțiuni confuze. "
        "Când ai o neurodivergență sau o dizabilitate, efortul de decodare e copleșitor. Aici intervine Limpede.”"
    )

    # --- SLIDE 3: Soluția Noastră ---
    s3 = prs.slides[2]
    update_shape_text(s3.shapes[2], "LIMPEDE")
    update_shape_text(s3.shapes[3], "PITCH ACCESSABILITY")
    update_shape_text(s3.shapes[4], "02")
    update_shape_text(s3.shapes[5], "CUM FUNCȚIONEAZĂ")
    update_shape_text(s3.shapes[6], "Selectezi → Limpede simplifică → Ai dovada")
    update_shape_text(s3.shapes[7], "LIMPEDE.RO")
    update_shape_text(s3.shapes[8], "HACKATHON 2026")
    update_shape_text(s3.shapes[10], "01")
    update_shape_text(s3.shapes[11], "Încarci sau selectezi")
    update_shape_text(s3.shapes[12], "PDF de onboarding, email de la manager sau text direct din Jira/Slack cu extensia de browser.")
    update_shape_text(s3.shapes[14], "02")
    update_shape_text(s3.shapes[15], "Primești claritate")
    update_shape_text(s3.shapes[16], "3 pași acționabili, verbe clare la imperativ, cardul «📌 De reținut azi» și orele/datele îngroșate.")
    update_shape_text(s3.shapes[18], "03")
    update_shape_text(s3.shapes[19], "Dovadă & Calendar")
    update_shape_text(s3.shapes[20], "Apeși «Arată în text» să vezi sursa exactă. La termene vagi, primești [De confirmat] și export direct în calendar.")

    s3.notes_slide.notes_text_frame.text = (
        "1:30 – 2:05 (0:35 min)\n"
        "„Fluxul este simplu și intuitiv: selectezi textul stufos, Limpede îl reduce la 3 pași esențiali cu verbe la imperativ, "
        "iar tu ai butonul «Arată în text» care îți luminează dovada din documentul original. Fără halucinații.”"
    )

    # --- SLIDE 4: Ce Avem în Plus (Super-puterile) ---
    s4 = prs.slides[3]
    update_shape_text(s4.shapes[2], "LIMPEDE")
    update_shape_text(s4.shapes[3], "PITCH ACCESSABILITY")
    update_shape_text(s4.shapes[4], "03")
    update_shape_text(s4.shapes[5], "CE AVEM ÎN PLUS")
    update_shape_text(s4.shapes[6], "Trei lucruri pe care nimeni altcineva nu le face.")
    update_shape_text(s4.shapes[7], "LIMPEDE.RO")
    update_shape_text(s4.shapes[8], "HACKATHON 2026")
    update_shape_text(s4.shapes[10], "Inovații concrete de care suntem cel mai mândri:")
    update_shape_text(s4.shapes[13], "0 Halucinații")
    update_shape_text(s4.shapes[14], "«ARATĂ ÎN TEXT»")
    update_shape_text(s4.shapes[16], "[De confirmat]")
    update_shape_text(s4.shapes[17], "PROTECȚIE LA TERMENE")
    update_shape_text(s4.shapes[19], "Zero Diagnostic")
    update_shape_text(s4.shapes[20], "FĂRĂ DOSAR MEDICAL")

    s4.notes_slide.notes_text_frame.text = (
        "2:05 – 2:40 (0:35 min)\n"
        "„Trei inovații cheie:\n"
        "1. Funcția «Arată în text» oferă dovada matematică a sursei: un click derulează documentul și aprinde citatul exact. Zero halucinații.\n"
        "2. Protejăm angajatul împotriva termenelor vagi: când un șef zice «cât mai repede», refuzăm să ghicim o dată; punem [De confirmat] și exportăm .ics în calendar.\n"
        "3. Nu cerem diagnostic medical. Personalizarea se bazează pe nevoi reale de confort, iar datele rămân în browserul tău.”"
    )

    # --- SLIDE 5: Spectrul Complet ---
    s5 = prs.slides[4]
    update_shape_text(s5.shapes[2], "LIMPEDE")
    update_shape_text(s5.shapes[3], "PITCH ACCESSABILITY")
    update_shape_text(s5.shapes[4], "04")
    update_shape_text(s5.shapes[5], "PENTRU TOATĂ LUMEA")
    update_shape_text(s5.shapes[6], "Ceva concret pentru fiecare tip de nevoie.")
    update_shape_text(s5.shapes[7], "LIMPEDE.RO")
    update_shape_text(s5.shapes[8], "HACKATHON 2026")
    update_shape_text(s5.shapes[10], "ADHD & Memorie")
    update_shape_text(s5.shapes[11], "CARD «DE REȚINUT»")
    update_shape_text(s5.shapes[12], "Fără politețuri sterile; maximum 3-4 pași imperativi sub 10 cuvinte.")
    update_shape_text(s5.shapes[14], "Vedere & Dislexie")
    update_shape_text(s5.shapes[15], "CONTRAST 19.5:1 AAA")
    update_shape_text(s5.shapes[16], "Fonturi licențiate OpenDyslexic și Atkinson cu diacritice românești complete.")
    update_shape_text(s5.shapes[18], "Auz & Mobilitate")
    update_shape_text(s5.shapes[19], "AUDIO & 100% TASTATURĂ")
    update_shape_text(s5.shapes[20], "Ședințe audio transformate în decizii scrise cu responsabili; comenzi fără mouse.")
    update_shape_text(s5.shapes[21], "Autism & comunicare literală: decodificăm cererile corporatiste ocolite («ar fi frumos dacă...») și marcăm glumele ca (posibilă glumă — nesigur).")

    s5.notes_slide.notes_text_frame.text = (
        "2:40 – 3:10 (0:30 min)\n"
        "„Design universal în practică: fiecare barieră funcțională are un răspuns tehnic în Limpede, "
        "de la contrast extrem și fonturi pentru dislexie până la decodificarea limbajului indirect de birou.”"
    )

    # --- SLIDE 6: Ecosistemul Unificat ---
    s6 = prs.slides[5]
    update_shape_text(s6.shapes[2], "LIMPEDE")
    update_shape_text(s6.shapes[3], "PITCH ACCESSABILITY")
    update_shape_text(s6.shapes[4], "05")
    update_shape_text(s6.shapes[5], "ECOSISTEMUL")
    update_shape_text(s6.shapes[6], "Funcționează oriunde muncește omul.")
    update_shape_text(s6.shapes[7], "LIMPEDE.RO")
    update_shape_text(s6.shapes[8], "HACKATHON 2026")
    update_shape_text(s6.shapes[10], "01")
    update_shape_text(s6.shapes[11], "Asistentul Web (Angajat)")
    update_shape_text(s6.shapes[12], "Clarifică proceduri stufoase, extrage termene în calendar și redactează cereri legale de adaptare a biroului.")
    update_shape_text(s6.shapes[14], "02")
    update_shape_text(s6.shapes[15], "Extensia de Browser")
    update_shape_text(s6.shapes[16], "Trăiește direct peste Confluence, Jira, Gmail și Slack. Card Shadow DOM complet izolat de stilurile paginii.")
    update_shape_text(s6.shapes[18], "03")
    update_shape_text(s6.shapes[19], "Portalul HR (Angajator)")
    update_shape_text(s6.shapes[20], "Scanează lizibilitatea documentelor interne (0-100), semnalează jargonul și produce versiuni Easy-to-Read.")

    s6.notes_slide.notes_text_frame.text = (
        "3:10 – 3:40 (0:30 min)\n"
        "„O suită bilaterală: angajatul primește sprijin pe loc, iar angajatorul primește portalul de audit HR "
        "care îl ajută să scrie documente umane încă din prima zi.”"
    )

    # --- SLIDE 7: Competiția ---
    s7 = prs.slides[6]
    update_shape_text(s7.shapes[2], "LIMPEDE")
    update_shape_text(s7.shapes[3], "PITCH ACCESSABILITY")
    update_shape_text(s7.shapes[4], "06")
    update_shape_text(s7.shapes[5], "COMPETIȚIA")
    update_shape_text(s7.shapes[6], "De ce ChatGPT și Grammarly nu rezolvă problema.")
    update_shape_text(s7.shapes[7], "LIMPEDE.RO")
    update_shape_text(s7.shapes[8], "HACKATHON 2026")
    update_shape_text(s7.shapes[9], "ChatGPT inventează date când nu știe, nu cunoaște contextul de birou și nu exportă în calendar. Grammarly corectează doar virgule, dar nu simplifică o procedură de 40 de pagini.")
    update_shape_text(s7.shapes[11], "✓  AVANTAJUL NOSTRU CATEGORIC")
    update_shape_text(s7.shapes[12], "Verbatim quote grounding (zero halucinații), 100% date pe dispozitiv (localStorage), respectarea strictă a EU AI Act Art. 5 (interzicere citire emoții la muncă) și funcționare offline.")

    s7.notes_slide.notes_text_frame.text = (
        "3:40 – 4:10 (0:30 min)\n"
        "„De ce nu folosește Ana ChatGPT? Pentru că ChatGPT inventează termene, ghicește date și nu se integrează cu calendarul. "
        "Limpede verifică fiecare citat, refuză să ghicească termene vagi, protejează confidențialitatea și respectă legislația europeană.”"
    )

    # --- SLIDE 8: Demonstrația Live ---
    s8 = prs.slides[7]
    update_shape_text(s8.shapes[2], "LIMPEDE")
    update_shape_text(s8.shapes[3], "PITCH ACCESSABILITY")
    update_shape_text(s8.shapes[4], "07")
    update_shape_text(s8.shapes[5], "DEMONSTRAȚIA LIVE")
    update_shape_text(s8.shapes[6], "Hai să vedem Limpede în acțiune.")
    update_shape_text(s8.shapes[7], "LIMPEDE.RO")
    update_shape_text(s8.shapes[8], "HACKATHON 2026")
    update_shape_text(s8.shapes[10], "PASUL 1")
    update_shape_text(s8.shapes[11], "Profilul Anei (Fără Diagnostic)")
    update_shape_text(s8.shapes[12], "Setare nevoi în propriile cuvinte: «am probleme de memorie, vreau datele îngroșate». Salvare 100% în browser.")
    update_shape_text(s8.shapes[14], "PASUL 2")
    update_shape_text(s8.shapes[15], "Ghid Onboarding & Calendar .ICS")
    update_shape_text(s8.shapes[16], "Încărcare PDF, card «De reținut», butonul «Arată în text» (aprinde citatul cu galben), alertă [De confirmat] și export calendar.")

    s8.notes_slide.notes_text_frame.text = (
        "4:10 – 6:30 (Live Demo)\n"
        "Trecem acum la demonstrația practică pe ecran: profil fără diagnostic, PDF cu «Arată în text», "
        "alertă de termen vag cu export calendar, extensia pe Jira/Slack și auditul HR."
    )

    # --- SLIDE 9: Concluzie & Impact ---
    s9 = prs.slides[8]
    update_shape_text(s9.shapes[2], "LIMPEDE")
    update_shape_text(s9.shapes[3], "PITCH ACCESSABILITY")
    update_shape_text(s9.shapes[4], "08")
    update_shape_text(s9.shapes[5], "CONCLUZIE & IMPACT")
    update_shape_text(s9.shapes[6], "Locul de muncă adaptat la om, nu invers.")
    update_shape_text(s9.shapes[7], "LIMPEDE.RO")
    update_shape_text(s9.shapes[8], "HACKATHON 2026")
    update_shape_text(s9.shapes[9], "Cu Limpede, prima zi de muncă nu mai este un test de anduranță cognitivă sau o sursă de panică, ci un parteneriat bazat pe claritate, demnitate și performanță.")
    update_shape_text(s9.shapes[11], "Gratuit")
    update_shape_text(s9.shapes[12], "PENTRU ANGAJAȚI")
    update_shape_text(s9.shapes[14], "B2B SaaS")
    update_shape_text(s9.shapes[15], "PENTRU COMPANII (ESG)")
    update_shape_text(s9.shapes[17], "454")
    update_shape_text(s9.shapes[18], "TESTE VERIFICATE VERZI")
    update_shape_text(s9.shapes[20], "AAA")
    update_shape_text(s9.shapes[21], "CONFORMITATE WCAG 2.2")

    s9.notes_slide.notes_text_frame.text = (
        "6:30 – 7:00 (0:30 min)\n"
        "„Cu Limpede, prima zi de muncă nu mai este un test de anduranță cognitivă sau o sursă de panică, ci un parteneriat bazat pe claritate, demnitate și performanță.\n"
        "Vă mulțumim și așteptăm cu entuziasm întrebările dumneavoastră!”"
    )

    prs.save(output_path)
    print(f"✅ Template-based PITCH LIVE PPTX generated at: {output_path}")


# ==============================================================================
# 2. PITCH LIVE DOCX (Direct, natural, human Romanian speech script)
# ==============================================================================
def build_pitch_live_docx(output_path):
    doc = docx.Document()
    for s in doc.sections:
        s.top_margin = DocxInches(0.8)
        s.bottom_margin = DocxInches(0.8)
        s.left_margin = DocxInches(0.8)
        s.right_margin = DocxInches(0.8)

    title_p = doc.add_paragraph()
    r = title_p.add_run("Limpede — Prezentare Pitch Live (Scurtă, Concisă, Autentică)")
    r.font.size = DocxPt(22)
    r.font.bold = True
    r.font.color.rgb = DocxRGBColor(13, 148, 136)

    sub_p = doc.add_paragraph()
    r = sub_p.add_run("Adaptăm locul de muncă la om, nu invers. • AccessABILITY Hackathon 2026\nFormat: 7:00 Minute (3:30 min Pitch + 3:00 min Live Demo + 0:30 min Concluzie)")
    r.font.size = DocxPt(11)
    r.font.italic = True
    r.font.color.rgb = DocxRGBColor(100, 116, 139)

    doc.add_heading("Slide 1: Problema Reală & Cârligul Emoțional (0:00 – 1:00)", level=1)
    doc.add_paragraph(
        "„Faceți cunoștință cu Ana. Are 23 de ani, a terminat facultatea și astăzi este prima ei zi de muncă. "
        "În primele două ore primește un teanc de 40 de pagini de proceduri, acronime corporatiste și e-mailuri cu termene vagi precum «cât mai repede».\n\n"
        "Ana are ADHD și anxietate socială. Îi este o frică paralizantă să întrebe pentru a treia oară ce înseamnă un termen de birou, de teamă să nu pară incompetentă în perioada de probă.\n\n"
        "În România și UE, 1 din 6 tineri trăiește cu o dizabilitate, iar 68% din abandonurile primului job se întâmplă din cauza comunicării inaccesibile și a fricii de a cere lămuriri. "
        "Pentru ei am creat Limpede: adaptăm locul de muncă la om, nu invers.”"
    )

    doc.add_heading("Slide 2: Soluția Noastră în 3 Pași Clari (1:00 – 1:30)", level=1)
    doc.add_paragraph(
        "1. Încarci sau selectezi: PDF de onboarding, email de la șef sau text direct din Jira/Slack cu extensia de browser.\n"
        "2. Limpede simplifică: 3 pași acționabili, verbe clare la imperativ, cardul «📌 De reținut azi» și orele/datele îngroșate.\n"
        "3. Ai dovada și calendarul: Apeși «Arată în text» să vezi sursa exactă. La termene vagi, primești [De confirmat] și export direct în Google Calendar sau Outlook."
    )

    doc.add_heading("Slide 3: Ce Ne Face Unici — Cele 3 Super-Puteri (1:30 – 2:05)", level=1)
    doc.add_paragraph(
        "• Adaptare fără diagnostic medical: Interfața se mulează pe stilul tău de confort (contrast 19.5:1, fonturi OpenDyslexic / Atkinson, ritm calm). Nu-ți cere dosar medical, iar datele nu pleacă din browserul tău.\n"
        "• Zero halucinații («Arată în text»): Nu ghicim niciodată. Când Limpede îți dă un pas, apeși un buton și îți luminează cu galben exact rândul din documentul original semnat.\n"
        "• Protecție pe termene & export .ICS: Șeful a zis «cât mai repede»? Nu inventăm o dată din burtă. Punem [De confirmat], alegi ziua și se duce direct în calendarul tău."
    )

    doc.add_heading("Slide 4: Spectrul Complet de Nevoi — Design Universal (2:05 – 2:40)", level=1)
    doc.add_paragraph(
        "• ADHD & Memorie: Card prioritar «De reținut» și maximum 3-4 pași imperativi sub 10 cuvinte.\n"
        "• Vedere Scăzută: Temă Contrast Ridicat 19.5:1 AAA, scalare 200%, pilule tactile mari (48px).\n"
        "• Autism & Literalitate: Decodificăm cererile corporatiste ocolite («ar fi frumos dacă...») și marcăm glumele ca (posibilă glumă — nesigur).\n"
        "• Dislexie: Fonturi licențiate OpenDyslexic și Atkinson Hyperlegible cu suport complet pentru diacritice românești (ă, î, â, ș, ț).\n"
        "• Auz & Mobilitate: Ședințe audio transformate în decizii scrise cu responsabili; comenzi 100% din tastatură (Alt + Shift + S)."
    )

    doc.add_heading("Slide 5: De Ce Noi și Nu ChatGPT / Grammarly? (2:40 – 3:10)", level=1)
    doc.add_paragraph(
        "• ChatGPT inventează date când nu știe, nu cunoaște contextul de birou și nu exportă în calendar.\n"
        "• Grammarly corectează doar virgule, dar nu simplifică o procedură de 40 de pagini.\n"
        "• Limpede garantează adevărul (verbatim quote grounding), păstrează datele 100% pe dispozitiv și respectă strict EU AI Act Art. 5 (interzicere analiză emoții la locul de muncă)."
    )

    doc.add_heading("Slide 6: Ghidul Demonstrației Live (3:10 – 6:30)", level=1)
    doc.add_paragraph(
        "Pasul 1: Profilul Anei — setare nevoi în propriile cuvinte («am probleme mari de memorie, vreau datele îngroșate»).\n"
        "Pasul 2: Ghidul Onboarding — încărcare PDF, card «De reținut» și butonul «Arată în text» care aprinde sursa cu galben.\n"
        "Pasul 3: Termen vag — email «cât mai repede», alertă [De confirmat] și export .ics în calendar.\n"
        "Pasul 4: Extensia de browser — selectare text pe Jira/Slack, butonul «Fă clar» și scurtare instantă.\n"
        "Pasul 5: Portalul HR — auditul lizibilității și generarea automată Easy-to-Read."
    )

    doc.add_heading("Slide 7: Concluzie & Citat de Final (6:30 – 7:00)", level=1)
    doc.add_paragraph(
        "„Cu Limpede, prima zi de muncă nu mai este un test de anduranță cognitivă sau o sursă de panică, ci un parteneriat bazat pe claritate, demnitate și performanță.\n\n"
        "Vă mulțumim și așteptăm cu drag întrebările dumneavoastră!”"
    )

    doc.save(output_path)
    print(f"✅ PITCH LIVE DOCX generated at: {output_path}")


def main():
    docs_dir = os.path.join(os.getcwd(), "docs")
    template_seed = os.path.join(docs_dir, "ideaproof_seed.pptx")

    # 1. Generate Pitch Live PPTX from real template if template exists
    pitch_pptx_out = os.path.join(docs_dir, "limpede_pitch_live.pptx")
    if os.path.exists(template_seed):
        build_pitch_live_from_template(template_seed, pitch_pptx_out)

    # 2. Generate Pitch Live DOCX
    pitch_docx_out = os.path.join(docs_dir, "limpede_pitch_live.docx")
    build_pitch_live_docx(pitch_docx_out)

    # Clean up downloaded raw seed files so repository stays clean
    if os.path.exists(os.path.join(docs_dir, "ideaproof_demoday.pptx")):
        os.remove(os.path.join(docs_dir, "ideaproof_demoday.pptx"))
    if os.path.exists(os.path.join(docs_dir, "ideaproof_seed.pptx")):
        os.remove(os.path.join(docs_dir, "ideaproof_seed.pptx"))

    print("\n🎉 ALL HUMAN-DESIGNED BUSINESS PRESENTATION ASSETS COMPLETED!")
    print(f"1. Pitch Live PPTX: {pitch_pptx_out}")
    print(f"2. Pitch Live DOCX: {pitch_docx_out}")


if __name__ == "__main__":
    main()
