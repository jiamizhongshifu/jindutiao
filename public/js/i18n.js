/**
 * GaiYa Website i18n (Internationalization) Library
 * Lightweight browser-side translation system
 */
class I18n {
    constructor() {
        this.locale = 'zh_CN';
        this.translations = {};
        this.fallbackLocale = 'zh_CN';
        this.initialized = false;
    }

    /**
     * Initialize i18n system
     * Detects browser language and loads translations
     */
    async init() {
        // Check saved preference first
        const savedLang = localStorage.getItem('gaiya_locale');

        if (savedLang) {
            this.locale = savedLang;
        } else {
            // Detect browser language
            const browserLang = navigator.language || navigator.userLanguage;
            if (browserLang.startsWith('zh')) {
                this.locale = 'zh_CN';
            } else {
                this.locale = 'en_US';
            }
        }

        // Load translations
        await this.loadTranslations(this.locale);

        // Also load fallback
        if (this.locale !== this.fallbackLocale) {
            await this.loadTranslations(this.fallbackLocale);
        }

        this.initialized = true;
        console.log(`[i18n] Initialized with locale: ${this.locale}`);
    }

    /**
     * Load translation file for a locale
     * @param {string} locale - Locale code (e.g., 'zh_CN', 'en_US')
     */
    async loadTranslations(locale) {
        try {
            const response = await fetch(`/locales/${locale}.json`);
            if (response.ok) {
                const data = await response.json();
                this.translations[locale] = data;
                console.log(`[i18n] Loaded translations for ${locale}`);
            } else {
                console.warn(`[i18n] Failed to load ${locale}.json: ${response.status}`);
            }
        } catch (error) {
            console.error(`[i18n] Error loading translations for ${locale}:`, error);
        }
    }

    /**
     * Translate a key
     * @param {string} key - Translation key (supports dot notation)
     * @param {object} params - Parameters for interpolation
     * @returns {string} Translated text
     */
    t(key, params = {}) {
        // Try current locale first
        let value = this._getNestedValue(this.translations[this.locale], key);

        // Fallback to default locale
        if (!value && this.locale !== this.fallbackLocale) {
            value = this._getNestedValue(this.translations[this.fallbackLocale], key);
        }

        // Return key if not found
        if (!value) {
            console.warn(`[i18n] Missing translation: ${key}`);
            return key;
        }

        // Interpolate parameters
        return this._interpolate(value, params);
    }

    /**
     * Get nested value from object using dot notation
     * @private
     */
    _getNestedValue(obj, key) {
        if (!obj) return null;

        const keys = key.split('.');
        let value = obj;

        for (const k of keys) {
            if (value && typeof value === 'object' && k in value) {
                value = value[k];
            } else {
                return null;
            }
        }

        return typeof value === 'string' ? value : null;
    }

    /**
     * Interpolate parameters in string
     * @private
     */
    _interpolate(str, params) {
        return str.replace(/\{(\w+)\}/g, (match, key) => {
            return params.hasOwnProperty(key) ? params[key] : match;
        });
    }

    /**
     * Switch to a different locale
     * @param {string} locale - Locale code
     * @param {boolean} reload - Whether to reload the page (default: true for production)
     */
    async setLocale(locale, reload = true) {
        if (!['zh_CN', 'en_US'].includes(locale)) {
            console.warn(`[i18n] Unsupported locale: ${locale}`);
            return;
        }

        // Don't switch if already on this locale
        if (this.locale === locale) {
            console.log(`[i18n] Already on locale: ${locale}`);
            return;
        }

        this.locale = locale;
        localStorage.setItem('gaiya_locale', locale);

        console.log(`[i18n] Switching to locale: ${locale}`);

        // Reload page for clean language switch (recommended for production)
        if (reload) {
            window.location.reload();
            return;
        }

        // Alternative: Update page without reload (may have issues with dynamic content)
        // Load translations if not already loaded
        if (!this.translations[locale]) {
            await this.loadTranslations(locale);
        }

        // Update page
        this.updatePage();

        console.log(`[i18n] Switched to locale: ${locale}`);
    }

    /**
     * Get current locale
     * @returns {string} Current locale code
     */
    getLocale() {
        return this.locale;
    }

    /**
     * Update all elements with data-i18n attributes
     */
    updatePage() {
        // Update text content
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            const translated = this.t(key);
            if (translated !== key) {
                el.textContent = translated;
            }
        });

        // Update placeholders
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            const translated = this.t(key);
            if (translated !== key) {
                el.placeholder = translated;
            }
        });

        // Update titles
        document.querySelectorAll('[data-i18n-title]').forEach(el => {
            const key = el.getAttribute('data-i18n-title');
            const translated = this.t(key);
            if (translated !== key) {
                el.title = translated;
            }
        });

        // Update HTML content (use with caution)
        document.querySelectorAll('[data-i18n-html]').forEach(el => {
            const key = el.getAttribute('data-i18n-html');
            const translated = this.t(key);
            if (translated !== key) {
                el.innerHTML = translated;
            }
        });

        // Update page title
        const titleEl = document.querySelector('title[data-i18n-page-title]');
        if (titleEl) {
            const key = titleEl.getAttribute('data-i18n-page-title');
            const translated = this.t(key);
            if (translated !== key) {
                document.title = translated;
            }
        }

        // Update language switcher active state
        document.querySelectorAll('[data-lang-switch]').forEach(el => {
            const lang = el.getAttribute('data-lang-switch');
            if (lang === this.locale) {
                el.classList.add('active');
            } else {
                el.classList.remove('active');
            }
        });

        // Dispatch event for custom handlers
        document.dispatchEvent(new CustomEvent('i18n:update', {
            detail: { locale: this.locale }
        }));
    }
}

// Create global instance
window.i18n = new I18n();

// Helper function for easy access
window.t = (key, params) => window.i18n.t(key, params);

// Switch language helper
window.switchLanguage = (locale) => window.i18n.setLocale(locale);

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', async () => {
    await window.i18n.init();
    window.i18n.updatePage();
});
