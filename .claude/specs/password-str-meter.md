# Software Specification Document

## 1. Feature Overview

This feature adds a real-time, client-side password strength meter to the signup page (`/signup`) of the vulnerable web application. As the user types into the password field, the meter visually indicates how well the password satisfies five strength criteria (minimum length, lowercase letter, uppercase letter, digit, special character) via a fill bar and a checklist of criteria that highlight as they are met. The meter is purely advisory: it provides feedback to the user but does not block form submission, does not perform any server-side validation, and does not alter the intentional vulnerabilities of the application (SQL Injection, XSS, weak session secret, absence of rate limiting, absence of CSRF protection, and — notably — no enforced password policy on the backend). This is a UX/education enhancement layered on top of the existing signup flow described in `app-foundation.md` and must not interfere with the `hash_password`/`verify_password` bcrypt flow described in `bcrypt-password-hashing.md`.

## 2. User Story

As a new user registering for the security lab platform, I want to see immediate visual feedback on how strong my chosen password is while I type it, so that I can choose a stronger password before submitting the signup form, without being forced to comply with any specific policy.

## 3. Acceptance Criteria

- **AC-01**: On page load, the strength meter fill bar is empty (0% width) and all criteria list items are rendered in the "unmet" (neutral/gray) visual state.
- **AC-02**: As the user types in the password field, the meter updates on every `input` event (no submit or blur required).
- **AC-03**: The meter fill bar width reflects the number of satisfied criteria out of 5, in even increments (0%, 20%, 40%, 60%, 80%, 100%).
- **AC-04**: Each of the 5 criteria is evaluated independently and reflected individually in the checklist:
  - Minimum length: password length ≥ 8 characters
  - Lowercase letter: contains at least one `[a-z]`
  - Uppercase letter: contains at least one `[A-Z]`
  - Digit: contains at least one `[0-9]`
  - Special character: contains at least one character from the set `!@#$%^&*()_+-=[]{};':"\|,.<>/?`
- **AC-05**: A satisfied criterion is visually distinguished (e.g., "met" color) from an unsatisfied criterion (e.g., neutral/gray color) in the checklist.
- **AC-06**: Clearing the password field (empty string) resets the meter to the same state as AC-01 (0% fill, all criteria unmet).
- **AC-07**: The meter is purely client-side and advisory — it does not disable, block, or prevent the "Create Account" submit button from being clicked or the form from being submitted, regardless of strength.
- **AC-08**: No new network requests are made as part of the strength evaluation (all computation happens client-side in the browser, synchronously, on each keystroke).
- **AC-09**: The existing password-confirmation-match validation (`password` vs `confirm_password` fields) continues to function unchanged and independently of the strength meter.
- **AC-10**: The server-side `/signup` endpoint and `signup()` service function are not modified to enforce or reject based on password strength; any password (including weak ones) that currently passes signup continues to be accepted, preserving the absence of server-side password policy enforcement.
- **AC-11**: The strength meter markup and script are scoped to the signup page only and do not appear on or affect the login page.
- **AC-12**: The feature must render correctly and be visible/legible in both light and dark theme states (the app supports a theme toggle via `data-theme` attribute).

## 4. Functional Specifications

- **FS-01**: A password strength evaluation runs on every `input` event fired by the `#password` field.
- **FS-02**: The evaluation computes a `strength` score as the count of satisfied criteria (integer, 0–5) out of the 5 criteria defined in AC-04.
- **FS-03**: The visual fill bar's width is set to `(strength / 5) * 100` percent.
- **FS-04**: Each criterion's corresponding list item is updated to a "met" or "unmet" visual state based on its individual boolean result — independent of the aggregate score used for the fill bar.
- **FS-05**: Evaluation logic uses only client-side JavaScript (no server round-trip, no external library dependency).
- **FS-06**: The feature does not persist strength state across page loads; state exists only in the DOM for the current session of interacting with the form.
- **FS-07**: The feature must not throw JavaScript errors for edge-case inputs, including empty string, strings containing only whitespace, unicode characters, or very long strings (see Business Logic rules for exact behavior).

## 5. UI/UX Requirements

- **UX-01**: The meter is positioned within the signup form, directly below the "Confirm Password" field group and above the submit button.
- **UX-02**: The meter consists of two visual elements:
  1. A horizontal fill bar (a container with a fixed-width track and an inner fill element whose width animates/updates based on strength).
  2. A checklist (`<ul>`) of the 5 criteria as plain-language labels: "8+ characters", "Lowercase letter", "Uppercase letter", "Digit", "Special character".
- **UX-03**: Met criteria are shown in a distinct "positive" color (e.g., green, consistent with existing success-state colors used elsewhere in the app), and unmet criteria in a neutral/muted color (e.g., gray), matching the existing inline style convention already used in this codebase (`#166534` for met, `#64748b` for unmet) unless superseded by a themed CSS class.
- **UX-04**: The component must be legible and correctly styled under both `data-theme="light"` and `data-theme="dark"` (the app's existing theme system, toggled via `#theme-toggle` and persisted to `localStorage`).
- **UX-05**: The meter must not shift or reflow other form elements unexpectedly as strength changes (only the fill bar's width and text colors change — no layout-affecting size changes to the checklist itself).
- **UX-06**: No numeric score, percentage, or strength label (e.g., "Weak"/"Strong") text is required to be displayed; the visual fill bar and per-criterion coloring are sufficient. (A textual strength label is optional/out of scope — see Section 10.)
- **UX-07**: The meter is purely advisory in tone; no error/blocking messaging (e.g., red text, disabled button) is shown regardless of how weak the password is.

## 6. API Contract (exact signature)

This is a client-side-only feature. There is no new backend endpoint, and no new Python function signature is introduced. The relevant client-side JavaScript function contract (to be attached as an event handler on `#password`'s `input` event, consistent with existing code in `frontend/templates/signup.html`) is:

```javascript
/**
 * Evaluates password strength against 5 fixed criteria and updates
 * the strength-fill bar width and per-criterion checklist coloring.
 * Pure function of `password`; has side effects only on the DOM
 * elements passed in (or module-scoped element references).
 *
 * @param {string} password - current value of the #password input
 * @returns {void}
 */
function updatePasswordStrength(password) { /* ... */ }
```

Existing DOM element IDs this function depends on (already present in `frontend/templates/signup.html`) and must continue to reference exactly:

- `#password` — the password `<input>` element (event source)
- `#strength-fill` — the inner fill `<div>` whose `style.width` is set
- `#strength-criteria` — the `<ul>` whose `<li>` children (in fixed order: length, lowercase, uppercase, digit, special) get their `style.color` set

No changes to any FastAPI route (`backend/app/api/routes/auth.py`) or service function (`backend/app/services/auth_service.py`) signatures are part of this feature.

## 7. Data Requirements

- No new database tables, columns, or migrations are required.
- No password strength score, metadata, or evaluation result is persisted to the `users` table or any other storage.
- No data is sent to the server as part of strength evaluation; the `password` field submitted via the existing `POST /signup` form remains the only password-related data transmitted, unchanged in format.
- No cookies, session variables, or localStorage keys are introduced by this feature (distinct from the existing unrelated `theme` localStorage key used by the theme toggle).

## 8. Business Logic (numbered rules)

1. Strength is computed as an integer count in the closed range `[0, 5]`, one point per satisfied criterion; there is no partial credit or weighting between criteria.
2. Criterion 1 (length) is satisfied when `password.length >= 8`. There is no upper bound; arbitrarily long passwords remain evaluated correctly for this criterion (still `true`) and for all other criteria.
3. Criterion 2 (lowercase) is satisfied when the password contains at least one character matching `[a-z]` (ASCII lowercase only; this matches the app's existing convention and is not required to support unicode letter classes).
4. Criterion 3 (uppercase) is satisfied when the password contains at least one character matching `[A-Z]` (ASCII uppercase only).
5. Criterion 4 (digit) is satisfied when the password contains at least one character matching `[0-9]`.
6. Criterion 5 (special character) is satisfied when the password contains at least one character from the literal set `! @ # $ % ^ & * ( ) _ + - = [ ] { } ; ' : " \ | , . < > / ?`.
7. The fill bar width is always `(count_of_satisfied_criteria / 5) * 100` percent, recomputed from scratch on every `input` event (no incremental/diff-based updates).
8. When `password === ""` (empty string, e.g., on page load or after the user clears the field), all 5 criteria evaluate to `false` and the fill bar width is `0%`.
9. The strength evaluation and DOM update must be idempotent and side-effect-free beyond updating the fill width and the 5 criteria colors — it must not mutate `password`, submit the form, make network requests, or write to storage.
10. The strength meter's evaluation result has no bearing on whether the "Create Account" button is enabled, clickable, or whether the form's `submit` event proceeds — that logic is governed solely by the existing, separate password-match validation (`password` vs `confirm_password`) already implemented in `frontend/templates/signup.html`.
11. The strength meter and its underlying criteria are not enforced or re-validated on the server; `backend/app/services/auth_service.py`'s `signup()` function must continue to accept any password value that currently passes existing (non-strength-related) validation, regardless of computed client-side strength.
12. Rule 11 is an intentional and required behavior of this educational application — the absence of a server-side password policy is not a bug to be fixed as part of this feature.

## 9. Dependencies

- No new third-party libraries, npm packages, or Python packages are required. The feature uses only vanilla JavaScript (`RegExp.prototype.test`, DOM APIs `addEventListener`, `style.width`, `style.color`), consistent with the codebase's existing "Vanilla JavaScript" frontend stack per `CLAUDE.md`.
- Depends on the existing signup page markup and script structure in `frontend/templates/signup.html` (specifically the `#password`, `#strength-fill`, and `#strength-criteria` elements/IDs already present).
- Depends on the existing theme system (`data-theme` attribute, `frontend/static/css/styles.css`) only insofar as styling must remain legible in both themes; no changes to the theme system itself are required.
- No dependency on `backend/app/core/security.py`, `bcrypt`, or any server-side hashing/verification logic — this feature is entirely independent of Vulnerability #5's fix.

## 10. Out of Scope

- Enforcing a minimum password strength on the server (server-side validation/rejection of weak passwords) — the app intentionally has no such policy.
- Disabling or graying out the "Create Account" submit button based on strength.
- Displaying a textual strength label (e.g., "Weak", "Medium", "Strong") — only the fill bar and per-criterion checklist are required.
- Blocklist/dictionary checks (e.g., rejecting "password123", checking against breached-password lists such as Have I Been Pwned).
- Any change to the `/login` page or login flow.
- Any change to password hashing, verification, or storage (`hash_password`/`verify_password`, bcrypt work factor) — covered separately by `bcrypt-password-hashing.md`.
- Any change to the other 7 intentional vulnerabilities (SQL Injection, Stored XSS, Reflected XSS, Session Hijacking via weak secret, Exposed Database endpoint, No Rate Limiting, CSRF) — all must remain exactly as currently implemented.
- Internationalization/localization of criterion labels.
- Accessibility enhancements beyond basic color-based state changes (e.g., ARIA live region announcements) unless explicitly requested in a future spec.
- Automated/unit test infrastructure setup if none currently exists for frontend JavaScript in this repo — manual verification steps are sufficient per Section 11.

## 11. Testing Requirements

| Test ID | Corresponding AC | Scenario | Steps | Expected Result |
|---------|------------------|----------|-------|------------------|
| T1 | AC-01 | Initial page state | Load `/signup` in a browser | Fill bar width is `0%`; all 5 criteria list items are in the neutral/unmet color |
| T2 | AC-02 | Live update on typing | Type a single character into `#password` | Meter updates immediately (no page reload, no blur/submit needed) |
| T3 | AC-03, Rule 7 | Fill bar increments | Type passwords satisfying 0, 1, 2, 3, 4, and 5 criteria respectively (e.g., `""`, `"a"`, `"a1"`, `"aA1"`, `"aA1!"`, `"aA1!aaaa"`) | Fill bar width is `0%, 20%, 40%, 60%, 80%, 100%` respectively |
| T4 | AC-04, Rules 2-6 | Individual criteria correctness | Type `"short"` (no upper/digit/special, <8 chars); then `"longenough"` (≥8, lowercase only); then `"Longenough1"`; then `"Longenough1!"` | Each criterion (length, lowercase, uppercase, digit, special) independently reflects `true`/`false` matching the regex definitions in Rules 2-6 |
| T5 | AC-05 | Visual met/unmet distinction | With a partially-satisfying password (e.g., `"abc12345"`: length + lowercase + digit met, upper + special unmet) | Met criteria show the "met" color; unmet criteria show the neutral color, simultaneously and correctly per-item |
| T6 | AC-06 | Reset on empty | Type a strong password, then delete all characters back to empty string | Fill bar returns to `0%` and all criteria return to unmet state, identical to T1 |
| T7 | AC-07 | Submission not blocked by weak password | Enter a weak password (e.g., `"a"`) satisfying 0-1 criteria, matching confirm-password field, and valid username/email | Form submits successfully (assuming password match validation passes); "Create Account" button is not disabled and click/submit is not intercepted due to strength |
| T8 | AC-08 | No network calls | Open browser dev tools Network tab, type into `#password` | No new XHR/fetch requests appear as a result of typing (only the eventual form POST on submit, if triggered) |
| T9 | AC-09 | Password match validation unaffected | Enter mismatched `password`/`confirm_password` values regardless of strength meter state, then submit | Existing `#password-error` "Passwords do not match" message still displays and submission is still prevented, exactly as before this feature |
| T10 | AC-10, Rule 11 | Server accepts weak passwords | Submit signup form with a weak password (e.g., `"a"`) and matching confirm field via `POST /signup` | Registration succeeds (per existing `signup()` logic) and does not return a strength-related error; response/behavior identical to current `signup()` behavior for any accepted password |
| T11 | AC-11 | Scoped to signup only | Load `/login` page | No strength meter markup, `#strength-fill`, or `#strength-criteria` elements are present or referenced |
| T12 | AC-12 | Theme legibility | Toggle theme to dark via `#theme-toggle`, then repeat T3 and T5 | Fill bar and criteria list remain legible and correctly colored (met vs. unmet) under `data-theme="dark"` |
| T13 | Rule 8 | Empty-string safety | Programmatically set `#password` value to `""` and dispatch an `input` event | No JavaScript exceptions thrown; state matches T1 |
| T14 | Rule 9 | No unintended side effects | Type into `#password` while monitoring `localStorage` and network calls | No new `localStorage` keys are written, no form auto-submission occurs, `password` input value itself is unchanged by the evaluation function |
| T15 | FS-07 | Edge-case input robustness | Type a very long string (500+ characters), a string of only whitespace, and a string containing unicode/emoji characters | No JavaScript errors thrown in any case; fill bar and criteria update to some well-defined (non-crashing) state consistent with Rules 2-6 applied to those characters |