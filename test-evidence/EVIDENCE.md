# SIKPRO V1 verification evidence

## Evidence summary

| Status | Records |
|---|---:|
| PASS | 45 |
| FAIL | 7 |
| BLOCKED | 7 |
| NOT RUN | 3 |
| **Total** | **62** |

Counts include initial failures and blocked runs separately from passing reruns. The original `CHART-004 — NOT RUN` record is retained as the pre-QA baseline; it is followed by per-family visual reruns. R and S remain unavailable under the application's maintenance placeholders. Full Windows common file-dialog interaction and non-100% DPI verification remain unresolved.

## Environment

`ENV-1` for the Tk GUI records: Windows 10 build 26300 (64-bit), Python 3.11.9, Tk 8.6, two monitors: `(0,0)-(1536,864)` and `(1920,0)-(3280,768)`, work areas `(48,0)-(1536,864)` and `(1968,0)-(3280,768)`. Both monitors report 96 DPI (100% scaling); a non-100% setting was not tested. The GUI smoke tests created real Tk windows and widgets and used real Tk event dispatch (`event_generate`) and `update`; the scripts drove controls programmatically. No screenshot of the desktop was captured. Actual app-rendered chart figures and Fishbone exports were saved and visually inspected.

`ENV-2` means the same Windows/Python environment without a display dependency; used for compile, test, and diff commands.

## Automated command record

| Command | Exit | Observed output |
|---|---:|---|
| `python -m compileall -q core logic models project_managers ui tests test-evidence/chart_visual_smoke.py test-evidence/popup_smoke.py test-evidence/dpi_probe.py test-evidence/native_dialog_probe.py` | 0 | Completed with no syntax errors. |
| `python -m unittest tests.test_fishbone_editor_gui tests.test_theme -v` | 0 (final) | 8 tests passed, including Tk keyboard tests. See `FISH-THEME-targeted-tests.txt`. |
| `python -m unittest discover -s tests -v` | 0 | 50 tests passed. See `REG-001-test-output.txt`. |
| `git diff --check` | 0 | No whitespace errors. |
| `python test-evidence/gui_smoke.py` | 0 (final) | Actual Tk workflow assertions passed; see `gui-smoke-output.txt`. |
| `python test-evidence/export_smoke.py` | 0 (final) | Fishbone PNG/PDF exports passed in Light and Dark; see `export-smoke-output.txt`. |
| `python test-evidence/defect_export_smoke.py` | 0 | Defect Concentration PNG/PDF exports passed; see `defect-export-smoke-output.txt`. |
| `$env:APPDATA='test-evidence\qa-appdata'; python test-evidence/chart_visual_smoke.py` | 0 (final) | Nine available live chart families rendered and resized in Light/Dark; see `chart-visual-output.txt` and `chart-visual/`. |
| `$env:APPDATA='test-evidence\qa-appdata'; python test-evidence/popup_smoke.py` | 0 (final) | Twelve reachable popup/config surfaces opened, themed, closed, and reopened; see `popup-smoke-output.txt`. |
| `python test-evidence/dpi_probe.py` | 0 | Two monitors enumerated; both 96 DPI (100%); see `dpi-probe-output.txt`. |
| `$env:APPDATA='test-evidence\qa-appdata'; python test-evidence/native_dialog_probe.py` | 0 (probe only) | No native Open dialog appeared in the visible-window inventory; this is evidence for BLOCKED, not a passing file-dialog test. |

## Individual records

### FISH-KEY-001 — PASS

| Field | Record |
|---|---|
| Feature | Fishbone cause text editor |
| Objective | Backspace deletes the character before the insertion point. |
| Preconditions | Real Tk `Text` editor open with `abcdef`, insertion point at `1.3`; ENV-1. |
| Test procedure | `python -m unittest tests.test_fishbone_editor_gui.FishboneEditorKeyboardGuiTests.test_fish_key_001_backspace_deletes_before_caret -v`; generate `<KeyPress-BackSpace>`. |
| Expected result | `c` is removed; other characters remain. |
| Actual result | Text became `abdef`. |
| Status | PASS |
| Evidence | Actual Tk assertion; `FISH-THEME-targeted-tests.txt`. |
| Environment | ENV-1 |
| Notes | Actual Tk widget, not a mocked editor. |

### FISH-KEY-002 — PASS

| Field | Record |
|---|---|
| Feature | Fishbone cause text editor |
| Objective | Delete removes the character after the insertion point. |
| Preconditions | Real Tk `Text` editor open with `abcdef`, insertion point at `1.3`; ENV-1. |
| Test procedure | Run the targeted test method and generate `<KeyPress-Delete>`. |
| Expected result | `d` is removed; preceding text remains. |
| Actual result | Text became `abcef`. |
| Status | PASS |
| Evidence | Actual Tk assertion; `FISH-THEME-targeted-tests.txt`. |
| Environment | ENV-1 |
| Notes | Verified on the selected text widget. |

### FISH-KEY-003 — PASS (verified rerun)

| Field | Record |
|---|---|
| Feature | Fishbone cause text editor |
| Objective | Cursor movement, Home/End, and editing in the middle of text work. |
| Preconditions | Real Tk `Text` editor with `abcdef`; ENV-1. |
| Test procedure | Generate Right, Home, type `X`, then End; inspect text and insertion index. |
| Expected result | Mid-string input is inserted without replacing the rest; End reaches the text end. |
| Actual result | Text became `Xabcdef`; End index was `1.7`, the correct end position for seven characters. |
| Status | PASS |
| Evidence | Actual Tk assertion; `FISH-THEME-targeted-tests.txt`. |
| Environment | ENV-1 |
| Notes | Initial run below failed only because the test incorrectly expected `1.8`; it was corrected and rerun. |

### FISH-KEY-003 — FAIL (initial run)

| Field | Record |
|---|---|
| Feature | Fishbone cause text editor test assertion |
| Objective | Verify that End reaches the text end. |
| Preconditions | Same actual Tk editor as the verified rerun; ENV-1. |
| Test procedure | Initial `python -m unittest tests.test_fishbone_editor_gui tests.test_theme -v`. |
| Expected result | The original assertion expected insertion index `1.8`. |
| Actual result | Tk returned `1.7`; the text was seven characters long (`Xabcdef`). |
| Status | FAIL |
| Evidence | Initial unittest output in the execution record: `AssertionError: '1.7' != '1.8'`. |
| Environment | ENV-1 |
| Notes | Incorrect test expectation, not an editing defect; corrected expectation and rerun passed. The original failure is retained here. |

### FISH-KEY-004 — PASS

| Field | Record |
|---|---|
| Feature | Fishbone cause text editor |
| Objective | Ctrl+A selects all; Text undo/redo works; editor shortcuts do not reach application shortcuts. |
| Preconditions | Real Tk `Text` editor with root Ctrl+Z/Ctrl+Y handlers bound; ENV-1. |
| Test procedure | Generate Ctrl+A, replace selection, Ctrl+Z, Ctrl+Y; inspect selected range, text, and root shortcut counters. |
| Expected result | Entire cause is selected; Text undo/redo changes its own contents; root shortcut counters stay empty. |
| Actual result | All assertions passed; no application shortcut was invoked. |
| Status | PASS |
| Evidence | `FISH-THEME-targeted-tests.txt`. |
| Environment | ENV-1 |
| Notes | Tk Text's built-in undo stack is used. |

### FISH-KEY-005 — PASS

| Field | Record |
|---|---|
| Feature | Fishbone cause editor isolation |
| Objective | Editing keys do not trigger diagram delete/save actions. |
| Preconditions | Modal cause editor open; callbacks spy on save; ENV-1. |
| Test procedure | Generate Backspace and Delete while editor owns focus; inspect dialog and callback state. |
| Expected result | Editor remains open and no save/delete callback runs. |
| Actual result | Dialog remained open; callback list was empty. |
| Status | PASS |
| Evidence | `FISH-THEME-targeted-tests.txt`. |
| Environment | ENV-1 |
| Notes | Direct test of event isolation; Fishbone model CRUD/reorder behavior is also covered by `test_quality_tools.py`. |

### FISH-KEY-006 — PASS

| Field | Record |
|---|---|
| Feature | Fishbone editor confirmation and cancellation |
| Objective | Confirm Enter, Escape, focus loss, and Ctrl+Enter behavior. |
| Preconditions | Actual Tk cause editor open; ENV-1. |
| Test procedure | Generate Enter; move focus to root; inspect dialog and text; generate Escape; open a second editor and generate Ctrl+Enter. |
| Expected result | Enter inserts newline; focus loss preserves open dialog/text; Escape cancels without saving; Ctrl+Enter saves and closes. |
| Actual result | All four assertions passed. |
| Status | PASS |
| Evidence | `FISH-THEME-targeted-tests.txt`, test method `test_enter_escape_focus_loss_and_ctrl_enter_confirmation`. |
| Environment | ENV-1 |
| Notes | — |

### FISH-WORKFLOW-001 — PASS

| Field | Record |
|---|---|
| Feature | Fishbone end-to-end cause workflow |
| Objective | Exercise effect entry, cause edit, reorder, category assignment, and delete through the live workspace. |
| Preconditions | Fishbone workspace open with a real model and listbox; ENV-1. |
| Test procedure | Change effect Entry; edit a cause in the Text dialog; add a second cause; select/reorder it; select a category in the real picker; delete it. |
| Expected result | Effect and edited text persist; cause order/category change; selected cause deletes without affecting the other cause. |
| Actual result | Effect `Seal leakage`; edited cause persisted; second cause reordered, moved to second category, and deleted. |
| Status | PASS |
| Evidence | Assertions and `FISHBONE_WORKFLOW` output in `gui-smoke-output.txt`. |
| Environment | ENV-1 |
| Notes | Uses real Tk widgets and the actual category picker; test schedules the selection in the modal picker. |

### THEME-001 — PASS

| Field | Record |
|---|---|
| Feature | Light-to-Dark application theme |
| Objective | Switching to Dark updates visible application surfaces and controls. |
| Preconditions | MainPage and Tk widgets initialized; ENV-1. |
| Test procedure | GUI smoke script switches to Dark and asserts root, context panel, selected navigation, and tksheet colors against the Dark palette. |
| Expected result | Window, panels, selection, and table use semantic Dark colors. |
| Actual result | Root `#171c24`, panel `#1d2530`/`#222a35`, selected nav `#304766`, tksheet input `#18212b`; assertions passed. |
| Status | PASS |
| Evidence | `gui_smoke.py`, `gui-smoke-output.txt`. |
| Environment | ENV-1 |
| Notes | Also switched repeatedly during active Fishbone and chart workflows. |

### THEME-002 — PASS

| Field | Record |
|---|---|
| Feature | Dark-to-Light application theme |
| Objective | Switching back to Light restores Light styling. |
| Preconditions | Same main window and active Fishbone editor/quality views; ENV-1. |
| Test procedure | Switch Dark → Light and inspect root, cause editor, figure, and quality tool surfaces. |
| Expected result | Light surfaces return without recreating the app or losing entered data. |
| Actual result | Root `#f3f6fa`, editor/input and plot backgrounds returned to Light; assertions passed. |
| Status | PASS |
| Evidence | `gui-smoke-output.txt`, `export-smoke-output.txt`. |
| Environment | ENV-1 |
| Notes | Light and Dark PNG/PDF exports both generated. |

### THEME-003 — PASS

| Field | Record |
|---|---|
| Feature | Existing and newly opened dialogs/workspaces |
| Objective | Existing dialogs update and newly opened windows inherit the active theme. |
| Preconditions | Cause editor opened before switching; Help workspace and a Toplevel opened after switching; ENV-1. |
| Test procedure | Change theme while the cause editor is open; then open Help and a new Toplevel in Dark. |
| Expected result | Existing editor updates without losing its text; new windows use Dark colors. |
| Actual result | Cause text survived; new Toplevel background `#171c24`; Help text `#18212b`, heading tag `#78aaff`. |
| Status | PASS |
| Evidence | `gui-smoke-output.txt`. |
| Environment | ENV-1 |
| Notes | Generic popup behavior and Help were checked; every individual chart configuration dialog was not visually opened. |

### THEME-004 — PASS (verified restart)

| Field | Record |
|---|---|
| Feature | Theme persistence |
| Objective | Dark preference survives application process restart. |
| Preconditions | Isolated temporary `APPDATA`; two independent Python GUI processes; ENV-1. |
| Test procedure | First process initializes MainPage and selects Dark; second process creates a new MainPage and prints its loaded mode. |
| Expected result | Second process starts in Dark. |
| Actual result | Both subprocess exit codes were 0; second printed `dark`; settings JSON contained `{"theme":"dark"}`. |
| Status | PASS |
| Evidence | `gui_smoke.py`, `gui-smoke-output.txt`; temporary settings were isolated from user settings. |
| Environment | ENV-1 |
| Notes | On Windows, `os.replace` was denied in the isolated environment; the settings writer now falls back to a direct write and the restart check passes. |

### THEME-004 — FAIL (initial run)

| Field | Record |
|---|---|
| Feature | Theme preference persistence |
| Objective | Save Dark and reload it. |
| Preconditions | Settings file in a temporary Windows directory; ENV-1. |
| Test procedure | Initial targeted theme persistence unit test called `save()` and reloaded the file. |
| Expected result | Reloaded manager reports Dark. |
| Actual result | Save could not replace the temporary file (`WinError 5: Access is denied`); file remained without the theme and reload defaulted to Light. |
| Status | FAIL |
| Evidence | Initial test output; follow-up direct reproduction printed the `WinError 5` and `last_persistence_error`. |
| Environment | ENV-1 |
| Notes | Root cause was Windows ACL behavior with `os.replace`; fallback write added; final unit test and process restart passed. Original failure retained. |

### THEME-005 — PASS

| Field | Record |
|---|---|
| Feature | Theme switching with unsaved input and analysis |
| Objective | Preserve cause text, sheet input, and current analysis during theme changes. |
| Preconditions | Unsaved Fishbone edit text and generated I-MR analysis in the live app; ENV-1. |
| Test procedure | Toggle themes repeatedly while cause editor is open and after generating a chart; compare text, sheet data, and Analysis object. |
| Expected result | No values/results are lost or recalculated. |
| Actual result | Pending cause text remained identical, saved cause updated correctly, sheet snapshot matched, and the same analysis object remained present. |
| Status | PASS |
| Evidence | Assertions in `gui_smoke.py`; `gui-smoke-output.txt`. |
| Environment | ENV-1 |
| Notes | The same analysis object/data remained intact; calculations were not modified by the theme manager. |

### I18N-001 — PASS

| Field | Record |
|---|---|
| Feature | Indonesian-Light localization |
| Objective | Indonesian labels remain active in Light mode. |
| Preconditions | MainPage initialized; ENV-1. |
| Test procedure | Set language to Indonesian, set theme to Light, inspect workspace label and theme mode. |
| Expected result | Indonesian data input label and Light colors. |
| Actual result | `Masukan Data`, `#f3f6fa`; assertions passed. |
| Status | PASS |
| Evidence | `gui-smoke-output.txt`. |
| Environment | ENV-1 |
| Notes | Theme and language state changed independently. |

### I18N-002 — PASS

| Field | Record |
|---|---|
| Feature | Indonesian-Dark localization |
| Objective | Indonesian labels remain active in Dark mode. |
| Preconditions | MainPage initialized; ENV-1. |
| Test procedure | Set language to Indonesian, set theme to Dark, inspect workspace label and theme mode. |
| Expected result | Indonesian label and Dark colors. |
| Actual result | `Masukan Data`, `#171c24`; assertions passed. |
| Status | PASS |
| Evidence | `gui-smoke-output.txt`. |
| Environment | ENV-1 |
| Notes | Theme selection does not change language. |

### I18N-003 — PASS

| Field | Record |
|---|---|
| Feature | English-Light localization |
| Objective | English labels remain active in Light mode. |
| Preconditions | MainPage initialized; ENV-1. |
| Test procedure | Set language to English, set theme to Light, inspect workspace label and theme mode. |
| Expected result | `Data Input` and Light colors. |
| Actual result | `Data Input`, `#f3f6fa`; assertions passed. |
| Status | PASS |
| Evidence | `gui-smoke-output.txt`. |
| Environment | ENV-1 |
| Notes | — |

### I18N-004 — PASS

| Field | Record |
|---|---|
| Feature | English-Dark localization |
| Objective | English labels remain active in Dark mode. |
| Preconditions | MainPage initialized; ENV-1. |
| Test procedure | Set language to English, set theme to Dark, inspect workspace label and theme mode. |
| Expected result | `Data Input` and Dark colors. |
| Actual result | `Data Input`, `#171c24`; assertions passed. |
| Status | PASS |
| Evidence | `gui-smoke-output.txt`. |
| Environment | ENV-1 |
| Notes | All four language/theme combinations were switched in one GUI session. |

### CHART-001 — PASS (tested subset)

| Field | Record |
|---|---|
| Feature | Light chart rendering |
| Objective | Verify readable Light backgrounds for tested chart workspaces. |
| Preconditions | Fishbone, Check Sheet, Defect Concentration, and I-MR view; ENV-1. |
| Test procedure | Create/open the workspaces in Light and inspect rendered figure/axes colors; render Fishbone export. |
| Expected result | Light plot background and visible semantic text/branches. |
| Actual result | Tested figure/axes returned white Light backgrounds; Fishbone Light PNG was valid and visually legible. |
| Status | PASS |
| Evidence | `gui-smoke-output.txt`; `EXPORT-001-fishbone.png`; `export-smoke-output.txt`. |
| Environment | ENV-1 |
| Notes | Pass applies to the named charts only. Other SPC chart families are explicitly not visually verified in CHART-004. |

### CHART-002 — PASS (tested subset)

| Field | Record |
|---|---|
| Feature | Dark chart rendering |
| Objective | Verify readable Dark backgrounds for tested chart workspaces. |
| Preconditions | I-MR, Fishbone, Check Sheet, and Defect Concentration figures; ENV-1. |
| Test procedure | Switch to Dark and inspect figure, axes, patch, title/tag, and plot background values; render Fishbone Dark export. |
| Expected result | Dark plot `#202833`, visible text/branches and contrast; unchanged chart result data. |
| Actual result | Tested plots used `#202833`; Fishbone branch/effect text and defect-area patches used Dark palette; Dark Fishbone image was visually legible. |
| Status | PASS |
| Evidence | `gui-smoke-output.txt`; `EXPORT-001-fishbone-dark.png`; `export-smoke-output.txt`. |
| Environment | ENV-1 |
| Notes | Pass applies to the named charts only, not every SPC family. |

### CHART-003 — PASS (verified rerun)

| Field | Record |
|---|---|
| Feature | Embedded chart resize |
| Objective | Confirm canvas redraws at a new window size. |
| Preconditions | Fishbone workspace open with a long cause; window in normal state; ENV-1. |
| Test procedure | Resize main window from `850x640` to `1180x790`, call Tk update, inspect canvas bounds and figure size. |
| Expected result | Canvas dimensions change and figure redraw remains responsive. |
| Actual result | Canvas changed from `628x476` to `958x600`; figure was `9.58x6.0` inches. |
| Status | PASS |
| Evidence | `gui-smoke-output.txt`. |
| Environment | ENV-1 |
| Notes | Resize behavior checked; no frame-time benchmark was collected. |

### CHART-003 — FAIL (initial run)

| Field | Record |
|---|---|
| Feature | Embedded chart resize test setup |
| Objective | Confirm canvas dimensions change after resizing. |
| Preconditions | Initial GUI script left the root in its zoomed state; ENV-1. |
| Test procedure | Initial smoke run compared canvas bounds after geometry changes without consistently setting the window to normal. |
| Expected result | Test expected canvas bounds to change. |
| Actual result | Assertion `d1 != d2` failed. |
| Status | FAIL |
| Evidence | Initial `gui_smoke.py` assertion output. |
| Environment | ENV-1 |
| Notes | Test setup was corrected to put the root in normal state before each geometry change; verified rerun resized from `628x476` to `958x600`. |

### CHART-004 — NOT RUN

| Field | Record |
|---|---|
| Feature | Remaining SPC chart-family visual theme coverage |
| Objective | Individually inspect Histogram, Pareto, Scatter, Xbar-R, Xbar-S, P, NP, C, U, R, and S chart rendering in both themes. |
| Preconditions | GUI required; ENV-1 available. |
| Test procedure | Not executed. |
| Expected result | Each chart family displays readable backgrounds, labels, legends, limits, and annotations in both themes. |
| Actual result | Not observed. |
| Status | NOT RUN |
| Evidence | N/A — no run or artifact exists. |
| Environment | ENV-1 available; no test session for these specific chart types. |
| Notes | Central Matplotlib styling was code-reviewed, but that does not prove their rendered appearance. Follow-up visual verification remains outstanding. |

### EXPORT-001 — PASS

| Field | Record |
|---|---|
| Feature | Fishbone PNG export |
| Objective | Produce a valid, readable PNG in Light and Dark. |
| Preconditions | Fishbone view with effect and cause; ENV-1. |
| Test procedure | Call the actual `FishboneView.export("png")` with a test save path in both themes; verify with Pillow and inspect the generated images. |
| Expected result | Valid image, readable text/diagram, theme-consistent background. |
| Actual result | Light and Dark PNGs opened and verified; both `2088x1007`; pixel background Light `(255,255,255)`, Dark `(32,40,51)`. |
| Status | PASS |
| Evidence | `EXPORT-001-fishbone.png`, `EXPORT-001-fishbone-dark.png`, `export-smoke-output.txt`. |
| Environment | ENV-1 |
| Notes | Images were generated by the app export path, not fabricated screenshots. |

### EXPORT-001 — BLOCKED (initial combined run)

| Field | Record |
|---|---|
| Feature | Fishbone PNG export combined smoke attempt |
| Objective | Exercise export within the longer multi-workspace GUI script. |
| Preconditions | Fishbone GUI smoke sequence; ENV-1. |
| Test procedure | Initial integrated script attempted export after several live dialog/theme operations. |
| Expected result | Export returns and produces a file. |
| Actual result | Combined process did not return from the export section during the bounded wait; the process was interrupted. |
| Status | BLOCKED |
| Evidence | Initial execution output ended after Fishbone theme checks; subsequent poll yielded no output; interrupted process exit 1. |
| Environment | ENV-1 |
| Notes | Isolated rerun through the same application export method passed; final pass is recorded above. |

### EXPORT-002 — PASS

| Field | Record |
|---|---|
| Feature | Fishbone PDF export |
| Objective | Produce a valid, readable one-page PDF in Light and Dark. |
| Preconditions | Fishbone view with effect and cause; ENV-1. |
| Test procedure | Call actual `FishboneView.export("pdf")` in Light and Dark; inspect PDF header and `/Type /Page` objects. |
| Expected result | Valid one-page PDF in each mode with readable figure palette. |
| Actual result | Both PDFs start `%PDF`, each has one page, and nonzero output; figure facecolor matched selected theme. |
| Status | PASS |
| Evidence | `EXPORT-002-fishbone.pdf`, `EXPORT-002-fishbone-dark.pdf`, `EXPORT-FOLLOWUP-002-fishbone.pdf`, `EXPORT-FOLLOWUP-002-fishbone-dark.pdf`, `export-smoke-output.txt`. |
| Environment | ENV-1 |
| Notes | Export was exercised through the actual app method; native file chooser was replaced with a temporary test path. |

### EXPORT-003 — PASS

| Field | Record |
|---|---|
| Feature | Defect Concentration PNG/PDF export |
| Objective | Ensure its existing PNG and PDF exports still work. |
| Preconditions | Defect Concentration workspace open; ENV-1. |
| Test procedure | Call `DefectConcentrationView.export` for PNG and PDF with test paths; inspect PNG with Pillow and PDF header/page object. |
| Expected result | Valid image and one-page PDF. |
| Actual result | PNG `674x782`; PDF begins `%PDF` and contains one page; both have nonzero size. |
| Status | PASS |
| Evidence | `EXPORT-003-defect-concentration.png`, `EXPORT-003-defect-concentration.pdf`, `EXPORT-FOLLOWUP-003-defect-concentration.pdf`, `defect-export-smoke-output.txt`. |
| Environment | ENV-1 |
| Notes | Check Sheet has no export action in its current UI; no Check Sheet export was applicable. |

### DIALOG-001 — PASS

| Field | Record |
|---|---|
| Feature | I-MR Generate lifecycle |
| Objective | Successful Generate closes configuration and shows result. |
| Preconditions | Six numeric observations entered in C1; real I-MR config dialog; ENV-1. |
| Test procedure | Open `IMRConfigPopup`, choose C1, invoke `generate()`, process Tk events. |
| Expected result | Config closes, chart view appears, analysis is stored. |
| Actual result | Config was destroyed, embedded chart became active, one analysis was added. |
| Status | PASS |
| Evidence | `gui_smoke.py`, `gui-smoke-output.txt`. |
| Environment | ENV-1 |
| Notes | Actual chart creation path; no mocked result constructor. |

### DIALOG-002 — PASS

| Field | Record |
|---|---|
| Feature | Generate validation failure |
| Objective | Invalid data leaves configuration open and preserves selected input. |
| Preconditions | One observation in C1; real I-MR config; error message function captured to avoid a blocking OS message box; ENV-1. |
| Test procedure | Select C1, call Generate, inspect dialog existence and field. |
| Expected result | Validation error is communicated; config and C1 selection remain. |
| Actual result | Config remained open, C1 remained selected, message stated at least two observations are required. |
| Status | PASS |
| Evidence | `gui-smoke-output.txt`. |
| Environment | ENV-1 |
| Notes | Error callback was captured rather than visually observing the native message box. |

### DIALOG-003 — PASS

| Field | Record |
|---|---|
| Feature | Generate execution failure |
| Objective | Runtime failure leaves configuration usable and communicates the error. |
| Preconditions | Real config dialog; `control_limits` fault-injected to raise `RuntimeError`; ENV-1. |
| Test procedure | Call Generate and capture the application's error callback. |
| Expected result | Config stays open and error is shown. |
| Actual result | Config stayed open; captured message included `The chart could not be created: injected chart failure`. |
| Status | PASS |
| Evidence | `gui-smoke-output.txt`. |
| Environment | ENV-1 |
| Notes | Fault injection validates the failure branch; message box itself was captured to avoid blocking. |

### DIALOG-004 — PASS

| Field | Record |
|---|---|
| Feature | Multi-monitor dialog placement |
| Objective | Popup centers on its parent's monitor and stays inside its work area. |
| Preconditions | Two physical monitor work areas available; parent moved to second monitor; ENV-1. |
| Test procedure | Create a Tk Toplevel owned by parent on monitor 2; run placement service and compare outer popup rect to monitor 2 work bounds. |
| Expected result | Popup is centered/clamped within `(1968,0)-(3280,768)`. |
| Actual result | Popup outer rect `(2422,293)-(2846,533)` fell entirely within monitor 2 work area. |
| Status | PASS |
| Evidence | `gui-smoke-output.txt`; actual Windows monitor/window geometry queries. |
| Environment | ENV-1, dual-monitor. |
| Notes | This run directly checked the second display. |

### REG-001 — PASS

| Field | Record |
|---|---|
| Feature | Existing regression suite |
| Objective | Run application unit/regression tests after changes. |
| Preconditions | Current working tree; ENV-2. |
| Test procedure | `python -m unittest discover -s tests -v`. |
| Expected result | All discovered tests pass. |
| Actual result | `Ran 50 tests`; `OK`; exit code 0. |
| Status | PASS |
| Evidence | `REG-001-test-output.txt`. |
| Environment | ENV-2 |
| Notes | Includes SPC calculation/Nelson tests, dialog helpers, chart workspace, quality models, and GUI keyboard tests. |

### BUILD-001 — PASS

| Field | Record |
|---|---|
| Feature | Python syntax compilation |
| Objective | Compile relevant application and test modules. |
| Preconditions | Current working tree; ENV-2. |
| Test procedure | `python -m compileall -q core logic models project_managers ui tests test-evidence/chart_visual_smoke.py test-evidence/popup_smoke.py test-evidence/dpi_probe.py test-evidence/native_dialog_probe.py`. |
| Expected result | Exit 0 with no syntax errors. |
| Actual result | Exit 0; no output. |
| Status | PASS |
| Evidence | Command result recorded in this report. |
| Environment | ENV-2 |
| Notes | — |

### REVIEW-001 — PASS

| Field | Record |
|---|---|
| Feature | Diff hygiene review |
| Objective | Check for whitespace and patch formatting errors. |
| Preconditions | Current working tree; ENV-2. |
| Test procedure | `git diff --check`. |
| Expected result | Exit 0. |
| Actual result | Exit 0, no output. |
| Status | PASS |
| Evidence | Command result recorded in this report. |
| Environment | ENV-2 |
| Notes | Working branch remained `main`; no commit, push, reset, or branch switch was performed. |

### GUI-SMOKE-001 — BLOCKED (initial harness run)

| Field | Record |
|---|---|
| Feature | Combined GUI verification harness |
| Objective | Start the GUI smoke script. |
| Preconditions | Initial script imported optional `pypdf`; ENV-1. |
| Test procedure | Launch initial script with `from pypdf import PdfReader`. |
| Expected result | Script imports and begins GUI checks. |
| Actual result | `ModuleNotFoundError: No module named 'pypdf'`; no GUI check ran in that attempt. |
| Status | BLOCKED |
| Evidence | Initial command output, exit 1. |
| Environment | ENV-1 |
| Notes | No dependency was added; script was corrected to validate PDF header/page object with stdlib and final GUI run passed. |

### GUI-SMOKE-001 — PASS (final harness run)

| Field | Record |
|---|---|
| Feature | Combined live GUI smoke run |
| Objective | Exercise language/theme changes, charts, dialogs, persistence, and resizing in one actual Tk session. |
| Preconditions | Tk available; temporary APPDATA; ENV-1. |
| Test procedure | `python test-evidence/gui_smoke.py`. |
| Expected result | Script completes all GUI assertions and restart check. |
| Actual result | Exit 0; all recorded assertions passed. |
| Status | PASS |
| Evidence | `gui-smoke-output.txt`; reproducible script `gui_smoke.py`. |
| Environment | ENV-1 |
| Notes | This records the verified rerun after the harness import issue. |

### GUI-SMOKE-002 — FAIL (initial harness run)

| Field | Record |
|---|---|
| Feature | Quality workspace smoke harness |
| Objective | Inspect Check Sheet then Defect Concentration styling. |
| Preconditions | GUI smoke had opened Check Sheet, then navigated to another workspace; ENV-1. |
| Test procedure | Initial harness queried the old Check Sheet widget after navigation had destroyed it. |
| Expected result | It expected a live widget. |
| Actual result | Tk raised `TclError: invalid command name ... checksheetview`. |
| Status | FAIL |
| Evidence | Initial smoke output, exit 1. |
| Environment | ENV-1 |
| Notes | Navigation correctly destroys the prior view. Harness was fixed to snapshot its values before navigation; final run passed. |

### GUI-SMOKE-002 — PASS (final harness run)

| Field | Record |
|---|---|
| Feature | Quality workspace theme smoke |
| Objective | Check Check Sheet and Defect Concentration in Light and Dark. |
| Preconditions | Both real workspace views created in Tk; ENV-1. |
| Test procedure | Switch both workspaces Light → Dark and inspect surface and figure colors. |
| Expected result | Each uses current palette and redraws. |
| Actual result | Both Light faces were white; both Dark faces `#202833`; defect patches used semantic Dark fills. |
| Status | PASS |
| Evidence | `gui_smoke.py`, `gui-smoke-output.txt`. |
| Environment | ENV-1 |
| Notes | Previous view was measured before navigating away. |

## Follow-up visual QA — 2026-10-26

### CHART-004-HISTOGRAM — PASS (verified rerun)

| Field | Record |
|---|---|
| Feature | Histogram chart family |
| Objective | Inspect actual embedded plot readability in both themes, theme switching, and resize. |
| Preconditions | ENV-1; live MainPage; representative six-value numeric dataset; actual HistogramChartPopup. |
| Test procedure | `$env:APPDATA='test-evidence\qa-appdata'; python test-evidence/chart_visual_smoke.py`; create the actual workspace in Light, switch the same figure to Dark, save PNGs, resize the host, and inspect both renders. |
| Expected result | Light/Dark figure and axes use their palette; title, ticks, bars, and grid remain readable; resize redraws. |
| Actual result | Light face `(1,1,1,1)`, Dark face `#202833`; chart resized from `952x612` to `814x565`; title shows “Simple Histogram”; assertions passed. |
| Status | PASS |
| Evidence | `chart-visual/histogram-light.png`, `chart-visual/histogram-dark.png`, `chart-visual-output.txt`, `chart_visual_smoke.py`. |
| Environment | ENV-1; chart canvas was a live Tk widget. |
| Notes | Figure was constructed by the application's chart view with representative data; calculations were not under test here. |

### CHART-004-PARETO — PASS (verified rerun)

| Field | Record |
|---|---|
| Feature | Pareto chart family |
| Objective | Inspect bars, cumulative line/percent annotations, dual axes, theme update, and resize. |
| Preconditions | ENV-1; live ParetoChartPopup; unique defect categories with frequencies 9, 6, and 4. |
| Test procedure | Run `python test-evidence/chart_visual_smoke.py`; capture the existing view in Light and Dark and inspect the app-rendered images. |
| Expected result | Bars, cumulative percentages, both axes, and labels remain legible in each palette and after resizing. |
| Actual result | Both figures had the expected facecolors; cumulative labels rendered 47.4%, 78.9%, 100.0%; canvas resized from `814x609` to `954x669`. |
| Status | PASS |
| Evidence | `chart-visual/pareto-light.png`, `chart-visual/pareto-dark.png`, `chart-visual/contact-sheet.png`, `chart-visual-output.txt`. |
| Environment | ENV-1; actual Tk chart workspace and Matplotlib figure. |
| Notes | Exploratory dataset initially repeated categories while also providing a frequency column, producing an invalid test fixture with overlapping points. The final run uses unique category rows; the initial screenshot was overwritten and is not claimed as product failure evidence. |

### CHART-004-SCATTER — PASS (verified rerun)

| Field | Record |
|---|---|
| Feature | Scatter chart family |
| Objective | Check marker contrast, axis labels/ticks, existing figure theme update, and resize. |
| Preconditions | ENV-1; live ScatterChartPopup; six finite X/Y observations. |
| Test procedure | Run `python test-evidence/chart_visual_smoke.py`; inspect saved Light/Dark figures and resize the actual embedded canvas. |
| Expected result | Points and axis text stay visible and the view redraws after theme and size changes. |
| Actual result | Both palette backgrounds and the six plotted points were visible; the canvas resized from `954x669` to `814x609`. |
| Status | PASS |
| Evidence | `chart-visual/scatter-light.png`, `chart-visual/scatter-dark.png`, `chart-visual-output.txt`. |
| Environment | ENV-1. |
| Notes | Simple scatter mode; regression and grouped scatter rendering were not part of this chart-family sample. |

### CHART-004-XBAR-R — PASS (verified rerun)

| Field | Record |
|---|---|
| Feature | X-bar R chart family |
| Objective | Check both panels, limits/center lines, legends, annotations, theme update, and resize. |
| Preconditions | ENV-1; actual XbarRChartPopup with five subgroups and explicit center/control limits. |
| Test procedure | Run `python test-evidence/chart_visual_smoke.py`; render each theme and compare each range-line label to its actual y coordinate. |
| Expected result | Text and control lines remain distinct in Light/Dark; UCL is attached to upper limit and LCL to lower limit. |
| Actual result | Both panels legible; range lines map `LCL = 0.0` to y=0 and `UCL = 0.94` to y=0.94 after correction; canvas `556x800`. |
| Status | PASS |
| Evidence | `chart-visual/xbar_r-light.png`, `chart-visual/xbar_r-dark.png`, `chart-visual-output.txt`; assertions in `chart_visual_smoke.py`. |
| Environment | ENV-1; live Tk chart workspace. |
| Notes | The first visual run revealed the UCL/LCL legend labels were attached to the opposite range lines. Small fix is in `logic/xbar_r.py`; initial failure is recorded below. |

### CHART-004-XBAR-S — PASS (verified rerun)

| Field | Record |
|---|---|
| Feature | X-bar S chart family |
| Objective | Check both panels, limits, legends, theme update, and resize. |
| Preconditions | ENV-1; actual XbarSChartPopup with five subgroups and explicit limits. |
| Test procedure | Run `python test-evidence/chart_visual_smoke.py`; render Light/Dark and resize the embedded canvas. |
| Expected result | Both panels remain readable with their control lines and labels in both themes. |
| Actual result | Both panel faces and text were legible; same view updated from Light to Dark; canvas `556x800`. |
| Status | PASS |
| Evidence | `chart-visual/xbar_s-light.png`, `chart-visual/xbar_s-dark.png`, `chart-visual-output.txt`. |
| Environment | ENV-1. |
| Notes | Representative valid subgroup summaries supplied to the actual chart view; subgroup calculation itself remains covered by `REG-001`. |

### CHART-004-P — PASS (verified rerun)

| Field | Record |
|---|---|
| Feature | p chart family |
| Objective | Check proportions, varying control-limit lines, center line, legend, theme update, and resize. |
| Preconditions | ENV-1; actual PChartPopup with five proportions and UCL/LCL vectors. |
| Test procedure | Run `python test-evidence/chart_visual_smoke.py`; save each palette and resize. |
| Expected result | Lines and labels are readable, limits distinguishable, and the chart redraws. |
| Actual result | Both themes rendered with expected facecolors and visible p/UCL/LCL/p-bar lines; canvas changed `570x566` to `570x626`. |
| Status | PASS |
| Evidence | `chart-visual/p-light.png`, `chart-visual/p-dark.png`, `chart-visual-output.txt`. |
| Environment | ENV-1. |
| Notes | Visual sample used explicit representative control limits; no analytical values were recalculated by theme switching. |

### CHART-004-NP — PASS (verified rerun)

| Field | Record |
|---|---|
| Feature | np chart family |
| Objective | Check count series, control limits, labels, theme update, and resize. |
| Preconditions | ENV-1; actual NPChartPopup with five counts and limits. |
| Test procedure | Run `python test-evidence/chart_visual_smoke.py`; save Light/Dark views and resize. |
| Expected result | Count data, limits, and legends remain legible after theme changes and resizing. |
| Actual result | Both palette renders and all lines/labels were visible; canvas changed `570x626` to `570x566`. |
| Status | PASS |
| Evidence | `chart-visual/np-light.png`, `chart-visual/np-dark.png`, `chart-visual-output.txt`. |
| Environment | ENV-1. |
| Notes | Chart view was instantiated with representative result data. |

### CHART-004-C — PASS (verified rerun)

| Field | Record |
|---|---|
| Feature | c chart family |
| Objective | Check count series, center/control lines, legend, theme update, and resize. |
| Preconditions | ENV-1; actual CChartPopup with five counts and explicit limits. |
| Test procedure | Run `python test-evidence/chart_visual_smoke.py`; inspect app-rendered images in both themes and resize. |
| Expected result | Chart lines and axis/legend text remain readable in Light and Dark. |
| Actual result | Both faces, labels, limits, and center line were visible; canvas changed `570x566` to `570x626`. |
| Status | PASS |
| Evidence | `chart-visual/c-light.png`, `chart-visual/c-dark.png`, `chart-visual-output.txt`. |
| Environment | ENV-1. |
| Notes | Representative chart result payload was passed to the real view. |

### CHART-004-U — PASS (verified rerun)

| Field | Record |
|---|---|
| Feature | u chart family |
| Objective | Check unit-rate series, control limits, labels, theme update, and resize. |
| Preconditions | ENV-1; actual UChartPopup with five rate observations and limit vectors. |
| Test procedure | Run `python test-evidence/chart_visual_smoke.py`; capture Light/Dark and resize. |
| Expected result | Data, control lines, title, and axes remain legible and redraw at a new size. |
| Actual result | Both palette renders were visible; canvas changed `614x689` to `614x629`. |
| Status | PASS |
| Evidence | `chart-visual/u-light.png`, `chart-visual/u-dark.png`, `chart-visual-output.txt`. |
| Environment | ENV-1. |
| Notes | Representative result payload used; numerical limit calculation was not changed. |

### CHART-004-R — BLOCKED

| Field | Record |
|---|---|
| Feature | Standalone R chart |
| Objective | Inspect R chart Light/Dark display and resizing. |
| Preconditions | ENV-1 available; application UI inspection. |
| Test procedure | Inspect `logic/rbar.py` and the application chart menu. |
| Expected result | A usable R chart opens for visual inspection. |
| Actual result | The UI disables R-bar and `RbarConfigPopup`/`RbarChartPopup` only show “Under Maintenance” then destroy themselves; no chart exists to render. |
| Status | BLOCKED |
| Evidence | `logic/rbar.py`; `ui/ui.py` subgroup menu; `popup-inventory.txt`. |
| Environment | ENV-1; GUI available. |
| Notes | Product capability blocker, not an environment issue. No chart theme claim is made for this placeholder. |

### CHART-004-S — BLOCKED

| Field | Record |
|---|---|
| Feature | Standalone S chart |
| Objective | Inspect S chart Light/Dark display and resizing. |
| Preconditions | ENV-1 available; application UI inspection. |
| Test procedure | Inspect `logic/sbar.py` and the application chart menu. |
| Expected result | A usable standalone S chart opens for visual inspection. |
| Actual result | S-bar is disabled and `SbarConfigPopup`/`SbarChartPopup` only show “Under Maintenance” then destroy themselves. Xbar-S was tested separately above. |
| Status | BLOCKED |
| Evidence | `logic/sbar.py`; `ui/ui.py` subgroup menu; `popup-inventory.txt`. |
| Environment | ENV-1; GUI available. |
| Notes | Product capability blocker; standalone S is distinct from the S panel inside Xbar-S. |

### CHART-004-HISTOGRAM — FAIL (initial visual run)

| Field | Record |
|---|---|
| Feature | Histogram chart title |
| Objective | Confirm chart title is correctly localized/displayed. |
| Preconditions | ENV-1; actual simple HistogramChartPopup. |
| Test procedure | Initial `python test-evidence/chart_visual_smoke.py`; inspect its actual figure title. |
| Expected result | “Simple Histogram” in English. |
| Actual result | The UI looked up misspelled localization key `simpe_histogram`, so it displayed the raw typo. |
| Status | FAIL |
| Evidence | Initial live figure inspection; no durable initial PNG/log was retained because rerun output replaced it. |
| Environment | ENV-1. |
| Notes | Confirmed application defect; corrected key and verified in the passing rerun above. Initial visual artifact is unavailable and not represented as a current screenshot. |

### CHART-004-XBAR-R — FAIL (initial visual run)

| Field | Record |
|---|---|
| Feature | Xbar-R range limit legend |
| Objective | Verify the UCL and LCL legend values correspond to their plotted lines. |
| Preconditions | ENV-1; actual XbarRChartPopup with R LCL=0 and UCL=0.94. |
| Test procedure | Initial live figure inspection of the R-panel line labels and y coordinates. |
| Expected result | UCL label on y=0.94; LCL label on y=0. |
| Actual result | The labels were reversed: the y=0 line was labelled UCL=0.94 and y=0.94 was labelled LCL=0.0. |
| Status | FAIL |
| Evidence | Initial chart render observed during first visual run; the pre-fix image was overwritten on rerun, so no durable initial image exists. |
| Environment | ENV-1. |
| Notes | Confirmed application defect; fixed both label bindings and rerun assertions passed. Numerical limits and plotted data did not change. |

### CHART-005 — PASS

| Field | Record |
|---|---|
| Feature | Visual QA regression fixes |
| Objective | Prevent regressions in Histogram title lookup and Xbar-R range limit labels. |
| Preconditions | ENV-1; corrected `logic/histogram.py` and `logic/xbar_r.py`. |
| Test procedure | `python test-evidence/chart_visual_smoke.py`; assert exact title `Simple Histogram` and map actual line labels to y coordinates before and after theme switching. |
| Expected result | Correct localized key is used; `LCL = 0.0` belongs to y=0 and `UCL = 0.94` belongs to y=0.94 in both themes. |
| Actual result | All assertions passed; all nine supported chart views passed Light/Dark rendering checks. |
| Status | PASS |
| Evidence | `chart_visual_smoke.py`, `chart-visual-output.txt`, relevant PNGs in `chart-visual/`. |
| Environment | ENV-1. |
| Notes | Theme changes did not modify chart result payloads. |

### DIALOG-AUDIT-001 — FAIL (initial harness run)

| Field | Record |
|---|---|
| Feature | Repeated popup smoke harness |
| Objective | Open, theme, close, and reopen representative app dialogs. |
| Preconditions | ENV-1; live Tk MainPage; first harness version also included synchronous modal CategoryPicker. |
| Test procedure | Initial runs of `python test-evidence/popup_smoke.py`. |
| Expected result | Each constructed dialog remains queryable after being closed and all listed dialogs complete. |
| Actual result | Initial harness queried a Toplevel after destroying it; a subsequent version blocked in CategoryPicker's `wait_window`; a later run passed the picker but had an incorrect CauseEditorDialog call signature. These were harness issues, not demonstrated application failures. |
| Status | FAIL |
| Evidence | Initial console failures were observed but the Tee log was overwritten by final reruns; exact initial output artifact is unavailable. |
| Environment | ENV-1. |
| Notes | Harness corrected to avoid querying destroyed windows, to omit the synchronous picker from this generic loop (picker interaction is in `gui_smoke.py`), and to use the actual cause-editor signature. Final run is recorded separately. |

### DIALOG-AUDIT-001 — PASS (verified rerun)

| Field | Record |
|---|---|
| Feature | Representative configuration dialog lifecycle and themes |
| Objective | Open/reopen 12 configuration/popup types, check geometry/work area, and switch active dialogs Light/Dark. |
| Preconditions | ENV-1; root on primary display; 12 live Tk popups/configurations. |
| Test procedure | `$env:APPDATA='test-evidence\qa-appdata'; python test-evidence/popup_smoke.py`; open each dialog, measure actual size/window rect, toggle Light→Dark→Light, destroy, reopen in Light, and close. |
| Expected result | Dialog exists, has usable dimensions, remains inside its parent monitor work area, responds to theme updates, and can be reopened without stale Tk errors. |
| Actual result | All 12 passed: Histogram menu, Pareto config, Scatter menu, I-MR, Xbar-R, Xbar-S, p, np, c, U mode, converter, and Fishbone cause editor. Sizes ranged from `320x200` to `1100x650`; all rects were inside `(48,0)-(1536,864)`. |
| Status | PASS |
| Evidence | `popup_smoke.py`, `popup-smoke-output.txt`; previous `gui-smoke-output.txt` also covers category picker and Fishbone interactions. |
| Environment | ENV-1; two monitors attached; this loop placed dialogs on monitor 1. |
| Notes | This is representative lifecycle/theme coverage, not a control-by-control keyboard/focus audit for every dialog. Native message boxes and file choosers are separate. |

### POPUP-INV-001 — PASS (code review)

| Field | Record |
|---|---|
| Feature | Application popup inventory |
| Objective | Identify reachable Toplevel classes and application-owned native file/message dialog calls. |
| Preconditions | Current source on `main`; ENV-2. |
| Test procedure | `rg -n 'class .*Popup|class .*Dialog|tk\.Toplevel|filedialog|messagebox' ui logic project_managers`. |
| Expected result | Inventory surfaces the chart, converter, quality-tool, help, and project dialogs for test scoping. |
| Actual result | Inventory written; chart config types are covered by DIALOG-AUDIT-001. Remaining classes include category text/add-record/preview/conversion, U-converted workflow, project confirmations, native message boxes, and export dialogs. |
| Status | PASS |
| Evidence | `popup-inventory.txt`; source list in `ui/ui.py`, `ui/quality_tools.py`, `logic/converter.py`, and `project_managers/project_manager.py`. |
| Environment | ENV-2; code review only. |
| Notes | This is a code inventory, not GUI verification. Exhaustive popup UX coverage remains NOT RUN below. |

### DIALOG-AUDIT-002 — NOT RUN

| Field | Record |
|---|---|
| Feature | Exhaustive popup and dialog interaction audit |
| Objective | Exercise every reachable dialog's keyboard focus, Enter/Escape, validation, execution error, localization, clipping, and repeated lifecycle behavior. |
| Preconditions | ENV-1 available. |
| Test procedure | Not executed for every inventoried class. |
| Expected result | Each dialog's intended controls and success/failure/cancel behaviors are individually observed and recorded. |
| Actual result | Representative config dialog lifecycle passed; prior records cover I-MR validation/execution branches, Fishbone, Help, and category selection. Category text, Check Sheet add/edit record, conversion preview/converted U, project confirmation, all native messageboxes, and every language combination per dialog were not individually driven. |
| Status | NOT RUN |
| Evidence | N/A for exhaustive test; inventory is `popup-inventory.txt`. |
| Environment | ENV-1 available. |
| Notes | No claim of exhaustive dialog verification. This remains follow-up work. |

### DPI-001 — PASS

| Field | Record |
|---|---|
| Feature | Current multi-monitor resolution and work-area handling |
| Objective | Check available monitor bounds, popup work-area clamp, and multiple window sizes. |
| Preconditions | ENV-1; two displays. |
| Test procedure | `python test-evidence/dpi_probe.py`; prior actual secondary-monitor dialog test `DIALOG-004`; chart resize tests at two window geometries. |
| Expected result | Both displays are enumerated; dialogs stay within the parent monitor work area; supported window-size changes redraw content. |
| Actual result | Monitor 1 bounds `1536x864`, monitor 2 `1360x768`; popup was previously clamped to monitor 2 work area; live chart canvases resized in smoke tests. |
| Status | PASS |
| Evidence | `dpi-probe-output.txt`, `gui-smoke-output.txt`, `chart-visual-output.txt`. |
| Environment | ENV-1. |
| Notes | Display resolutions differ. This pass does not imply non-100% scaling coverage. |

### DPI-002 — BLOCKED

| Field | Record |
|---|---|
| Feature | Non-100% Windows scaling |
| Objective | Verify clipping and dialog/layout behavior at a non-default display scale. |
| Preconditions | Windows GUI available; system setting left unchanged. |
| Test procedure | Read system and per-monitor DPI with `python test-evidence/dpi_probe.py`. |
| Expected result | Test at one or more monitor scales above/below 100%. |
| Actual result | Both monitors and system report 96 DPI (100%); no non-100% monitor was available. System display settings were not changed. |
| Status | BLOCKED |
| Evidence | `dpi-probe-output.txt`: `system_dpi 96`, both monitors `dpi (96,96)`. |
| Environment | Windows 10 build 26300, ENV-1. |
| Notes | Scaling-specific behavior remains unverified. |

### FILE-DIALOG-001 — BLOCKED

| Field | Record |
|---|---|
| Feature | Native Windows file-open dialog |
| Objective | Exercise cancel, valid Excel selection, and unsupported/invalid file handling through Import Excel. |
| Preconditions | ENV-1; actual ProjectManager Import Excel workflow; no real user file was selected. |
| Test procedure | `python test-evidence/native_dialog_probe.py`, which calls `app.ui.project_manager.import_excel()` and enumerates visible Windows dialogs in the process. |
| Expected result | Native Open dialog appears and can be cancelled or supplied a valid/invalid fixture path; active input is preserved on cancel/failure. |
| Actual result | Probe returned exit 0 but found only `SPC App`; no Open dialog was exposed to the available UI automation, so selection/cancel/error behavior was not observed. |
| Status | BLOCKED |
| Evidence | `native-dialog-probe.txt`; output `NO_COMMON_DIALOG` followed by visible-window inventory. |
| Environment | ENV-1; GUI process ran, no UI Automation/pywinauto available. |
| Notes | The probe did not establish whether Windows suppressed the dialog or whether it was inaccessible to this automation. No manual test was available in this run. Do not treat exit 0 as file dialog success. |

### FILE-DIALOG-002 — BLOCKED

| Field | Record |
|---|---|
| Feature | Native Windows file-save dialog |
| Objective | Exercise cancellation, valid path, filename with spaces, and save outcome through an application export/save workflow. |
| Preconditions | ENV-1; actual file chooser required. |
| Test procedure | Attempt was not completed because the native Open chooser could not be surfaced to the available automation; no native Save chooser was driven. |
| Expected result | Save path and spaced filename are accepted; cancel leaves current analysis/input unchanged. |
| Actual result | Not observed. Existing export smoke tests patched the chooser to a deterministic path and therefore do not satisfy native dialog coverage. |
| Status | BLOCKED |
| Evidence | `native-dialog-probe.txt`; export smoke logs only evidence app export functions, not the native Save dialog. |
| Environment | ENV-1; no UI Automation/pywinauto available. |
| Notes | Manual or UIA-driven native Save dialog verification remains outstanding. |

### CHART-VALIDATION-001 — NOT RUN

| Field | Record |
|---|---|
| Feature | Per-chart empty/invalid/insufficient-data GUI validation |
| Objective | Observe validation feedback and input preservation for all supported chart families. |
| Preconditions | ENV-1; chart dialogs reachable. |
| Test procedure | Not executed per family in this visual-render pass. Existing automated validation tests were included in REG-001, and I-MR validation/execution branches were driven in `gui_smoke.py`. |
| Expected result | Each chart's empty, malformed, and insufficient data states report an appropriate error without crashing or discarding input. |
| Actual result | Automated validation suite passes, but actual GUI behavior for all families was not individually observed. |
| Status | NOT RUN |
| Evidence | `REG-001-test-output.txt`, `gui-smoke-output.txt`; no per-chart validation GUI artifact. |
| Environment | ENV-1 GUI available; no per-family interaction run. |
| Notes | This gap remains despite successful visual rendering of nine chart families. |

### REVIEW-002 — PASS

| Field | Record |
|---|---|
| Feature | Diff and branch-safety review |
| Objective | Verify only focused visual fixes were added and branch/commit safety rules remained respected. |
| Preconditions | Existing uncommitted tree on `main`; no branch changes permitted. |
| Test procedure | `git diff --check`; `git status --short --branch`; `git log -1 --oneline`; source review of the two chart changes. |
| Expected result | Clean patch formatting; no commit/push/reset/branch switch; unrelated pre-existing work preserved. |
| Actual result | Diff check passed; working tree remains on `main`; no commit, push, reset, or branch switch performed. Existing modifications remain. |
| Status | PASS |
| Evidence | Current Git status and diff output. |
| Environment | ENV-2. |
| Notes | This test does not imply the repository was clean before the task. |

