# Password Strength Meter Implementation Plan

This document outlines the phase-by-phase implementation plan for the password strength meter feature as specified in `.claude/specs/password-str-meter.md`. The plan is strictly additive/advisory and preserves all eight intentional lab vulnerabilities, including the intentional absence of server-side password policy enforcement.

**Discovery note**: Inspection of the current codebase shows the required markup, client-side logic, and CSS for this feature are **already present** in `frontend/templates/signup.html` and `frontend/static/css/styles.css`, and already satisfy the spec's functional requirements (5 criteria, live `input`-event updates, advisory-only behavior, no server round-trip). This plan therefore consists of a verification pass confirming the existing implementation against every AC/FR/Business Logic rule in the spec, plus one identified follow-up item (Phase 4) for theme-contrast robustness. No files are expected to require changes unless Phase 4's verification surfaces a real contrast defect.

## Phase 1: Verify Signup Template Markup

**Files to inspect (no changes anticipated):**
- `frontend/templates/signup.html`

**Verification:**
Confirm the form contains, in order, directly below the Confirm Password group and above the submit button:
```html
<!-- Password Strength Meter (Advisory UX) -->
<div class="password-strength-meter">
    <label>Password Strength:</label>
    <div class="strength-bar">
        <div class="strength-fill" id="strength-fill"></div>
    </div>
    <ul class="strength-criteria" id="strength-criteria">
        <li>8+ characters</li>
        <li>Lowercase letter</li>
        <li>Uppercase letter</li>
        <li>Digit</li>
        <li>Special character</li>
    </ul>
</div>
```
Confirm:
- Element IDs `#strength-fill` and `#strength-criteria` exist exactly as named (required by API Contract in spec Section 6).
- The 5 `<li>` items appear in the fixed order: length, lowercase, uppercase, digit, special (required for correct indexed access in the JS handler — Section 6 / Rule 4-6 ordering dependency).
- The meter block sits inside `#signup-form`, not duplicated elsewhere, and does not appear in `frontend/templates/login.html` (AC-11).

**Verification steps addressed:**
- UX-01, UX-02
- AC-01 (structural prerequisite), AC-11
- Section 6 (DOM element ID contract)

## Phase 2: Verify Client-Side Strength Evaluation Logic

**Files to inspect (no changes anticipated):**
- `frontend/templates/signup.html` (inline `<script>` block)

**Verification:**
Confirm the `input` event listener on `#password` matches the required behavior:
```javascript
passwordInput.addEventListener('input', function() {
    const password = this.value;
    let strength = 0;
    const criteria = [
        password.length >= 8,
        /[a-z]/.test(password),
        /[A-Z]/.test(password),
        /\d/.test(password),
        /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)
    ];

    strength = criteria.filter(Boolean).length;
    strengthFill.style.width = (strength / 5) * 100 + '%';

    strengthCriteria[0].style.color = criteria[0] ? '#166534' : '#64748b';
    strengthCriteria[1].style.color = criteria[1] ? '#166534' : '#64748b';
    strengthCriteria[2].style.color = criteria[2] ? '#166534' : '#64748b';
    strengthCriteria[3].style.color = criteria[3] ? '#166534' : '#64748b';
    strengthCriteria[4].style.color = criteria[4] ? '#166534' : '#64748b';
});
```
Check each rule from spec Section 8 against this code:
- Rule 1: `strength` is an integer count 0–5 via `criteria.filter(Boolean).length` — matches.
- Rule 2: length check is `>= 8`, no upper bound — matches.
- Rule 3–6: regexes match the exact character classes specified (`[a-z]`, `[A-Z]`, `\d`, and the literal special-character set) — matches.
- Rule 7: fill width recomputed from scratch every `input` event via `(strength / 5) * 100` — matches.
- Rule 8: empty string yields all-`false` criteria and `0%` width — matches (regex/length checks naturally evaluate to `false`/fail on `""`).
- Rule 9: function only mutates `strengthFill.style.width` and the 5 `li.style.color` values; no form submission, network call, or storage write occurs — matches.
- Rule 10: this listener is entirely separate from the `form.addEventListener('submit', ...)` password-match handler; it does not call `preventDefault()` or reference the submit button — matches.
- FS-07: for pathological input (very long strings, whitespace-only, unicode), `.length`, `.test()` do not throw — confirm no exceptions occur (manual test, see Phase 6 / T15).

**Verification steps addressed:**
- FS-01 through FS-06
- AC-02, AC-03, AC-04, AC-06, AC-08, AC-09 (independence from match-validation handler)
- Business Logic Rules 1–10
- Section 6 API Contract (function behavior, though implemented as an inline closure rather than a named top-level function — see Implementation Notes)

## Phase 3: Verify CSS Styling

**Files to inspect (no changes anticipated):**
- `frontend/static/css/styles.css` (rules under `/* Password Strength Meter */`, approx. lines 322–371)

**Verification:**
Confirm the following selectors exist and produce the required visuals:
```css
.password-strength-meter { margin-top: 20px; font-size: 0.875rem; color: var(--color-text-secondary); }
.password-strength-meter label { display: block; margin-bottom: 4px; font-weight: 600; }
.strength-bar { width: 100%; height: 8px; background-color: #e2e8f0; border-radius: 4px; overflow: hidden; margin-bottom: 8px; }
.strength-fill { height: 100%; background-color: var(--color-brand-primary); width: 0%; transition: width 0.2s ease; }
.strength-criteria { list-style: none; padding: 0; margin-top: 8px; }
.strength-criteria li { margin-bottom: 4px; display: flex; align-items: center; font-size: 0.8125rem; }
```
Check:
- `.strength-fill` width starts at `0%` and transitions smoothly (UX-05: no layout-shifting side effects, only width/color changes).
- `.password-strength-meter` and `.strength-fill` use theme-aware CSS custom properties (`var(--color-text-secondary)`, `var(--color-brand-primary)`), so they adapt automatically when `data-theme="dark"` is set on `<html>` — matches UX-04.
- No JavaScript or CSS references a font, layout, or z-index that would visually displace the submit button or other form fields as strength changes.

**Verification steps addressed:**
- UX-02, UX-03 (partial — brand color adapts via CSS var), UX-05
- AC-12 (partial — see Phase 4 for the remaining gap)

## Phase 4: Theme-Contrast Follow-Up (Conditional)

**Files that may require changes:**
- `frontend/static/css/styles.css` (only if contrast check fails)
- `frontend/templates/signup.html` (only if inline JS colors are replaced with CSS classes)

**Finding:**
The per-criterion met/unmet colors are set via inline JS (`'#166534'` green / `'#64748b'` gray) rather than theme-aware CSS variables, and `.strength-bar`'s track background (`#e2e8f0`, a light gray) is also hardcoded rather than themed. The spec (Section 5, UX-03) explicitly permits keeping this existing inline-style convention "unless superseded by a themed CSS class," so this is not a spec violation by default — but AC-12 requires legibility in both themes, so this must be **manually verified**, not assumed.

**Verification procedure:**
1. Load `/signup`, toggle to dark theme via the existing theme toggle.
2. Type a password satisfying some but not all criteria (e.g., `"abc12345"`).
3. Visually inspect: is `#166534` (dark green) legible against the dark theme's surface background (`--color-bg-surface: #1e293b`)? Is `#64748b` (muted gray) legible against the same background? Is the `#e2e8f0` light-gray track visually distinct from the surrounding dark surface (it will render as a light rectangle on a dark page — check this is an acceptable/intentional look rather than a jarring one)?

**Conditional remediation (only if the above check fails):**
If contrast or visual coherence is inadequate in dark theme, replace the inline `style.color` assignments with a CSS class toggle (e.g., add/remove a `.met` class per `<li>`) and define `.strength-criteria li.met` / default colors as theme-aware custom properties in `styles.css`, following the same `:root[data-theme="dark"]` override pattern already used elsewhere in the file (see `dark-mode-toggle.md` / `dark-mode-toggle-plan.md` for the established convention). Similarly, consider theming `.strength-bar`'s track color via a custom property if it fails the visual check.

**Verification steps addressed:**
- AC-12, UX-04 (remainder)
- T12 (from spec Section 11)

## Phase 5: Verify Server-Side Non-Enforcement

**Files to inspect (no changes anticipated):**
- `backend/app/api/routes/auth.py` (`signup_post`)
- `backend/app/services/auth_service.py` (`signup`)

**Verification:**
Confirm `signup()` performs no password-strength-related validation or rejection — it must accept any password value (including a single character) that currently passes today, exactly as before this feature. Confirm no new request parameters, headers, or fields related to strength are read from the `POST /signup` form submission.

**Verification steps addressed:**
- AC-10, Business Logic Rules 11–12
- T10

## Phase 6: Manual Test Execution

**Files to inspect:** none (test execution only, per spec Section 11, tests T1–T15)

**Procedure:**
Execute each test case from `.claude/specs/password-str-meter.md` Section 11 against the running application (`python backend/app/main.py`, browse to `http://localhost:3001/signup`):

1. **T1** — Load `/signup`; confirm `0%` fill and all-unmet criteria.
2. **T2** — Type one character; confirm immediate (no reload) update.
3. **T3** — Step through passwords satisfying 0/1/2/3/4/5 criteria; confirm fill widths `0/20/40/60/80/100%`.
4. **T4** — Confirm each criterion evaluates independently and correctly per its regex.
5. **T5** — Confirm met vs. unmet color distinction is simultaneous and per-item accurate.
6. **T6** — Clear a strong password back to empty; confirm reset to initial state.
7. **T7** — Submit with a weak password (matching confirm field, valid username/email); confirm submission is not blocked by strength.
8. **T8** — Watch Network tab while typing; confirm no new requests fire.
9. **T9** — Confirm mismatched password/confirm-password still blocks submission via the existing, separate handler, regardless of strength meter state.
10. **T10** — Submit a weak password via `POST /signup` directly; confirm server accepts it (see Phase 5).
11. **T11** — Load `/login`; confirm no strength meter elements are present.
12. **T12** — Repeat T3/T5 with dark theme active (see Phase 4).
13. **T13** — Programmatically dispatch an `input` event with an empty value; confirm no exceptions and state matches T1.
14. **T14** — Type into the field while monitoring `localStorage` and network activity; confirm no new keys/requests and that `password` input's own value is untouched by the handler.
15. **T15** — Try a very long string (500+ chars), whitespace-only string, and a string with unicode/emoji; confirm no JavaScript errors and a well-defined (non-crashing) resulting state.

**Verification steps addressed:**
- All of AC-01 through AC-12
- All of T1–T15

## Phase 7: Vulnerability Preservation Verification

**Files to verify (NO CHANGES MADE):**
- All backend files (preserve SQL Injection, weak session secret, exposed `/download/db`, no rate limiting, no CSRF protection)
- All frontend templates (preserve Stored XSS via `{{username}}` substitution on `/welcome`, Reflected XSS in `/search`)
- `backend/app/core/security.py` / `backend/app/services/auth_service.py` bcrypt flow (unaffected by this feature — see spec Section 9)

**Verification:**
- Confirm no changes were made anywhere outside the scope discussed in Phases 1–4 (i.e., `git status` shows no unexpected diffs, or, if Phase 4 remediation was needed, diffs are limited to `frontend/static/css/styles.css` and/or `frontend/templates/signup.html`).
- Spot-check that SQL Injection (`' OR '1'='1` on `/login`), Stored XSS (`<script>alert(1)</script>` as username), and Reflected XSS (`/search?query=<script>alert(1)</script>`) remain exploitable exactly as before.

**Verification steps addressed:**
- AC-10 (server-side policy absence), Out of Scope Section 10 (no vulnerability-fixing side effects)

## Implementation Notes

1. **No source code changes are expected** as the outcome of this plan under the normal path — the feature described in the spec is already implemented in `frontend/templates/signup.html` and `frontend/static/css/styles.css`. This plan's purpose is to formally verify that existing implementation against the newly-written spec, and to document the one identified area (dark-theme contrast of hardcoded inline colors, Phase 4) that requires a manual check before being considered fully compliant with AC-12.
2. **Naming discrepancy (non-blocking)**: Spec Section 6 describes the logic as a standalone function `updatePasswordStrength(password)`. The actual implementation is an anonymous function passed directly to `addEventListener('input', ...)`. This is functionally equivalent and satisfies every behavioral requirement (Sections 4, 8) — refactoring it into a named function is optional polish, not required for spec compliance, and should only be done if requested separately (to avoid unnecessary churn on working code per the project's "don't refactor beyond what's asked" norm).
3. **If Phase 4 requires remediation**, follow the existing `:root[data-theme="dark"]` CSS custom-property override convention already established by the dark mode toggle feature (`dark-mode-toggle-plan.md` Phase 1) rather than introducing a new theming mechanism.
4. **Vulnerability Preservation**: Zero changes anticipated to backend logic or any of the other 7 intentional vulnerabilities. If Phase 4 remediation is needed, it is strictly a CSS/markup styling change with no security-relevant effect.
5. **No new files, dependencies, or database changes** are introduced by this plan, consistent with spec Sections 7 and 9.

This plan, in the expected (no-remediation-needed) case, results in **zero file changes** — it is a verification-only plan. In the conditional case where Phase 4 surfaces a real contrast defect, changes are limited to:
- `frontend/static/css/styles.css`
- `frontend/templates/signup.html` (only if inline colors are migrated to CSS classes)

No backend files, and no files related to the other 7 intentional vulnerabilities, are touched under any path of this plan.
