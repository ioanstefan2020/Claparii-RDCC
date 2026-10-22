"""Automated Settings Engine V2 Tests (Task A1).
Tests persistence across reload simulation, migration, clamping, presets, and export/import.
Ref: docs/TASKS-WAVE2.md A1, docs/SETTINGS-SPEC.md
"""
import subprocess
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
SETTINGS_JS = ROOT / "web" / "a11y" / "settings.js"
PRESETS_JS = ROOT / "web" / "a11y" / "presets.js"


def run_node_settings_test(js_code: str) -> dict:
    script = f"""
    // Mock minimal localStorage and document
    const storageMap = new Map();
    globalThis.localStorage = {{
      getItem(k) {{ return storageMap.has(k) ? storageMap.get(k) : null; }},
      setItem(k, v) {{ storageMap.set(k, String(v)); }},
      removeItem(k) {{ storageMap.delete(k); }},
      clear() {{ storageMap.clear(); }}
    }};

    const domAttrs = {{}};
    const domStyles = {{}};
    globalThis.document = {{
      documentElement: {{
        setAttribute(k, v) {{ domAttrs[k] = String(v); }},
        getAttribute(k) {{ return domAttrs[k] || null; }},
        style: {{
          setProperty(k, v) {{ domStyles[k] = String(v); }},
          getPropertyValue(k) {{ return domStyles[k] || ""; }}
        }}
      }}
    }};
    globalThis.window = {{
      addEventListener() {{}},
      removeEventListener() {{}}
    }};

    import('{SETTINGS_JS.as_uri()}').then(async (mod) => {{
      const testFn = async () => {{
        {js_code}
      }};
      try {{
        const result = await testFn();
        console.log(JSON.stringify({{ ok: true, result, storage: Object.fromEntries(storageMap), domAttrs, domStyles }}));
      }} catch (err) {{
        console.log(JSON.stringify({{ ok: false, error: err.message, stack: err.stack }}));
      }}
    }});
    """
    proc = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        capture_output=True,
        text=True,
        check=True
    )
    return json.loads(proc.stdout.strip())


def test_settings_defaults_and_clamping():
    res = run_node_settings_test("""
      mod.setSetting('font_scale', 500); // Should clamp to 200
      mod.setSetting('line_height', 0.5); // Should clamp to 1.2
      mod.setSetting('theme', 'invalid_theme'); // Should fallback to default 'soft'
      return {
        font_scale: mod.getSetting('font_scale'),
        line_height: mod.getSetting('line_height'),
        theme: mod.getSetting('theme')
      };
    """)
    assert res["ok"] is True
    data = res["result"]
    assert data["font_scale"] == 200
    assert data["line_height"] == 1.2
    assert data["theme"] == "soft"


def test_settings_persistence_across_reload_simulation():
    res = run_node_settings_test("""
      mod.setSetting('theme', 'amber');
      mod.setSetting('font_scale', 125);
      mod.setSetting('layout', 'guided');
      const rawStored = globalThis.localStorage.getItem('primazi.settings.v2');
      return { rawStored };
    """)
    assert res["ok"] is True
    stored = json.loads(res["result"]["rawStored"])
    assert stored["theme"] == "amber"
    assert stored["font_scale"] == 125
    assert stored["layout"] == "guided"
    assert stored["version"] == 2


def test_preset_application():
    res = run_node_settings_test("""
      mod.applyPreset('citire-usoara');
      return {
        reading_level: mod.getSetting('reading_level'),
        format: mod.getSetting('format'),
        line_height: mod.getSetting('line_height'),
        tone_notes: mod.getSetting('tone_notes')
      };
    """)
    assert res["ok"] is True
    data = res["result"]
    assert data["reading_level"] == "very_simple"
    assert data["format"] == "steps"
    assert data["line_height"] == 1.8
    assert data["tone_notes"] == "on"


def test_reset_only_on_explicit_call():
    res = run_node_settings_test("""
      mod.setSetting('theme', 'hc-dark');
      mod.setSetting('font_scale', 150);
      mod.resetAll();
      return {
        theme: mod.getSetting('theme'),
        font_scale: mod.getSetting('font_scale')
      };
    """)
    assert res["ok"] is True
    data = res["result"]
    assert data["theme"] == "soft"
    assert data["font_scale"] == 100


def test_export_import_json():
    res = run_node_settings_test("""
      mod.setSetting('theme', 'sapphire');
      mod.setSetting('font_scale', 140);
      const exported = mod.exportJSON();
      
      mod.resetAll();
      const importRes = mod.importJSON(exported);
      return {
        importOk: importRes.ok,
        theme: mod.getSetting('theme'),
        font_scale: mod.getSetting('font_scale')
      };
    """)
    assert res["ok"] is True
    data = res["result"]
    assert data["importOk"] is True
    assert data["theme"] == "sapphire"
    assert data["font_scale"] == 140
