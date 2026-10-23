"""Tests for Romanian Voiceover Core, Voice Engine, and Blind Mode (Ecran Negru).
Validates:
- Role mapping into natural Romanian
- Accessible label precedence
- State announcement formatting (bifat, extins)
- Voice quality preference scoring
- Curtain styles and F9 toggle behavior
"""

import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
VOICEOVER_CORE_JS = ROOT / "web" / "a11y" / "voiceover-core.js"
BLIND_MODE_JS = ROOT / "web" / "a11y" / "blind-mode.js"
SHELL_CSS = ROOT / "web" / "css" / "shell.css"


def run_node_code(code: str) -> str:
    proc = subprocess.run(
        ["node", "--input-type=module", "-e", code],
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.strip()


def test_element_roles_ro():
    """Verify HTML and ARIA roles map to proper Romanian labels."""
    script = f"""
    import {{ getElementRoleRo }} from '{VOICEOVER_CORE_JS.as_uri()}';

    const btn = {{ tagName: 'BUTTON', getAttribute: () => null }};
    const link = {{ tagName: 'A', hasAttribute: (a) => a === 'href', getAttribute: () => null }};
    const chk = {{ tagName: 'INPUT', getAttribute: (a) => a === 'type' ? 'checkbox' : null }};
    const txt = {{ tagName: 'INPUT', getAttribute: (a) => a === 'type' ? 'text' : null }};
    const h2 = {{ tagName: 'H2', getAttribute: () => null }};

    const out = {{
        btn: getElementRoleRo(btn),
        link: getElementRoleRo(link),
        chk: getElementRoleRo(chk),
        txt: getElementRoleRo(txt),
        h2: getElementRoleRo(h2)
    }};
    console.log(JSON.stringify(out));
    """
    res = json.loads(run_node_code(script))
    assert res["btn"]["role"] == "Buton"
    assert res["link"]["role"] == "Link"
    assert res["chk"]["role"] == "Bifă"
    assert res["txt"]["role"] == "Casetă de text"
    assert res["h2"]["role"] == "Antet"
    assert res["h2"]["level"] == 2


def test_accessible_label_resolution():
    """Verify accessible label precedence (aria-label vs textContent)."""
    script = f"""
    import {{ getAccessibleLabel }} from '{VOICEOVER_CORE_JS.as_uri()}';

    const elAria = {{
        tagName: 'BUTTON',
        getAttribute: (a) => a === 'aria-label' ? 'Salvează modificările' : null,
        innerText: 'OK'
    }};
    const elText = {{
        tagName: 'BUTTON',
        getAttribute: () => null,
        innerText: 'Anulează'
    }};

    const out = {{
        aria: getAccessibleLabel(elAria),
        text: getAccessibleLabel(elText)
    }};
    console.log(JSON.stringify(out));
    """
    res = json.loads(run_node_code(script))
    assert res["aria"] == "Salvează modificările"
    assert res["text"] == "Anulează"


def test_element_state_ro():
    """Verify interactive state resolution in Romanian (bifat, extins)."""
    script = f"""
    import {{ getElementStateRo }} from '{VOICEOVER_CORE_JS.as_uri()}';

    const chkChecked = {{
        checked: true,
        getAttribute: (a) => a === 'type' ? 'checkbox' : null
    }};
    const chkUnchecked = {{
        checked: false,
        getAttribute: (a) => a === 'type' ? 'checkbox' : null
    }};
    const expanded = {{
        getAttribute: (a) => a === 'aria-expanded' ? 'true' : null
    }};

    const out = {{
        checked: getElementStateRo(chkChecked),
        unchecked: getElementStateRo(chkUnchecked),
        expanded: getElementStateRo(expanded)
    }};
    console.log(JSON.stringify(out));
    """
    res = json.loads(run_node_code(script))
    assert "bifat" in res["checked"]
    assert "nebifat" in res["unchecked"]
    assert "extins" in res["expanded"]


def test_format_element_announcement_ro():
    """Verify complete announcement formatting in Romanian."""
    script = f"""
    import {{ formatElementAnnouncementRo }} from '{VOICEOVER_CORE_JS.as_uri()}';

    const btn = {{
        tagName: 'BUTTON',
        getAttribute: () => null,
        innerText: 'Clarifică documentul'
    }};
    const chk = {{
        tagName: 'INPUT',
        checked: true,
        getAttribute: (a) => {{
            if (a === 'type') return 'checkbox';
            if (a === 'aria-label') return 'Instrucțiuni scrise';
            return null;
        }}
    }};

    const out = {{
        btn: formatElementAnnouncementRo(btn),
        chk: formatElementAnnouncementRo(chk)
    }};
    console.log(JSON.stringify(out));
    """
    res = json.loads(run_node_code(script))
    assert res["btn"] == "Buton: Clarifică documentul"
    assert "Bifă: Instrucțiuni scrise: bifat" in res["chk"]


def test_voice_scoring():
    """Verify Romanian voices are prioritized over non-Romanian voices."""
    script = f"""
    import {{ scoreVoice }} from '{VOICEOVER_CORE_JS.as_uri()}';

    const naturalRo = {{ lang: 'ro-RO', name: 'Microsoft Alina Natural' }};
    const standardRo = {{ lang: 'ro-RO', name: 'Romanian Standard' }};
    const enVoice = {{ lang: 'en-US', name: 'English David', default: false }};

    const out = {{
        natural: scoreVoice(naturalRo),
        standard: scoreVoice(standardRo),
        en: scoreVoice(enVoice)
    }};
    console.log(JSON.stringify(out));
    """
    res = json.loads(run_node_code(script))
    assert res["natural"] == 100
    assert res["standard"] == 80
    assert res["en"] == 0
    assert res["natural"] > res["standard"] > res["en"]


def test_blind_curtain_css_properties():
    """Verify that #blind-curtain CSS defines pitch-black overlay and correct z-index."""
    css_content = SHELL_CSS.read_text(encoding="utf-8")
    tokens_content = (ROOT / "web" / "css" / "tokens.css").read_text(encoding="utf-8")
    assert ".blind-curtain" in css_content
    assert "var(--blind-curtain-bg)" in css_content
    assert "--blind-curtain-bg: #000000;" in tokens_content
    assert "2147483647" in css_content
    assert "pointer-events: none" in css_content


def test_blind_mode_js_structure():
    """Verify blind-mode.js contains F9 handler, toggle function, and storage key."""
    js_content = BLIND_MODE_JS.read_text(encoding="utf-8")
    assert "F9" in js_content
    assert "toggleBlindMode" in js_content
    assert "isBlindModeActive" in js_content
    assert "limpede_blind_mode" in js_content
    assert "Modul ecran negru activat" in js_content
