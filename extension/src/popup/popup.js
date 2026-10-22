/**
 * popup.js - Quick Extension Controls
 */

document.addEventListener("DOMContentLoaded", async () => {
  let activeHostname = "";

  // 1. Get active tab's hostname
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab?.url) {
      const url = new URL(tab.url);
      activeHostname = url.hostname;
      const hostLabel = document.getElementById("activeHost");
      if (hostLabel) hostLabel.textContent = activeHostname || "Pagină locală";
    }
  } catch (_) {}

  // 2. Fetch current config & prefs
  chrome.runtime.sendMessage({ type: "PREFS_GET" }, (res) => {
    if (!res) return;
    const config = res.config || {};
    const prefs = res.prefs || {};

    const siteEnabledCheckbox = document.getElementById("siteEnabledCheckbox");
    const readingLevelSelect = document.getElementById("readingLevelSelect");
    const localOnlyCheckbox = document.getElementById("localOnlyCheckbox");

    // Check if site is disabled
    const disabledSites = config.disabledSites || [];
    if (siteEnabledCheckbox) {
      siteEnabledCheckbox.checked = !disabledSites.includes(activeHostname);
      siteEnabledCheckbox.addEventListener("change", () => {
        let updatedDisabled = [...disabledSites];
        if (siteEnabledCheckbox.checked) {
          updatedDisabled = updatedDisabled.filter(h => h !== activeHostname);
        } else {
          if (!updatedDisabled.includes(activeHostname)) {
            updatedDisabled.push(activeHostname);
          }
        }
        chrome.runtime.sendMessage({
          type: "CONFIG_SET",
          config: { disabledSites: updatedDisabled }
        });
      });
    }

    // Reading level
    if (readingLevelSelect) {
      const currentLvl = prefs.prefs?.reading_level || 2;
      readingLevelSelect.value = String(currentLvl);
      readingLevelSelect.addEventListener("change", () => {
        const newLvl = Number(readingLevelSelect.value);
        const updatedPrefs = {
          ...prefs,
          prefs: {
            ...(prefs.prefs || {}),
            reading_level: newLvl
          }
        };
        chrome.runtime.sendMessage({
          type: "PREFS_SET",
          prefs: updatedPrefs
        });
      });
    }

    // Local only
    if (localOnlyCheckbox) {
      localOnlyCheckbox.checked = !!config.localOnly;
      localOnlyCheckbox.addEventListener("change", () => {
        chrome.runtime.sendMessage({
          type: "CONFIG_SET",
          config: { localOnly: localOnlyCheckbox.checked }
        });
      });
    }
  });

  // Open settings
  const openSettingsBtn = document.getElementById("openSettingsBtn");
  if (openSettingsBtn) {
    openSettingsBtn.addEventListener("click", () => {
      chrome.runtime.openOptionsPage();
    });
  }
});
