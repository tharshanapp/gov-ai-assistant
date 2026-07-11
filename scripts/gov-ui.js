(function () {
  const APP_TITLE = "__APP_TITLE__";
  const ROOT = window.parent && window.parent.document ? window.parent : window;
  const DOC = ROOT.document;
  const WIN = ROOT;
  const SIDEBAR_KEY = "gov-sidebar-state";

  if (WIN.__govKnowledgeUiBooted) return;
  WIN.__govKnowledgeUiBooted = true;

  function appUrl() {
    return WIN.location.href;
  }

  function labelOf(el) {
    return (
      (el.getAttribute("aria-label") || "") + " " +
      (el.getAttribute("title") || "") + " " +
      (el.getAttribute("data-testid") || "") + " " +
      (el.textContent || "")
    ).toLowerCase();
  }

  function isBlockedHref(href) {
    if (!href) return false;
    const h = href.toLowerCase();
    return (
      h.includes("github.com") || h.includes("github.dev") ||
      h.includes("streamlit.io") || h.includes("streamlit.com") ||
      h.includes("share.streamlit")
    );
  }

  function isGovControl(el) {
    if (!el) return false;
    return !!(el.closest("#gov-top-actions") || el.closest("#gov-share-modal") || el.id === "gov-sidebar-toggle");
  }

  function hideBlocked(el) {
    if (!el || isGovControl(el) || el.dataset.govHidden === "1") return;
    const href = el.href || el.getAttribute("href") || "";
    const label = labelOf(el);
    const tid = el.getAttribute("data-testid") || "";
    const blocked =
      isBlockedHref(href) ||
      label.includes("github") || label.includes("fork") ||
      label.includes("view source") || label.includes("edit app") ||
      label.includes("streamlit") ||
      (label.includes("star") && !el.closest("#gov-top-actions")) ||
      (label.includes("menu") && tid.includes("Toolbar")) ||
      (el.className || "").toLowerCase().includes("viewerbadge") ||
      el.id === "GithubIcon" ||
      tid === "baseButton-header";
    if (blocked) {
      el.dataset.govHidden = "1";
      el.style.setProperty("display", "none", "important");
      el.style.setProperty("visibility", "hidden", "important");
      el.style.setProperty("pointer-events", "none", "important");
    }
  }

  function hideNativeSidebarControls() {
    DOC.querySelectorAll(
      '[data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"], [data-testid="stSidebarCollapseButton"]'
    ).forEach((el) => {
      if (el.dataset.govSidebarHidden === "1") return;
      el.dataset.govSidebarHidden = "1";
      el.style.setProperty("display", "none", "important");
      el.style.setProperty("visibility", "hidden", "important");
      el.style.setProperty("opacity", "0", "important");
      el.style.setProperty("pointer-events", "none", "important");
    });
  }

  function isSidebarCollapsed() {
    if (DOC.documentElement.classList.contains("gov-sidebar-hidden")) return true;
    if (DOC.documentElement.classList.contains("gov-sidebar-force-show")) return false;

    const sidebar = DOC.querySelector('section[data-testid="stSidebar"]');
    if (sidebar) {
      if (sidebar.getAttribute("aria-expanded") === "false") return true;
      const rect = sidebar.getBoundingClientRect();
      if (rect.width < 24) return true;
    }
    return false;
  }

  function saveSidebarState(open) {
    try {
      WIN.sessionStorage.setItem(SIDEBAR_KEY, open ? "open" : "closed");
    } catch (e) {}
  }

  function showSidebar() {
    DOC.documentElement.classList.remove("gov-sidebar-hidden");
    DOC.documentElement.classList.add("gov-sidebar-force-show");
    saveSidebarState(true);
    tryNativeToggle(true);
  }

  function hideSidebar() {
    DOC.documentElement.classList.remove("gov-sidebar-force-show");
    DOC.documentElement.classList.add("gov-sidebar-hidden");
    saveSidebarState(false);
    tryNativeToggle(false);
  }

  function forceNativeClick(el) {
    const target = el && el.tagName === "BUTTON" ? el : (el && el.querySelector("button")) || el;
    if (!target) return false;
    const opts = { bubbles: true, cancelable: true, view: WIN };
    try { target.focus(); } catch (e) {}
    target.dispatchEvent(new PointerEvent("pointerdown", opts));
    target.dispatchEvent(new MouseEvent("mousedown", opts));
    target.dispatchEvent(new PointerEvent("pointerup", opts));
    target.dispatchEvent(new MouseEvent("mouseup", opts));
    target.dispatchEvent(new MouseEvent("click", opts));
    return true;
  }

  function tryNativeToggle(wantOpen) {
    const expandSelectors = [
      '[data-testid="stSidebarCollapsedControl"] button',
      '[data-testid="stSidebarCollapsedControl"]',
      '[data-testid="collapsedControl"] button',
      '[data-testid="collapsedControl"]',
      'button[aria-label*="Open sidebar" i]',
      'button[aria-label*="Expand sidebar" i]',
    ];
    const collapseSelectors = [
      '[data-testid="stSidebarCollapseButton"]',
      'section[data-testid="stSidebar"] button[kind="header"]',
      'button[aria-label*="Close sidebar" i]',
      'button[aria-label*="Collapse sidebar" i]',
    ];
    const selectors = wantOpen ? expandSelectors : collapseSelectors;
    for (const sel of selectors) {
      const el = DOC.querySelector(sel);
      if (el && forceNativeClick(el)) return true;
    }
    return false;
  }

  function applySavedSidebarState() {
    try {
      const saved = WIN.sessionStorage.getItem(SIDEBAR_KEY);
      if (saved === "open") {
        DOC.documentElement.classList.remove("gov-sidebar-hidden");
        DOC.documentElement.classList.add("gov-sidebar-force-show");
      } else if (saved === "closed") {
        DOC.documentElement.classList.remove("gov-sidebar-force-show");
        DOC.documentElement.classList.add("gov-sidebar-hidden");
      }
    } catch (e) {}
  }

  function restoreSidebarState() {
    applySavedSidebarState();
  }

  function updateSidebarToggle() {
    const btn = DOC.getElementById("gov-sidebar-toggle");
    if (!btn) return;
    const collapsed = isSidebarCollapsed();
    btn.textContent = collapsed ? ">>" : "<<";
    btn.title = collapsed ? "Show sidebar" : "Hide sidebar";
    btn.setAttribute("aria-label", collapsed ? "Show sidebar" : "Hide sidebar");
    if (collapsed) {
      btn.style.left = "0";
    } else {
      const sidebar = DOC.querySelector('section[data-testid="stSidebar"]');
      const left = sidebar ? Math.max(sidebar.getBoundingClientRect().right - 15, 0) : 0;
      btn.style.left = left + "px";
    }
  }

  function toggleSidebar() {
    if (isSidebarCollapsed()) showSidebar();
    else hideSidebar();
    setTimeout(updateSidebarToggle, 80);
    setTimeout(updateSidebarToggle, 350);
  }

  function ensureSidebarToggle() {
    let btn = DOC.getElementById("gov-sidebar-toggle");
    if (!btn) {
      btn = DOC.createElement("button");
      btn.id = "gov-sidebar-toggle";
      btn.type = "button";
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        toggleSidebar();
      });
      DOC.body.appendChild(btn);
      restoreSidebarState();
    }
    applySavedSidebarState();
    hideNativeSidebarControls();
    updateSidebarToggle();
  }

  function scrub() {
    DOC.querySelectorAll(
      '[data-testid="stToolbar"], [data-testid="stToolbarActions"], #MainMenu, [class*="viewerBadge"], #GithubIcon, [class*="Profile"], [class*="profile"], [data-testid="stHeaderActionElements"]'
    ).forEach((el) => {
      if (el.dataset.govToolbarHidden === "1") return;
      el.dataset.govToolbarHidden = "1";
      el.style.setProperty("display", "none", "important");
      el.style.setProperty("visibility", "hidden", "important");
      el.style.setProperty("pointer-events", "none", "important");
    });
    hideNativeSidebarControls();
    DOC.querySelectorAll("a, button").forEach(hideBlocked);
  }

  function blockClicks() {
    if (DOC.__govBlockClicks) return;
    DOC.__govBlockClicks = true;
    DOC.addEventListener("click", (e) => {
      const a = e.target.closest("a");
      if (a && isBlockedHref(a.href) && !isGovControl(a)) {
        e.preventDefault();
        e.stopPropagation();
      }
    }, true);
  }

  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text);
    }
    const ta = DOC.createElement("textarea");
    ta.value = text;
    DOC.body.appendChild(ta);
    ta.select();
    DOC.execCommand("copy");
    DOC.body.removeChild(ta);
    return Promise.resolve();
  }

  function injectStyles() {
    if (DOC.getElementById("gov-ui-styles")) return;
    const style = DOC.createElement("style");
    style.id = "gov-ui-styles";
    style.textContent = `
      #gov-top-actions{position:fixed;top:0.5rem;right:0.6rem;z-index:999992}
      #gov-share-open{font-family:Source Sans 3,sans-serif;font-size:0.82rem;font-weight:700;
      padding:0.42rem 1rem;border-radius:999px;border:1.5px solid #C9A227;cursor:pointer;
      background:linear-gradient(135deg,#1A2B4A,#2C4A7C);color:#fff;box-shadow:0 2px 12px rgba(26,43,74,.18)}
      #gov-sidebar-toggle{position:fixed;top:50%;transform:translateY(-50%);left:0;z-index:999995;
      font-family:Source Sans 3,sans-serif;font-size:0.95rem;font-weight:700;width:30px;height:52px;
      padding:0;border:1px solid #D4DCE8;border-radius:0 8px 8px 0;cursor:pointer;
      background:linear-gradient(135deg,#1A2B4A,#2C4A7C);color:#fff;
      box-shadow:2px 0 12px rgba(26,43,74,.18);transition:left .2s ease;line-height:1}
      #gov-sidebar-toggle:hover{background:#2C4A7C;border-color:#C9A227}
      html.gov-sidebar-hidden section[data-testid="stSidebar"]{
      transform:translateX(-110%)!important;min-width:0!important;max-width:0!important;width:0!important;
      overflow:hidden!important;opacity:0!important;visibility:hidden!important;pointer-events:none!important}
      html.gov-sidebar-force-show section[data-testid="stSidebar"]{
      display:block!important;transform:none!important;min-width:21rem!important;width:21rem!important;
      max-width:21rem!important;opacity:1!important;visibility:visible!important;pointer-events:auto!important;
      position:relative!important;left:0!important;margin-left:0!important}
      html.gov-sidebar-force-show section[data-testid="stSidebar"] > div{
      width:21rem!important;max-width:21rem!important}
      [data-testid="collapsedControl"],[data-testid="stSidebarCollapsedControl"],[data-testid="stSidebarCollapseButton"]{
      display:none!important;visibility:hidden!important;opacity:0!important;pointer-events:none!important}
      #gov-share-modal{position:fixed;inset:0;z-index:999999;display:none;align-items:center;justify-content:center}
      #gov-share-modal.open{display:flex}
      #gov-share-backdrop{position:absolute;inset:0;background:rgba(26,43,74,.45)}
      #gov-share-box{position:relative;background:#fff;border-radius:12px;width:min(520px,92vw);
      box-shadow:0 12px 40px rgba(26,43,74,.25);font-family:Source Sans 3,sans-serif;overflow:hidden}
      #gov-share-tabs{display:flex;border-bottom:1px solid #D4DCE8}
      #gov-share-tabs button{flex:1;padding:0.85rem 0;border:none;background:#fff;color:#6B7A90;
      font-weight:600;cursor:pointer;border-bottom:2px solid transparent}
      #gov-share-tabs button.active{color:#1A2B4A;border-bottom-color:#1A2B4A}
      .gov-share-panel{display:none;padding:1.1rem 1.25rem}
      .gov-share-panel.active{display:block}
      #gov-invite-row{display:flex;gap:0.5rem}
      #gov-invite-emails{flex:1;padding:0.65rem 0.75rem;border:1px solid #D4DCE8;border-radius:8px;font-size:0.9rem}
      #gov-invite-btn{padding:0.65rem 1rem;border:none;border-radius:8px;background:#1A2B4A;color:#fff;font-weight:600;cursor:pointer}
      .gov-social-grid{display:grid;grid-template-columns:1fr 1fr;gap:0.55rem}
      .gov-social-grid button{padding:0.65rem;border:1px solid #D4DCE8;border-radius:8px;background:#F8F9FB;
      cursor:pointer;font-weight:600;color:#1A2B4A}
      #gov-embed-code{width:100%;height:90px;padding:0.6rem;border:1px solid #D4DCE8;border-radius:8px;font-size:0.78rem}
      #gov-share-footer{display:flex;justify-content:flex-end;padding:0.85rem 1.25rem;border-top:1px solid #D4DCE8}
      #gov-copy-link{background:none;border:none;color:#2C4A7C;font-weight:700;cursor:pointer;font-size:0.88rem}
      #gov-share-close{position:absolute;top:0.55rem;right:0.75rem;border:none;background:none;font-size:1.2rem;cursor:pointer;color:#6B7A90}
      [data-testid="stToolbar"],#MainMenu,a[href*="github.com"],a[href*="streamlit.io"]{
      display:none!important;visibility:hidden!important;pointer-events:none!important}
    `;
    DOC.head.appendChild(style);
  }

  function switchTab(tab) {
    DOC.querySelectorAll("#gov-share-tabs button").forEach((b) => {
      b.classList.toggle("active", b.dataset.tab === tab);
    });
    DOC.querySelectorAll(".gov-share-panel").forEach((p) => {
      p.classList.toggle("active", p.id === "gov-tab-" + tab);
    });
  }

  function openShareModal() {
    const modal = DOC.getElementById("gov-share-modal");
    if (!modal) return;
    const url = appUrl();
    const embed = DOC.getElementById("gov-embed-code");
    if (embed) {
      embed.value = '<iframe src="' + url + '" height="720" width="100%" frameborder="0"></iframe>';
    }
    modal.classList.add("open");
    switchTab("invite");
  }

  function closeShareModal() {
    const modal = DOC.getElementById("gov-share-modal");
    if (modal) modal.classList.remove("open");
  }

  function ensureUi() {
    injectStyles();

    if (!DOC.getElementById("gov-top-actions")) {
      const bar = DOC.createElement("div");
      bar.id = "gov-top-actions";
      bar.innerHTML = '<button type="button" id="gov-share-open">Share</button>';
      DOC.body.appendChild(bar);
      DOC.getElementById("gov-share-open").addEventListener("click", openShareModal);
    }

    if (!DOC.getElementById("gov-share-modal")) {
      const modal = DOC.createElement("div");
      modal.id = "gov-share-modal";
      modal.innerHTML = `
        <div id="gov-share-backdrop"></div>
        <div id="gov-share-box">
          <button type="button" id="gov-share-close" aria-label="Close">✕</button>
          <div id="gov-share-tabs">
            <button type="button" data-tab="invite" class="active">Invite</button>
            <button type="button" data-tab="social">Social</button>
            <button type="button" data-tab="embed">Embed</button>
          </div>
          <div id="gov-tab-invite" class="gov-share-panel active">
            <div id="gov-invite-row">
              <input type="text" id="gov-invite-emails" placeholder="Emails, comma separated">
              <button type="button" id="gov-invite-btn">Invite</button>
            </div>
          </div>
          <div id="gov-tab-social" class="gov-share-panel">
            <div class="gov-social-grid">
              <button type="button" data-net="email">✉️ Email</button>
              <button type="button" data-net="whatsapp">💬 WhatsApp</button>
              <button type="button" data-net="linkedin">🔗 LinkedIn</button>
              <button type="button" data-net="facebook">📘 Facebook</button>
              <button type="button" data-net="twitter">🐦 X / Twitter</button>
              <button type="button" data-net="telegram">✈️ Telegram</button>
            </div>
          </div>
          <div id="gov-tab-embed" class="gov-share-panel">
            <textarea id="gov-embed-code" readonly></textarea>
            <button type="button" id="gov-copy-embed" style="margin-top:0.5rem;padding:0.5rem 1rem;border:none;border-radius:8px;background:#1A2B4A;color:#fff;font-weight:600;cursor:pointer">Copy embed code</button>
          </div>
          <div id="gov-share-footer">
            <button type="button" id="gov-copy-link">🔗 Copy link</button>
          </div>
        </div>
      `;
      DOC.body.appendChild(modal);
      DOC.getElementById("gov-share-close").addEventListener("click", closeShareModal);
      DOC.getElementById("gov-share-backdrop").addEventListener("click", closeShareModal);
      DOC.querySelectorAll("#gov-share-tabs button").forEach((btn) => {
        btn.addEventListener("click", () => switchTab(btn.dataset.tab));
      });
      DOC.getElementById("gov-invite-btn").addEventListener("click", () => {
        const emails = DOC.getElementById("gov-invite-emails").value.trim();
        if (!emails) return;
        const url = appUrl();
        const subject = encodeURIComponent(APP_TITLE);
        const body = encodeURIComponent("Try this government knowledge assistant:\\n\\n" + url);
        WIN.location.href = "mailto:" + emails + "?subject=" + subject + "&body=" + body;
      });
      DOC.getElementById("gov-copy-link").addEventListener("click", () => {
        copyText(appUrl()).then(() => {
          const btn = DOC.getElementById("gov-copy-link");
          const old = btn.textContent;
          btn.textContent = "✓ Copied!";
          setTimeout(() => { btn.textContent = old; }, 2000);
        });
      });
      DOC.getElementById("gov-copy-embed").addEventListener("click", () => {
        copyText(DOC.getElementById("gov-embed-code").value);
      });
      DOC.querySelectorAll(".gov-social-grid button").forEach((btn) => {
        btn.addEventListener("click", () => {
          const url = encodeURIComponent(appUrl());
          const text = encodeURIComponent(APP_TITLE);
          const net = btn.dataset.net;
          const links = {
            email: "mailto:?subject=" + text + "&body=" + encodeURIComponent(appUrl()),
            whatsapp: "https://wa.me/?text=" + text + "%20" + url,
            linkedin: "https://www.linkedin.com/sharing/share-offsite/?url=" + url,
            facebook: "https://www.facebook.com/sharer/sharer.php?u=" + url,
            twitter: "https://twitter.com/intent/tweet?url=" + url + "&text=" + text,
            telegram: "https://t.me/share/url?url=" + url + "&text=" + text,
          };
          if (links[net]) WIN.open(links[net], "_blank", "noopener,noreferrer");
        });
      });
    }
  }

  let runPending = false;
  function run() {
    if (runPending) return;
    runPending = true;
    requestAnimationFrame(() => {
      runPending = false;
      ensureUi();
      ensureSidebarToggle();
      scrub();
      blockClicks();
    });
  }

  run();
  WIN.addEventListener("resize", updateSidebarToggle);

  if (WIN.__govUiInterval) clearInterval(WIN.__govUiInterval);
  WIN.__govUiInterval = setInterval(run, 3000);
})();
