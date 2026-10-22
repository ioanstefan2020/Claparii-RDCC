/**
 * popup.js - Quick Extension Controls
 */

document.addEventListener("DOMContentLoaded", async () => {
  let activeHostname = "";

  // 1. Get active tab's hostname
  try {
    const [tab] = await chrome.tabs.query({
      active: true,
      currentWindow: true,
    });
    if (tab?.url) {
      const url = new URL(tab.url);
      activeHostname = url.hostname;
      const hostLabel = document.getElementById("activeHost");
      if (hostLabel) hostLabel.textContent = activeHostname || "Pagină locală";
    }
  } catch (_) {}

  // 2. Fetch current config & prefs directly from chrome.storage.local
  try {
    const stored = await chrome.storage.local.get([
      "wp.ext.config",
      "wp.ext.prefs.v1",
    ]);
    const config = stored["wp.ext.config"] || { disabledSites: [] };
    const prefs = stored["wp.ext.prefs.v1"] || { prefs: { reading_level: 2 } };

    const siteEnabledCheckbox = document.getElementById("siteEnabledCheckbox");
    const readingLevelSelect = document.getElementById("readingLevelSelect");
    const localOnlyCheckbox = document.getElementById("localOnlyCheckbox");

    // Check if site is disabled
    const disabledSites = config.disabledSites || [];
    if (siteEnabledCheckbox) {
      siteEnabledCheckbox.checked = !disabledSites.includes(activeHostname);
      siteEnabledCheckbox.addEventListener("change", async () => {
        let updatedDisabled = [...disabledSites];
        if (siteEnabledCheckbox.checked) {
          updatedDisabled = updatedDisabled.filter((h) => h !== activeHostname);
        } else {
          if (!updatedDisabled.includes(activeHostname)) {
            updatedDisabled.push(activeHostname);
          }
        }
        const updatedConfig = { ...config, disabledSites: updatedDisabled };
        await chrome.storage.local.set({ "wp.ext.config": updatedConfig });
      });
    }

    // Reading level
    if (readingLevelSelect) {
      const currentLvl = prefs.prefs?.reading_level || 2;
      readingLevelSelect.value = String(currentLvl);
      readingLevelSelect.addEventListener("change", async () => {
        const newLvl = Number(readingLevelSelect.value);
        const updatedPrefs = {
          ...prefs,
          updatedAt: new Date().toISOString(),
          prefs: {
            ...(prefs.prefs || {}),
            reading_level: newLvl,
          },
        };
        await chrome.storage.local.set({ "wp.ext.prefs.v1": updatedPrefs });
      });
    }

    // Local only
    if (localOnlyCheckbox) {
      localOnlyCheckbox.checked = !!config.localOnly;
      localOnlyCheckbox.addEventListener("change", async () => {
        const updatedConfig = {
          ...config,
          localOnly: localOnlyCheckbox.checked,
        };
        await chrome.storage.local.set({ "wp.ext.config": updatedConfig });
      });
    }
  } catch (err) {
    console.error("Popup storage error:", err);
  }

  // Open settings
  const openSettingsBtn = document.getElementById("openSettingsBtn");
  if (openSettingsBtn) {
    openSettingsBtn.addEventListener("click", () => {
      chrome.runtime.openOptionsPage();
    });
  }
});
