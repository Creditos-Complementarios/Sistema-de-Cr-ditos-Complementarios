/** @odoo-module **/

const MODULE_PREFIX = "actividades_complementarias";

function _getStorageKey() {
    const uid = document.cookie.match(/session_id=([^;]+)/)?.[1] || "default";
    return `ac_active_menu_xmlid_${uid}`;
}

function _isModuleActive() {
    const brand = document.querySelector(".o_menu_brand");
    return brand?.dataset?.menuXmlid?.startsWith(MODULE_PREFIX) ?? false;
}

function injectChevrons() {
    if (!_isModuleActive()) return;
    const sections = document.querySelector(".o_main_navbar .o_menu_sections");
    if (!sections) return;
    sections.querySelectorAll("button").forEach(btn => {
        if (btn.querySelector(".ac_nav_chevron")) return;
        const span = document.createElement("span");
        span.className = "ac_nav_chevron";
        btn.appendChild(span);
    });
}

function setupOverlayObserver() {
    const overlayRoot = document.querySelector(".o-main-components-container");
    if (!overlayRoot) return;

    new MutationObserver(() => {
        if (!_isModuleActive()) {
            localStorage.removeItem(_getStorageKey());
            document.querySelectorAll(".o-overlay-container a[data-menu-xmlid]")
                .forEach(el => el.classList.remove("ac_menu_active_item"));
            return;
        }

        const items = document.querySelectorAll(
            ".o-overlay-container a[data-menu-xmlid][href]"
        );
        if (!items.length) return;

        const currentPath = window.location.pathname;
        const saved = localStorage.getItem(_getStorageKey());

        items.forEach(item => {
            const href  = item.getAttribute("href") || "";
            const xmlid = item.dataset.menuXmlid    || "";

            item.classList.remove("ac_menu_active_item");
            item.style.removeProperty("color");
            item.style.removeProperty("font-weight");

            const matchesUrl = href === currentPath || currentPath.startsWith(href + "/");
            const matchesSaved = saved && saved === xmlid;

            if (matchesUrl || matchesSaved) {
                item.classList.add("ac_menu_active_item");
                if (matchesUrl) {
                    localStorage.setItem(_getStorageKey(), xmlid);
                }
            }
        });
    }).observe(overlayRoot, { childList: true, subtree: true });
}

function listenMenuClicks() {
    document.addEventListener("mousedown", (e) => {
        if (!_isModuleActive()) return;
        const item = e.target.closest(
            ".o-overlay-container a[data-menu-xmlid]"
        );
        if (!item) return;
        localStorage.setItem(_getStorageKey(), item.dataset.menuXmlid);
    }, true);
}

document.addEventListener("DOMContentLoaded", () => {
    setTimeout(() => {
        injectChevrons();
        listenMenuClicks();
        setupOverlayObserver();

        const navbar = document.querySelector(".o_main_navbar");
        if (navbar) {
            new MutationObserver(() => {
                injectChevrons();
            }).observe(navbar, { childList: true, subtree: true });
        }

        new MutationObserver(() => {
            setTimeout(injectChevrons, 150);
            if (!_isModuleActive()) {
                localStorage.removeItem(_getStorageKey());
            }
        }).observe(document.body, {
            attributes: true,
            subtree: true,
            attributeFilter: ["data-menu-xmlid"],
        });
    }, 500);
});