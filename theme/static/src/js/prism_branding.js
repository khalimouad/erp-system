/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { WebClient } from "@web/webclient/webclient";
import { patch } from "@web/core/utils/patch";
import { session } from "@web/session";

// Patch the WebClient to change the title
patch(WebClient.prototype, "prism_branding.WebClient", {
    setup() {
        this._super(...arguments);
        this.title.setParts({ zopenerp: "PRISM" });
    },
});

// Override the default Odoo title
const oldGetTitle = document.title;
Object.defineProperty(document, 'title', {
    get: function() {
        const title = oldGetTitle.get.call(this);
        return title.replace(/Odoo/g, 'PRISM');
    },
    set: function(newValue) {
        oldGetTitle.set.call(this, newValue.replace(/Odoo/g, 'PRISM'));
    }
});

// Override the default Odoo service worker
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.getRegistrations().then(function(registrations) {
        for (let registration of registrations) {
            if (registration.scope.includes('odoo')) {
                registration.unregister();
            }
        }
    });
}

// Override the default Odoo session info
const originalSessionInfo = session.session_info;
if (originalSessionInfo) {
    originalSessionInfo.db_name = originalSessionInfo.db_name || "PRISM";
    originalSessionInfo.server_version = originalSessionInfo.server_version.replace(/Odoo/g, 'PRISM');
    originalSessionInfo.server_version_info = originalSessionInfo.server_version_info || [2025, 0, 0, 'PRISM', 0, ''];
}

// Add custom event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Replace any Odoo text in the DOM with PRISM
    const replaceOdooText = function() {
        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );
        
        let node;
        while (node = walker.nextNode()) {
            if (node.nodeValue.includes('Odoo')) {
                node.nodeValue = node.nodeValue.replace(/Odoo/g, 'PRISM');
            }
        }
    };
    
    // Run initially and then observe for changes
    replaceOdooText();
    
    // Create a mutation observer to watch for DOM changes
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList' || mutation.type === 'characterData') {
                replaceOdooText();
            }
        });
    });
    
    // Start observing
    observer.observe(document.body, {
        childList: true,
        subtree: true,
        characterData: true
    });
});

// Override the default Odoo favicon
const setFavicon = function() {
    let links = document.querySelectorAll('link[rel="icon"], link[rel="shortcut icon"]');
    if (links.length === 0) {
        const link = document.createElement('link');
        link.rel = 'shortcut icon';
        link.href = '/theme/static/src/img/favicon.ico';
        document.head.appendChild(link);
    } else {
        links.forEach(link => {
            if (link.href.includes('odoo')) {
                link.href = '/theme/static/src/img/favicon.ico';
            }
        });
    }
};

// Set favicon on load and when the DOM changes
document.addEventListener('DOMContentLoaded', setFavicon);
window.addEventListener('load', setFavicon);
