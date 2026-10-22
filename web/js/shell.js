/**
 * shell.js - Accessible App Shell Interactive Behavior
 * Project: PrimaZi (AccessABILITY Hackathon 2026)
 * Owner: p3
 *
 * Handles:
 * - Desktop sidebar collapse/expand with persistence to wp.prefs.v1
 * - Mobile drawer toggle (<768px) with backdrop, Escape key, and focus return
 */

const STORAGE_KEY = "wp.prefs.v1";

function readPrefs() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { version: 1, prefs: { sidebar: "open" } };
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" ? parsed : { version: 1, prefs: { sidebar: "open" } };
  } catch (err) {
    return { version: 1, prefs: { sidebar: "open" } };
  }
}

function updateSidebarPref(newState) {
  try {
    const state = readPrefs();
    if (!state.prefs) state.prefs = {};
    state.prefs.sidebar = newState;
    state.updatedAt = new Date().toISOString();
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch (err) {
    // Ignore storage errors in private mode
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const root = document.documentElement;
  const menuToggle = document.getElementById("btn-menu-toggle");
  const sidebarCollapse = document.getElementById("btn-sidebar-collapse");
  const sidebar = document.getElementById("app-sidebar");
  const backdrop = document.getElementById("sidebar-backdrop");
  const liveRegion = document.getElementById("status-live");

  function announce(msg) {
    if (liveRegion) {
      liveRegion.textContent = "";
      setTimeout(() => { liveRegion.textContent = msg; }, 50);
    }
  }

  // 1. Mobile Drawer Toggle (<768px)
  function openDrawer() {
    if (!sidebar) return;
    sidebar.classList.add("is-drawer-open");
    if (backdrop) backdrop.classList.add("is-active");
    if (menuToggle) {
      menuToggle.setAttribute("aria-expanded", "true");
    }
    const firstFocusable = sidebar.querySelector("a, button");
    if (firstFocusable) firstFocusable.focus();
    announce("Meniul de navigare a fost deschis.");
  }

  function closeDrawer() {
    if (!sidebar) return;
    sidebar.classList.remove("is-drawer-open");
    if (backdrop) backdrop.classList.remove("is-active");
    if (menuToggle) {
      menuToggle.setAttribute("aria-expanded", "false");
      menuToggle.focus();
    }
    announce("Meniul de navigare a fost închis.");
  }

  if (menuToggle) {
    menuToggle.addEventListener("click", () => {
      const isOpen = sidebar && sidebar.classList.contains("is-drawer-open");
      if (isOpen) {
        closeDrawer();
      } else {
        openDrawer();
      }
    });
  }

  if (backdrop) {
    backdrop.addEventListener("click", closeDrawer);
  }

  // Close drawer on Escape key
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      if (sidebar && sidebar.classList.contains("is-drawer-open")) {
        closeDrawer();
      }
    }
  });

  // 2. Desktop Sidebar Collapse Toggle
  if (sidebarCollapse) {
    sidebarCollapse.addEventListener("click", () => {
      const isCurrentlyCollapsed = root.getAttribute("data-sidebar") === "collapsed";
      const nextState = isCurrentlyCollapsed ? "open" : "collapsed";
      root.setAttribute("data-sidebar", nextState);
      sidebarCollapse.setAttribute("aria-expanded", nextState === "open" ? "true" : "false");
      updateSidebarPref(nextState);
      announce(nextState === "collapsed" ? "Bara laterală a fost restrânsă." : "Bara laterală a fost extinsă.");
    });
  }
});
