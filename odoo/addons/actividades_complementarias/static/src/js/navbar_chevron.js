/** @odoo-module **/

const MODULE_PREFIX = "actividades_complementarias";

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

document.addEventListener("DOMContentLoaded", () => {
    setTimeout(() => {
        injectChevrons();

        const navbar = document.querySelector(".o_main_navbar");
        if (navbar) {
            new MutationObserver(() => {
                injectChevrons();
            }).observe(navbar, { childList: true, subtree: true });
        }

        new MutationObserver(() => {
            setTimeout(injectChevrons, 150);
        }).observe(document.body, {
            attributes: true,
            subtree: true,
            attributeFilter: ["data-menu-xmlid"],
        });
    }, 500);
});