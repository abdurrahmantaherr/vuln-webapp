# Dark Mode Toggle Implementation Plan

This document outlines the phase-by-phase implementation plan for the dark mode toggle feature as specified in .claude/specs/dark-mode-toggle.md. The plan is strictly additive and preserves all eight intentional lab vulnerabilities.

## Phase 1: CSS Theme Definitions

**Files to modify:**
- `frontend/static/css/styles.css`

**Edits:**
Add dark theme overrides using `:root[data-theme="dark"]` selector while preserving existing `:root` (light theme) values exactly as they are.

**Before:**
```css
/* CSS Variables for Design System */
:root {
    /* Primary Colors */
    --color-brand-primary: #1a237e;
    --color-brand-secondary: #3949ab;
    --color-brand-tertiary: #283593;
    --color-brand-deep: #0d1b5e;
    --color-bg-dashboard: #eef1f8;
    --color-bg-surface: #ffffff;

    /* Text Colors */
    --color-text-primary: #1e293b;
    --color-text-secondary: #475569;
    --color-text-muted: #64748b;
    --color-text-accent: #1a237e;
    --color-text-on-brand: #ffffff;

    /* Border Radius */
    --border-radius-inputs: 8px;
    --border-radius-buttons: 8px;
    --border-radius-cards: 10px;
    --border-radius-status-tags: 6px;

    /* Shadows */
    --shadow-header: 0 2px 10px rgba(26,35,126,0.08);
    --shadow-card-hover: 0 4px 16px rgba(26,35,126,0.10);
    --shadow-focus-glow: 0 0 0 3px rgba(57,73,171,0.12);

    /* Step Colors */
    --color-step-bg: #1a237e;
    --color-step-text: #ffffff;
    --color-step-badge: rgba(255,255,255,0.2);
    --color-step-muted: rgba(255,255,255,0.85);
}
```

**After:**
```css
/* CSS Variables for Design System */
:root {
    /* Primary Colors */
    --color-brand-primary: #1a237e;
    --color-brand-secondary: #3949ab;
    --color-brand-tertiary: #283593;
    --color-brand-deep: #0d1b5e;
    --color-bg-dashboard: #eef1f8;
    --color-bg-surface: #ffffff;

    /* Text Colors */
    --color-text-primary: #1e293b;
    --color-text-secondary: #475569;
    --color-text-muted: #64748b;
    --color-text-accent: #1a237e;
    --color-text-on-brand: #ffffff;

    /* Border Radius */
    --border-radius-inputs: 8px;
    --border-radius-buttons: 8px;
    --border-radius-cards: 10px;
    --border-radius-status-tags: 6px;

    /* Shadows */
    --shadow-header: 0 2px 10px rgba(26,35,126,0.08);
    --shadow-card-hover: 0 4px 16px rgba(26,35,126,0.10);
    --shadow-focus-glow: 0 0 0 3px rgba(57,73,171,0.12);

    /* Step Colors */
    --color-step-bg: #1a237e;
    --color-step-text: #ffffff;
    --color-step-badge: rgba(255,255,255,0.2);
    --color-step-muted: rgba(255,255,255,0.85);
}

/* Dark Theme Overrides */
:root[data-theme="dark"] {
    /* Primary Colors */
    --color-brand-primary: #3b82f6;
    --color-brand-secondary: #60a5fa;
    --color-brand-tertiary: #93c5fd;
    --color-brand-deep: #2563eb;
    --color-bg-dashboard: #0f172a;
    --color-bg-surface: #1e293b;

    /* Text Colors */
    --color-text-primary: #f8fafc;
    --color-text-secondary: #cbd5e1;
    --color-text-muted: #94a3b8;
    --color-text-accent: #3b82f6;
    --color-text-on-brand: #ffffff;

    /* Border Radius */
    --border-radius-inputs: 8px;
    --border-radius-buttons: 8px;
    --border-radius-cards: 10px;
    --border-radius-status-tags: 6px;

    /* Shadows */
    --shadow-header: 0 2px 10px rgba(59,130,246,0.15);
    --shadow-card-hover: 0 4px 16px rgba(59,130,246,0.2);
    --shadow-focus-glow: 0 0 0 3px rgba(96,165,250,0.3);

    /* Step Colors */
    --color-step-bg: #3b82f6;
    --color-step-text: #ffffff;
    --color-step-badge: rgba(255,255,255,0.2);
    --color-step-muted: rgba(255,255,255,0.6);
}
```

**Verification steps addressed:**
- TC-25: WCAG AA contrast in dark theme
- FR-07: CSS Custom Properties for Theming
- NFR-03: Accessibility (WCAG AA Contrast)

## Phase 2: Login Template Updates

**Files to modify:**
- `frontend/templates/login.html`

**Edits:**
1. Add pre-paint script in `<head>` before stylesheet link
2. Add toggle button markup in top-right corner of `.right-panel` (inside `.form-container`)

**Before:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sign In - Vulnerable Web Application</title>
    <link rel="stylesheet" href="/static/css/styles.css">
</head>
```

**After:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sign In - Vulnerable Web Application</title>
    <!-- Pre-paint theme application script (blocks parsing, runs before stylesheet) -->
    <script>
        (function() {
            try {
                var theme = localStorage.getItem("theme");
                if (theme === "light" || theme === "dark") {
                    document.documentElement.dataset.theme = theme;
                } else {
                    document.documentElement.dataset.theme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
                }
            } catch (e) {
                // localStorage unavailable or error; fall back to prefers-color-scheme
                document.documentElement.dataset.theme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
            }
        })();
    </script>
    <link rel="stylesheet" href="/static/css/styles.css">
</head>
```

**Add toggle button inside `.form-container` (after `<h2>Sign In</h2>` and before form):**
```html
<!-- Add this after <h2>Sign In</h2> and <p class="form-subtitle"> -->
<h2>Sign In</h2>
<p class="form-subtitle">Enter your credentials to access the lab</p>
<button id="theme-toggle" type="button" class="theme-toggle-btn" aria-label="Switch to dark mode">
    <!-- Optional: sun/moon icon or text can go here -->
</button>
```

**Complete before/after for login.html body section:**
**Before:**
```html
<body>
    <div class="container">
        <!-- Left Panel -->
        <div class="left-panel">
            <!-- ... left panel content ... -->
        </div>

        <!-- Right Panel -->
        <div class="right-panel">
            <div class="form-container">
                <h2>Sign In</h2>
                <p class="form-subtitle">Enter your credentials to access the lab</p>
                <!-- ... rest of form ... -->
            </div>
        </div>
    </div>
</body>
```

**After:**
```html
<body>
    <div class="container">
        <!-- Left Panel -->
        <div class="left-panel">
            <!-- ... left panel content ... -->
        </div>

        <!-- Right Panel -->
        <div class="right-panel">
            <div class="form-container">
                <h2>Sign In</h2>
                <p class="form-subtitle">Enter your credentials to access the lab</p>
                <button id="theme-toggle" type="button" class="theme-toggle-btn" aria-label="Switch to dark mode">
                    <!-- Toggle button - can contain icon or text -->
                </button>

                <!-- Error Message Area -->
                <div id="error-message" class="error-message" style="display: none;">
                    Invalid credentials
                </div>

                <!-- ... rest of form remains unchanged ... -->
            </div>
        </div>
    </div>
</body>
```

**Verification steps addressed:**
- FR-01: Theme Attribute on `<html>`
- FR-02: Pre-Paint Theme Application (No Flash)
- FR-05: Keyboard Accessibility
- FR-06: aria-label Reflects Next Action
- FR-09: Position of Toggle Control
- NFR-01: Zero FOUC / No Flash on Load
- NFR-04: Backwards Compatibility
- TC-01, TC-02, TC-05, TC-06, TC-07, TC-09, TC-18, TC-22, TC-23, TC-26, TC-28, TC-29, TC-30

## Phase 3: Signup Template Updates

**Files to modify:**
- `frontend/templates/signup.html`

**Edits:**
1. Add pre-paint script in `<head>` before stylesheet link (identical to login.html)
2. Add toggle button markup in top-right corner of `.right-panel` (inside `.form-container`)

**Before:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Create Account - Vulnerable Web Application</title>
    <link rel="stylesheet" href="/static/css/styles.css">
</head>
```

**After:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Create Account - Vulnerable Web Application</title>
    <!-- Pre-paint theme application script (blocks parsing, runs before stylesheet) -->
    <script>
        (function() {
            try {
                var theme = localStorage.getItem("theme");
                if (theme === "light" || theme === "dark") {
                    document.documentElement.dataset.theme = theme;
                } else {
                    document.documentElement.dataset.theme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
                }
            } catch (e) {
                // localStorage unavailable or error; fall back to prefers-color-scheme
                document.documentElement.dataset.theme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
            }
        })();
    </script>
    <link rel="stylesheet" href="/static/css/styles.css">
</head>
```

**Add toggle button inside `.form-container` (after `<h2>Create Account</h2>` and before form):**
```html
<!-- Add this after <h2>Create Account</h2> and <p class="form-subtitle"> -->
<h2>Create Account</h2>
<p class="form-subtitle">Fill in your details to register for the lab</p>
<button id="theme-toggle" type="button" class="theme-toggle-btn" aria-label="Switch to dark mode">
    <!-- Optional: sun/moon icon or text can go here -->
</button>
```

**Verification steps addressed:**
- Same as Phase 2 (login.html) but for signup page
- TC-04, TC-07, TC-18, TC-22, TC-23, TC-26, TC-28, TC-29, TC-30

## Phase 4: Dashboard Template Updates

**Files to modify:**
- `frontend/templates/dashboard.html`

**Edits:**
1. Add pre-paint script in `<head>` before stylesheet link (identical to login/signup)
2. Add toggle button markup in fixed header's right side, alongside organizational logos

**Before:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - Vulnerable Web Application</title>
    <link rel="stylesheet" href="/static/css/styles.css">
</head>
```

**After:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - Vulnerable Web Application</title>
    <!-- Pre-paint theme application script (blocks parsing, runs before stylesheet) -->
    <script>
        (function() {
            try {
                var theme = localStorage.getItem("theme");
                if (theme === "light" || theme === "dark") {
                    document.documentElement.dataset.theme = theme;
                } else {
                    document.documentElement.dataset.theme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
                }
            } catch (e) {
                // localStorage unavailable or error; fall back to prefers-color-scheme
                document.documentElement.dataset.theme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
            }
        })();
    </script>
    <link rel="stylesheet" href="/static/css/styles.css">
</head>
```

**Add toggle button inside `.header-content` (after `.header-logos`):**
```html
<!-- Add this after </div class="header-logos"> and before </div class="header-content"> -->
<div class="header-content">
    <div class="header-title">Security Vulnerability Lab</div>
    <div class="header-logos">
        <img src="/static/images/PUCIT_Logo.png" alt="PUCIT Logo" class="logo">
        <img src="/static/images/blue-logo-scl2.png" alt="Excaliat Logo" class="logo">
        <img src="/static/images/excaliat-logo.png" alt="FCCU Logo" class="logo">
    </div>
    <button id="theme-toggle" type="button" class="theme-toggle-btn" aria-label="Switch to dark mode">
        <!-- Optional: sun/moon icon or text can go here -->
    </button>
</div>
```

**Verification steps addressed:**
- Same as Phase 2 but for dashboard page
- TC-03, TC-06, TC-07, TC-18, TC-20, TC-21, TC-23, TC-26, TC-28, TC-29, TC-30

## Phase 5: JavaScript Toggle Behavior

**Files to modify:**
- `frontend/templates/login.html`
- `frontend/templates/signup.html`
- `frontend/templates/dashboard.html`

**Edits:**
Add identical JavaScript toggle handler at the end of `<body>` (before `</body>`) in each template:

**Before `</body>` in each template:**
```html
    </body>
</html>
```

**After `</body>` in each template:**
```html
    <script>
        // Theme toggle functionality
        const themeToggleBtn = document.getElementById('theme-toggle');
        
        if (themeToggleBtn) {
            // Set initial aria-label based on current theme
            const updateAriaLabel = () => {
                const currentTheme = document.documentElement.dataset.theme;
                themeToggleBtn.setAttribute('aria-label', 
                    currentTheme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode');
            };
            
            // Initialize aria-label on load
            updateAriaLabel();
            
            // Toggle theme on button click
            themeToggleBtn.addEventListener('click', () => {
                const currentTheme = document.documentElement.dataset.theme;
                const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
                
                // Update html attribute
                document.documentElement.dataset.theme = newTheme;
                
                // Persist to localStorage (with error handling for privacy modes)
                try {
                    localStorage.setItem('theme', newTheme);
                } catch (e) {
                    // localStorage unavailable; theme still works for current session
                }
                
                // Update aria-label for next action
                updateAriaLabel();
            });
        }
    </script>
</body>
</html>
```

**Verification steps addressed:**
- FR-03: localStorage Persistence
- FR-04: prefers-color-scheme Fallback
- FR-05: Keyboard Accessibility (inherited from native button)
- FR-06: aria-label Reflects Next Action
- FR-08: Implementation Surface (vanilla JS, no frameworks)
- NFR-02: Performance (lightweight script)
- NFR-04: Backwards Compatibility
- TC-05, TC-06, TC-07, TC-16, TC-17, TC-18, TC-29, TC-30
- AP-01, AP-02, AP-03, AP-04 (edge cases handled via try/catch)

## Phase 6: Vulnerability Preservation Verification

**Files to verify (NO CHANGES MADE):**
- All backend files (preserve SQL injection, weak password storage, exposed database, no rate limiting, CSRF)
- All frontend templates (preserve stored XSS via `{{username}}` substitution, reflected XSS in `/search`)

**Verification steps addressed:**
- All TC-08 through TC-15 (stored XSS, SQL injection, reflected XSS, session hijacking, weak password storage, exposed database, no rate limiting, CSRF)
- TC-27: Reflected XSS works in both themes
- TC-37: Stored XSS preserves with theme active
- All "Additive non-regression" test cases from spec

## Implementation Notes

1. **Positioning CSS**: Add minimal positioning CSS for toggle button (can be added to existing styles or inline if preferred per spec's "no new files" requirement):
   ```css
   /* Add to existing styles.css */
   .theme-toggle-btn {
       position: absolute;
       top: 16px;
       right: 16px;
       background: transparent;
       border: none;
       font-size: 1.25rem;
       cursor: pointer;
       padding: 8px;
       color: var(--color-text-on-brand);
   }
   
   /* For dashboard header (adjust positioning) */
   .header .theme-toggle-btn {
       position: static;
       margin-left: auto;
   }
   ```
   *Note: Per spec FR-08 and NFR-04, this should be minimal and not affect layout if JS is disabled.*

2. **Accessibility**: Native button provides keyboard accessibility (Enter/Space) per FR-05.

3. **Error Handling**: Try/catch blocks around localStorage operations per FR-03 and AP-02.

4. **No Flash Guarantee**: Inline script in `<head>` before stylesheet ensures FR-02 and NFR-01.

5. **Vulnerability Preservation**: Zero changes to backend or existing frontend logic that powers the 8 lab vulnerabilities.

This plan strictly follows the specification and will result in changes only to the four specified files:
- `frontend/static/css/styles.css`
- `frontend/templates/login.html`
- `frontend/templates/signup.html`
- `frontend/templates/dashboard.html`

No new files are created, and no existing functionality (including vulnerabilities) is altered.