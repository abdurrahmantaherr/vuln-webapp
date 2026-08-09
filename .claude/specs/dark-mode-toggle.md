# Software Specification Document (Implementation Addendum)

## Scope
This document captures implementation-level behavior for an additive dark mode toggle feature on the three frontend templates (login, signup, dashboard). It is strictly scoped to presentation-layer changes driven by CSS custom properties and a `data-theme` attribute on the `<html>` element. Theme preference is persisted in `localStorage` under the key `"theme"` and restored before paint to prevent a flash of incorrect theme. This specification explicitly does NOT alter any of the eight intentional lab vulnerabilities; the application remains a security education platform exactly as specified in PRD.md, TDD.md, and `.claude/specs/app-foundation.md`. This addendum reuses the section conventions of `app-foundation.md` and adds nothing to runtime behavior, persistence model, session model, authentication flow, or backend code paths.

## Runtime Behavior
- Theme is applied via a `data-theme` attribute on the `<html>` element (root element) with values `"light"` or `"dark"`
- A blocking inline `<script>` runs in the `<head>` of every affected template (before the stylesheet loads) to set `document.documentElement.dataset.theme` before first paint
- The blocking script reads `localStorage.getItem("theme")`; if absent or not one of `"light"`/`"dark"`, it falls back to `window.matchMedia("(prefers-color-scheme: dark)").matches`
- The CSS custom properties defined in `frontend/static/css/styles.css` are rebased inside `:root[data-theme="light"]` and `:root[data-theme="dark"]` selectors so that the same component styles render correctly in both themes
- Theme toggle button is a client-side only control; clicking it swaps `data-theme` on `<html>` and writes the new value to `localStorage` under key `"theme"`
- No server-side changes, no new endpoints, no changes to the database, no changes to session handling
- The toggle button's `aria-label` reflects the action that will happen on the next click (i.e., when the current theme is light, the label reads "Switch to dark mode"; when dark, it reads "Switch to light mode")
- Theme preference persists across page navigation within the application because it is keyed on `<html>` and stored in `localStorage`
- Theme preference persists across browser sessions for the same origin because `localStorage` is durable

## Scope & Non-Goals

### In Scope
- A light/dark theme toggle control rendered on `login.html`, `signup.html`, and `dashboard.html`
- Visual restyling of the existing color palette via CSS custom properties under `:root[data-theme="..."]` selectors
- `localStorage` persistence under key `"theme"`
- `prefers-color-scheme` fallback when no saved value exists
- Accessibility: keyboard activation, `aria-label`, visible focus
- A blocking pre-paint script to prevent flash of incorrect theme (FOUC/FOIT)

### Intentionally NOT In Scope (Lab Vulnerabilities Remain)
All eight OWASP Top 10 vulnerabilities implemented for security education MUST remain intact and exploitable. This addendum MUST NOT remove, sanitize, escape, validate, rate-limit, or otherwise fix any of them:
1. **SQL Injection** — login and signup SQL queries via string concatenation remain unchanged
2. **Stored XSS** — username continues to be stored unsanitized and reflected on dashboard via `{{username}}` substitution (the `<script>` tag in a stored username MUST still render and execute; see TC-08)
3. **Reflected XSS** — `/search` endpoint continues to interpolate the `query` parameter directly into HTML response without escaping
4. **Session Hijacking** — hardcoded weak session signing secret `"super-secret-key-12345"` remains unchanged
5. **Weak Password Storage** — MD5 hashing without salt in `hash_password()` remains unchanged
6. **Exposed Database** — unauthenticated `/download/db` endpoint remains unchanged
7. **No Rate Limiting** — no endpoint receives rate limiting, throttling, captcha, or lockout
8. **CSRF** — no token validation is added to any form

## User Flows

### Theme Toggle Flow
1. User loads any of the three affected pages (login, signup, or dashboard)
2. Before first paint, the inline pre-paint script reads `localStorage.getItem("theme")`
3. If value is `"light"` or `"dark"`, that value is applied to `<html data-theme="...">`
4. If value is absent/null/non-matching, the script checks `window.matchMedia("(prefers-color-scheme: dark)").matches`
5. If the media query matches, `"dark"` is applied; otherwise `"light"` is applied
6. Page renders in the resolved theme without flash
7. User clicks the toggle button (or activates it via keyboard)
8. The new theme value is computed by flipping the current value
9. `document.documentElement.dataset.theme` is set to the new value
10. `localStorage.setItem("theme", newValue)` persists the preference
11. `aria-label` on the toggle button updates to reflect the new "next action"
12. CSS custom properties re-resolve under the new `data-theme` selector and the page repaints

### Cross-Page Persistence Flow
1. User toggles theme to dark on `/login`
2. `localStorage.theme === "dark"` and `<html data-theme="dark">`
3. User submits form (via existing login or signup POST) and is redirected to `/welcome`
4. Dashboard HTML loads; the inline pre-paint script reads `localStorage.theme === "dark"`
5. `data-theme="dark"` is set before paint; dashboard renders in dark theme on first paint (no flash)

## Functional Requirements

### FR-01: Theme Attribute on `<html>`
- A `data-theme` attribute on `<html>` controls theme; legal values are `"light"` and `"dark"`
- Absence of `data-theme` is treated as light theme (current default) for graceful degradation
- All theme-aware CSS uses `:root[data-theme="..."]` selectors — never `[data-theme]` on body or any inner element
- Toggle button manipulates `document.documentElement.dataset.theme`, not a child element

### FR-02: Pre-Paint Theme Application (No Flash)
- A blocking inline `<script>` is placed in the `<head>` of each affected template, BEFORE the `<link rel="stylesheet">`
- The script sets `document.documentElement.dataset.theme` synchronously before the browser paints
- No `DOMContentLoaded`, `load`, or other deferred event is used for theme application
- No framework, no build step, no module bundler

### FR-03: localStorage Persistence
- Key: literal string `"theme"`
- Values: literal strings `"light"` or `"dark"`; any other value is treated as absent
- Read on every page load by the pre-paint script
- Written on every toggle interaction
- No JSON wrapping; values are plain strings
- If `localStorage` is unavailable (e.g., disabled browser storage), the toggle still works for the current page using `prefers-color-scheme` and does not throw

### FR-04: prefers-color-scheme Fallback
- When `localStorage.getItem("theme")` is `null` or not `"light"`/`"dark"`, fall back to `window.matchMedia("(prefers-color-scheme: dark)").matches`
- If the media query matches, apply `"dark"`; otherwise apply `"light"`
- Fallback is consulted only on initial load, not on subsequent toggle interactions
- A change to `prefers-color-scheme` while the page is open does NOT auto-update the theme (out of scope)

### FR-05: Keyboard Accessibility
- Toggle is implemented as a real `<button>` element, not a `<div>` with a click handler
- Native button focus, focus ring, and Enter/Space activation are inherited from the browser
- No `tabindex`, no custom key handlers, no `e.preventDefault()` on space/enter
- The button participates in normal tab order on each affected page

### FR-06: aria-label Reflects Next Action
- `aria-label` is dynamically updated to describe the action the button will perform when activated
- When current theme is light, label reads: `"Switch to dark mode"`
- When current theme is dark, label reads: `"Switch to light mode"`
- Label updates synchronously inside the same click/keydown handler that flips the theme
- A visible text label or icon MAY also be present, but `aria-label` MUST be set on the button itself

### FR-07: CSS Custom Properties for Theming
- All existing color tokens in `styles.css` (e.g., `--color-bg-dashboard`, `--color-text-primary`, `--color-bg-surface`) continue to exist under `:root`
- The `:root` selector declares the LIGHT values (matching today's appearance exactly so that removing JS leaves the page identical to today)
- A new `:root[data-theme="dark"]` selector declares the DARK values for every token used by the affected templates
- No hardcoded color hex values are introduced into components; components continue to reference variables
- Brand gradient on auth pages (login/signup left panel) and dashboard hero banner receives dark-theme values via custom-property overrides; the gradient structure (`linear-gradient(135deg, ...)`) is preserved

### FR-08: Implementation Surface
- The toggle is implemented with vanilla JavaScript, CSS custom properties, and a `data-theme` attribute on `<html>`
- No JavaScript framework, no build step, no preprocessor, no new dependencies
- Affected files: `frontend/static/css/styles.css`, `frontend/templates/login.html`, `frontend/templates/signup.html`, `frontend/templates/dashboard.html`
- No other file is created or modified (no `theme.js`, no backend changes, no template partials)

### FR-09: Position of Toggle Control
- Login and signup: toggle button is rendered in the top-right corner of the right (form) panel, absolutely positioned relative to `.right-panel` (or `.form-container`)
- Dashboard: toggle button is rendered in the fixed header's right side, alongside or near the three organizational logos
- On screens narrower than 768px, the toggle remains visible and reachable (it is not hidden in responsive layouts)

## Non-Functional Requirements

### NFR-01: Zero FOUC / No Flash on Load
- The theme applied at first paint equals the theme that will be applied after JS executes
- No light-theme flash when the user's saved preference is dark
- No dark-theme flash when the user's saved preference is light

### NFR-02: Performance
- The blocking pre-paint script is < 1 KB, contains no DOM tree walks, no queries, no loops beyond a single ternary
- No network requests, no fonts, no images added by this feature
- No measurable impact on Largest Contentful Paint beyond the synchronous script execution

### NFR-03: Accessibility (WCAG AA Contrast)
- Dark-theme color pairings MUST meet WCAG AA contrast (4.5:1 for body text, 3:1 for large text and UI components)
- Focus indicators remain visible in both themes (the existing `--shadow-focus-glow` continues to render against both backgrounds)
- The toggle button has visible focus state inherited from browser defaults plus the existing focus-glow style

### NFR-04: Backwards Compatibility
- If JavaScript is disabled, pages render in the LIGHT theme (the `:root` default), matching today's appearance exactly
- If `localStorage` throws (private mode in some browsers), the toggle still works in-memory for the current page; no exception is surfaced to the user
- If `prefers-color-scheme` is unavailable, the system light value is used

### NFR-05: No Regression on Lab Vulnerabilities
- After deployment, all eight lab vulnerabilities MUST remain exploitable as documented in `.claude/specs/app-foundation.md`
- No new escaping, sanitization, validation, or rate limiting is introduced anywhere
- The `{{username}}` substitution on `dashboard.html` continues to inject raw HTML; a stored `<script>alert(1)</script>` username still fires on the dashboard (TC-08)

## Success Paths

### SP-01: First-Visit Light Theme (System Preference Light)
1. User loads `/login` for the first time on a device with light system preference
2. `localStorage.theme` is `null`
3. `prefers-color-scheme: dark` media query returns `false`
4. Pre-paint script sets `<html data-theme="light">`
5. Page renders in light theme on first paint
6. Toggle button shows "Switch to dark mode" label
7. User clicks toggle
8. Theme flips to dark; `localStorage.theme = "dark"`; label updates to "Switch to light mode"

### SP-02: First-Visit Dark Theme (System Preference Dark)
1. User loads `/signup` on a device with dark system preference
2. `localStorage.theme` is `null`
3. `prefers-color-scheme: dark` media query returns `true`
4. Pre-paint script sets `<html data-theme="dark">`
5. Page renders in dark theme on first paint
6. Toggle button shows "Switch to light mode" label

### SP-03: Returning User — Saved Dark Theme
1. User who previously selected dark mode loads `/login`
2. `localStorage.theme === "dark"`
3. Pre-paint script sets `<html data-theme="dark">` BEFORE stylesheet parses
4. Page renders dark on first paint; no light flash
5. Toggle button shows "Switch to light mode" label

### SP-04: Returning User — Saved Light Theme
1. User who previously selected light mode loads `/welcome`
2. `localStorage.theme === "light"`
3. Pre-paint script sets `<html data-theme="light">`
4. Page renders light on first paint; no dark flash
5. Toggle button shows "Switch to dark mode" label

### SP-05: Cross-Page Persistence
1. User toggles to dark on `/login`
2. User logs in and is redirected to `/welcome`
3. `localStorage.theme === "dark"` is read by dashboard's pre-paint script
4. Dashboard renders dark on first paint without any flash

## Alternate Paths

### AP-01: Stored Value Is Invalid
1. `localStorage.theme === "purple"` (or any non-`"light"`/`"dark"` value)
2. Pre-paint script treats invalid value as absent
3. Falls back to `prefers-color-scheme` resolution (SP-01 or SP-02)
4. Theme resolves correctly without error

### AP-02: localStorage Throws (Privacy Mode)
1. `localStorage.getItem("theme")` throws `SecurityError` or returns `null`
2. Pre-paint script catches throw (or accepts `null`) and falls back to `prefers-color-scheme`
3. Page renders correctly in the resolved theme
4. Toggle still works in-memory for the current page; `localStorage.setItem` may silently fail but does not throw

### AP-03: prefers-color-scheme Unavailable
1. `window.matchMedia` is undefined or returns `null.matches`
2. Pre-paint script defaults to `"light"`
3. Page renders in light theme; toggle continues to function

### AP-04: JavaScript Disabled
1. User has JavaScript disabled in browser
2. Pre-paint script does not execute
3. No `data-theme` attribute is set
4. CSS selectors that require `[data-theme="dark"]` do not match
5. Page renders in light theme using the `:root` defaults — visually identical to today
6. Toggle button is visible but inert

## Edge Cases

### EC-01: localStorage Cleared Mid-Session
- User clears site data while page is open
- Subsequent toggle writes may throw or be silently dropped
- Toggle still updates `data-theme` for the current page
- On next reload, the theme is resolved via `prefers-color-scheme`

### EC-02: Multiple Tabs Open
- User opens `/login` and `/welcome` in two tabs
- Toggle in tab 1 writes `localStorage.theme = "dark"`
- Tab 2 does NOT auto-update (no `storage` event listener — out of scope)
- Reloading tab 2 picks up the new value via the pre-paint script

### EC-03: Toggle Button Pressed Before Page Fully Painted
- Pre-paint script has already set `data-theme` by the time the toggle button is clickable
- Clicking the toggle is well-defined at any point after the button is in the DOM
- No race condition between pre-paint script and toggle script

### EC-04: Stored XSS Username With Theme Active
- A user with stored username `<script>alert('xss')</script>` logs in
- `{{username}}` substitution injects the raw script
- The script executes in the dark-themed dashboard exactly as it does in light mode
- The presence of `data-theme="dark"` on `<html>` does NOT block the script
- TC-08 asserts this behavior is preserved

### EC-05: Dashboard Render With Dark Theme + Stored XSS Payload
- User toggles to dark theme
- Logs in as a user with an XSS-payload username
- Page renders dark
- XSS payload executes
- Both behaviors are observable simultaneously; neither is regressed

### EC-06: Theme Toggle Clicked During Form Submission
- User clicks toggle while signup form is submitting
- Toggle handler updates `data-theme` and `localStorage`
- Form submission is unaffected; toggle does not `e.preventDefault()` on form submit
- Server receives the same form data regardless of theme state

### EC-07: Reflected XSS in /search Endpoint
- Out of scope for this spec; the `/search` endpoint is server-side and unaffected by the frontend theme toggle
- Search results continue to render unsanitized HTML in both light and dark themes

## Business Rules

1. The toggle is additive UI; it MUST NOT introduce escaping of any server-rendered content.
2. The toggle MUST NOT introduce CSRF tokens, rate limits, captchas, or any other defenses — doing so would fix a lab vulnerability.
3. The `localStorage` key MUST be the literal string `"theme"` (lowercase, no namespace) so it is the same key across all three pages.
4. The `:root` selector in `styles.css` continues to declare the LIGHT values so that disabling JavaScript leaves the application visually identical to the current release.
5. The pre-paint script MUST be inline (not an external file) so it blocks parsing and runs before the stylesheet applies colors.
6. The pre-paint script MUST NOT depend on any framework, library, or external file.

## Rebuild Requirements

A compatible implementation of this addendum MUST reproduce the following exact behaviors:

1. **Pre-paint Script (in `<head>`, before `<link rel="stylesheet">`, in all three templates):**
   - Read `localStorage.getItem("theme")`
   - If value is `"light"` or `"dark"`, set `document.documentElement.dataset.theme` to that value
   - Otherwise, set `document.documentElement.dataset.theme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"`
   - Script is synchronous, inline, and contains no event listeners
   - Script is wrapped to catch any `localStorage` exception and fall back to `matchMedia`

2. **CSS Theming (in `frontend/static/css/styles.css`):**
   - `:root` selector continues to declare LIGHT values for all existing tokens (no behavioral change for users without the toggle)
   - New `:root[data-theme="dark"]` selector overrides every token consumed by `login.html`, `signup.html`, and `dashboard.html`
   - WCAG AA contrast (4.5:1 body, 3:1 large/UI) is met for dark-theme pairings
   - Brand gradients (`linear-gradient(135deg, var(--color-brand-...)...)`) on auth left panels and dashboard hero continue to use variable references and resolve correctly in both themes

3. **Toggle Button (in all three templates):**
   - Real `<button>` element with `type="button"`
   - `aria-label` reflects next action ("Switch to dark mode" when current theme is light; "Switch to light mode" when dark)
   - `click` listener flips `document.documentElement.dataset.theme` and writes `localStorage.setItem("theme", newValue)`
   - Listener also updates the button's `aria-label` to match the new next action
   - Button is keyboard reachable via Tab; Enter and Space activate it natively
   - Button has visible focus styling (existing `--shadow-focus-glow` is applied via `:focus-visible`)

4. **Position:**
   - Login/signup: inside `.right-panel` (or `.form-container`), top-right corner
   - Dashboard: inside `.header-content`, alongside the existing three organizational logos
   - On viewports < 768px the button remains visible and clickable

5. **No Other Files Touched:**
   - No new `.js` files
   - No backend changes (no FastAPI route changes, no middleware changes)
   - No new template partials
   - No database changes
   - No session/cookie changes
   - No `package.json`, `pyproject.toml`, or `uv.lock` changes

6. **Lab Vulnerabilities Preserved (must be unchanged):**
   - SQL Injection: login/signup string-concatenation queries
   - Stored XSS: `{{username}}` substitution injects raw HTML on dashboard
   - Reflected XSS: `/search` query parameter interpolated directly into HTML response
   - Session Hijacking: hardcoded signing secret
   - Weak Password Storage: unsalted MD5
   - Exposed Database: unauthenticated `/download/db`
   - No Rate Limiting: still absent on all endpoints
   - CSRF: still absent on all forms

## Acceptance Criteria

### AC-01: Pre-Paint Theme Application
- Given a returning user with `localStorage.theme === "dark"`
- When they load `/login`, `/signup`, or `/welcome`
- Then `<html data-theme="dark">` is set before first paint
- And no light-theme flash is visible
- And the toggle button's `aria-label` reads "Switch to light mode"

### AC-02: prefers-color-scheme Fallback
- Given a first-time visitor with no saved preference and a dark system preference
- When they load any of the three pages
- Then `<html data-theme="dark">` is set before first paint
- And the toggle button's `aria-label` reads "Switch to light mode"

### AC-03: localStorage Persistence Across Pages
- Given a user who has toggled to dark on `/login`
- When they submit the login form and land on `/welcome`
- Then `/welcome` renders in dark theme on first paint
- And `localStorage.getItem("theme")` returns `"dark"`

### AC-04: Keyboard Accessibility
- Given the toggle button is rendered on any page
- When the user tabs to it and presses Enter or Space
- Then the theme toggles
- And `aria-label` updates to the new next action
- And `localStorage` is updated

### AC-05: aria-label Reflects Next Action
- Given the current theme is light
- When the toggle button is rendered
- Then `aria-label` is the literal string `"Switch to dark mode"`
- And when the current theme is dark, `aria-label` is `"Switch to light mode"`

### AC-06: No-JS Graceful Degradation
- Given JavaScript is disabled
- When any of the three pages is loaded
- Then the page renders in the light theme (identical to current production)
- And no `data-theme` attribute is set
- And the toggle button is visible but inert

### AC-07: No Flash of Unstyled / Wrong Theme
- Given any of the three pages is loaded with a saved `localStorage.theme`
- When the browser begins painting
- Then the first paint uses the saved theme
- And no brief appearance of the wrong theme is observable

### AC-08: Lab Vulnerabilities Untouched
- Given the application is rebuilt with the dark mode feature
- When a user registers with username `<script>alert('xss')</script>`
- And logs in
- Then the dashboard still injects the raw `<script>` tag into the hero banner
- And the script executes regardless of current theme
- And TC-08 passes

## Test Cases

| TC-ID | Scenario | Precondition | Expected Result |
|-------|----------|--------------|-----------------|
| TC-01 | First-visit light fallback | `localStorage` empty, system preference light | `<html data-theme="light">` set before first paint on login, signup, and dashboard; toggle label reads "Switch to dark mode" |
| TC-02 | First-visit dark fallback | `localStorage` empty, system preference dark | `<html data-theme="dark">` set before first paint on all three pages; toggle label reads "Switch to light mode" |
| TC-03 | Saved dark persists across pages | `localStorage.theme === "dark"` set, login page loaded | Page paints dark on first load; toggle to `/welcome` via login, dashboard also paints dark on first load; no light flash on either page |
| TC-04 | Saved light persists across pages | `localStorage.theme === "light"` set, signup page loaded | Page paints light on first load; submit signup and redirect to `/login`; `/login` paints light on first load; no dark flash |
| TC-05 | Toggle click flips theme | On login page in light theme | Click toggle; `<html data-theme="dark">`; `localStorage.theme === "dark"`; toggle label changes to "Switch to light mode" |
| TC-06 | Toggle click reverse | On dashboard in dark theme | Click toggle; `<html data-theme="light">`; `localStorage.theme === "light"`; toggle label changes to "Switch to dark mode" |
| TC-07 | Keyboard activation | On signup page | Tab to toggle button (focus ring visible); press Enter; theme flips; press Space; theme flips back |
| TC-08 | Stored XSS preserved (additive non-regression) | User registers with username `<script>alert('xss')</script>`; logs in | Dashboard renders the raw `<script>` tag in the hero banner; script executes (alert fires) regardless of current theme; `{{username}}` substitution is unchanged |
| TC-09 | SQL Injection preserved (additive non-regression) | `/login` endpoint accessible | Submitting `' OR '1'='1` as username and any password returns `{ success: true, redirect: "/welcome" }`; theme toggle remains visible and functional on the login page |
| TC-10 | Reflected XSS preserved (additive non-regression) | `/search` endpoint accessible | `GET /search?q=<script>alert(1)</script>` returns HTML containing the unescaped `<script>` tag; theme does not affect server response |
| TC-11 | Session Hijacking secret unchanged (additive non-regression) | Codebase inspection | `super-secret-key-12345` is still present in `backend/app/main.py` (or equivalent location); no rotation, no environment variable introduced |
| TC-12 | Weak password storage unchanged (additive non-regression) | Register a user with password `Password123!` | Stored password in `vulnerable_app.db` is the unsalted MD5 hash `42f749ade7f9e195bf475f37a44cafcb` |
| TC-13 | Exposed database endpoint unchanged (additive non-regression) | Unauthenticated request | `GET /download/db` returns the SQLite database file without authentication |
| TC-14 | No rate limiting on login (additive non-regression) | 100 rapid login submissions | All 100 requests are processed; none are throttled, blocked, or rejected by a rate limiter |
| TC-15 | CSRF token absent (additive non-regression) | Inspect login/signup templates and POST handlers | No CSRF token field is added to login or signup forms; backend still does not validate any token |
| TC-16 | Invalid localStorage value falls back | `localStorage.theme === "purple"` set | Page resolves to light or dark based on `prefers-color-scheme`; no JS error thrown |
| TC-17 | localStorage unavailable | Browser denies localStorage access (e.g., strict privacy) | Page still renders in the correct theme via `prefers-color-scheme`; toggle still flips theme for current page; no uncaught exception |
| TC-18 | JavaScript disabled | Browser has JS disabled | Pages render in light theme (matching current production); toggle button visible but inert |
| TC-19 | Multiple tabs | Two tabs of `/login` open | Toggling theme in tab 1 updates tab 1 only; tab 2 keeps its current theme until reload (no `storage` event listener required) |
| TC-20 | Dashboard toggle position | Dashboard loaded at viewport width 1280px | Toggle is visible in the fixed header alongside or near the three organizational logos; does not overlap the title |
| TC-21 | Mobile dashboard toggle | Dashboard loaded at viewport width 375px | Toggle remains visible in the header; logos are scaled to 40px per existing responsive rules; toggle does not overflow |
| TC-22 | Auth-page toggle position | Login or signup loaded at viewport width 1280px | Toggle is visible in the top-right of the right (form) panel; does not overlap form inputs |
| TC-23 | Focus ring in dark theme | Dashboard in dark theme, toggle focused | Visible focus indicator using `--shadow-focus-glow` or equivalent outline on dark background |
| TC-24 | No new files created | Repository inspection after implementation | Only `styles.css`, `login.html`, `signup.html`, `dashboard.html` are modified; no new `.js`, `.css`, `.html`, or backend files appear |
| TC-25 | WCAG AA contrast in dark theme | Dashboard rendered in dark theme | Body text vs surface background contrast ratio ≥ 4.5:1; secondary text vs surface ≥ 4.5:1; UI component borders vs surface ≥ 3:1 |
| TC-26 | Form submission unaffected by theme | Login form filled, light theme active | Submitting form performs identical AJAX POST to `/login`; theme toggle does not `preventDefault` on the form submit event |
| TC-27 | Reflected XSS works in both themes | `/search?q=<script>alert(1)</script>` | Unescaped `<script>` is present in the response HTML in both light and dark contexts (response is server-side, theme-independent) |
| TC-28 | Pre-paint script is inline | Inspect `<head>` of each affected template | A `<script>` tag containing the theme-resolution logic appears BEFORE the `<link rel="stylesheet" href="/static/css/styles.css">`; it has no `src` attribute (inline) |
| TC-29 | localStorage key is exactly "theme" | Browser devtools, Application tab | The key is the literal string `theme` (lowercase, no prefix, no namespace) |
| TC-30 | aria-label updates on every toggle | Start on login in light theme | `aria-label` is `"Switch to dark mode"` → click → `"Switch to light mode"` → click → `"Switch to dark mode"`; label matches current next action after every flip |

## Verification Steps

Manual verification on a developer workstation after rebuild:

1. **Start the application**:
   ```bash
   uv run backend/app/main.py
   ```
   Expected console output: Uvicorn running on `http://0.0.0.0:3001` (or `http://127.0.0.1:3001` if `HOST` is set).

2. **Verify first-visit light fallback (TC-01)**:
   - Open browser DevTools → Application → Local Storage → `http://localhost:3001` → delete the `theme` key
   - Set OS / browser to light theme
   - Visit `http://localhost:3001/login`
   - Expected: page renders in light theme on first paint; toggle label is "Switch to dark mode"

3. **Verify first-visit dark fallback (TC-02)**:
   - Delete `theme` key from localStorage
   - Set OS / browser to dark theme
   - Visit `http://localhost:3001/signup`
   - Expected: page renders in dark theme on first paint; toggle label is "Switch to light mode"

4. **Verify cross-page persistence (TC-03, TC-04)**:
   - Set `localStorage.theme = "dark"` in DevTools
   - Visit `http://localhost:3001/login`, then log in, then observe `http://localhost:3001/welcome`
   - Expected: both pages render dark on first paint without flash
   - Repeat with `localStorage.theme = "light"`

5. **Verify toggle interaction (TC-05, TC-06)**:
   - On `/login`, click the toggle button
   - Expected: theme flips, `localStorage.theme` updates, label changes
   - Repeat on `/welcome`

6. **Verify keyboard accessibility (TC-07)**:
   - On `/signup`, press Tab until the toggle button is focused
   - Press Enter; theme should flip
   - Press Space; theme should flip back

7. **Verify stored XSS still works (TC-08)**:
   - Register a new account with username `<script>alert('xss')</script>` via `http://localhost:3001/signup`
   - Log in via `http://localhost:3001/login`
   - Expected: dashboard renders, alert fires, hero banner contains literal `<script>` tag in the HTML source (View Page Source)
   - Repeat in dark theme; alert still fires

8. **Verify SQL injection still works (TC-09)**:
   - On `http://localhost:3001/login`, submit username `' OR '1'='1` and any password
   - Expected: response is `{ success: true, redirect: "/welcome" }`; theme toggle remains functional

9. **Verify reflected XSS still works (TC-10)**:
   - Visit `http://localhost:3001/search?q=<script>alert(1)</script>`
   - Expected: HTML response contains an unescaped `<script>` tag; theme does not affect the response

10. **Verify no new files (TC-24)**:
    ```bash
    git status
    ```
    Expected: only `frontend/static/css/styles.css`, `frontend/templates/login.html`, `frontend/templates/signup.html`, `frontend/templates/dashboard.html` are modified.

## Documentation Gaps

1. **Dark-Theme Token Catalog**: This specification introduces dark values for existing CSS custom properties but does not enumerate every individual hex override; the implementer is expected to derive each dark value from the corresponding light value while satisfying WCAG AA contrast (NFR-03).
2. **Toggle Visual Iconography**: This specification does not mandate whether the toggle button shows text, an icon (e.g., moon/sun), or both, so long as `aria-label` reflects the next action (FR-06). The implementer may choose any visible representation.
3. **Theme Persistence Across Logout**: The toggle state is intentionally independent of authentication; logging out does not reset the theme. This is by design but is not surfaced in user-facing copy.
4. **System Preference Change Mid-Session**: A change to `prefers-color-scheme` after page load is intentionally NOT observed in real time; only the value at first paint is consulted. The implementer MAY add a `matchMedia.addEventListener` later as an enhancement, but it is not required.