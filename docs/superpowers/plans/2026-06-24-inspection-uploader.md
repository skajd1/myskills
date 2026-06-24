# Inspection Uploader Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reusable personal Codex skill that previews Outlook inspection PDF candidates, identifies customers from first-page OCR text, and uploads only user-approved PDFs to configured SharePoint folders.

**Architecture:** The skill package owns both the agent-facing instructions and a deterministic Python CLI. The CLI separates pure logic from live Microsoft Graph calls so customer matching, filename rendering, config validation, and state handling can be tested without Outlook or SharePoint access.

**Tech Stack:** Python 3.13 standard library for core logic and tests, optional runtime packages for live mode (`msal`, `requests`, `PyYAML`, PDF/OCR tools), Codex skill metadata in `SKILL.md` and `agents/openai.yaml`.

---

## File Structure

- `C:\Users\wooch\.codex\skills\inspection-uploader\SKILL.md`: trigger conditions, required preview/approval workflow, command sequence, safety rules.
- `C:\Users\wooch\.codex\skills\inspection-uploader\agents\openai.yaml`: UI metadata for Codex skill lists.
- `C:\Users\wooch\.codex\skills\inspection-uploader\scripts\inspection_uploader.py`: CLI entrypoint and pure business logic.
- `C:\Users\wooch\.codex\skills\inspection-uploader\tests\test_inspection_uploader.py`: unit tests for deterministic logic.
- `C:\Users\wooch\.codex\skills\inspection-uploader\references\config-schema.md`: configuration schema and filename-template rules.
- `C:\Users\wooch\.codex\skills\inspection-uploader\assets\config.example.yaml`: starter YAML config.

## Task 1: Scaffold The Skill Package

**Files:**
- Create directory: `C:\Users\wooch\.codex\skills\inspection-uploader`
- Create: `C:\Users\wooch\.codex\skills\inspection-uploader\SKILL.md`
- Create: `C:\Users\wooch\.codex\skills\inspection-uploader\agents\openai.yaml`
- Create directories: `scripts`, `tests`, `references`, `assets`

- [ ] **Step 1: Create the directory structure**

Run:

```powershell
$root = 'C:\Users\wooch\.codex\skills\inspection-uploader'
New-Item -ItemType Directory -Force -Path $root, "$root\agents", "$root\scripts", "$root\tests", "$root\references", "$root\assets"
```

Expected: directories exist.

- [ ] **Step 2: Add minimal placeholder skill metadata**

Create `SKILL.md` with valid frontmatter:

```markdown
---
name: inspection-uploader
description: Use when the user wants Codex to process scanned inspection PDF emails from Outlook, identify the customer, preview candidates, and upload approved files to SharePoint.
---

# Inspection Uploader

Follow the bundled workflow for Outlook inspection PDF preview and SharePoint upload.
```

- [ ] **Step 3: Add initial UI metadata**

Create `agents/openai.yaml`:

```yaml
display_name: Inspection Uploader
short_description: Preview scanned Outlook inspection PDFs and upload approved files to SharePoint.
default_prompt: Run the inspection uploader preview workflow.
```

## Task 2: Test Config Validation

**Files:**
- Create: `C:\Users\wooch\.codex\skills\inspection-uploader\tests\test_inspection_uploader.py`
- Create: `C:\Users\wooch\.codex\skills\inspection-uploader\scripts\inspection_uploader.py`

- [ ] **Step 1: Write failing tests**

Add tests:

```python
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import inspection_uploader as uploader


class ConfigValidationTests(unittest.TestCase):
    def test_valid_config_returns_no_errors(self):
        config = {
            "customers": [
                {
                    "id": "acme",
                    "display_name": "ACME Korea",
                    "aliases": ["ACME", "ACME Korea"],
                    "sharepoint": {
                        "site_url": "https://tenant.sharepoint.com/sites/Inspection",
                        "drive_name": "Documents",
                        "folder_path": "Customers/ACME/Inspection",
                    },
                    "filename_template": "{date:%Y%m%d}_{customer}_{original_stem}.pdf",
                }
            ]
        }

        self.assertEqual(uploader.validate_config(config), [])

    def test_missing_required_customer_fields_are_reported(self):
        config = {"customers": [{"id": "acme"}]}

        errors = uploader.validate_config(config)

        self.assertIn("customers[0].display_name is required", errors)
        self.assertIn("customers[0].aliases must contain at least one alias", errors)
        self.assertIn("customers[0].sharepoint.site_url is required", errors)
        self.assertIn("customers[0].sharepoint.drive_name is required", errors)
        self.assertIn("customers[0].sharepoint.folder_path is required", errors)
        self.assertIn("customers[0].filename_template is required", errors)
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```powershell
& 'C:\Users\wooch\AppData\Local\Programs\Python\Python313\python.exe' -m unittest C:\Users\wooch\.codex\skills\inspection-uploader\tests\test_inspection_uploader.py -v
```

Expected: FAIL or ERROR because `inspection_uploader` or `validate_config` does not exist.

- [ ] **Step 3: Implement minimal validation**

Add `validate_config(config)` to `scripts/inspection_uploader.py`. It must check for `customers`, required customer fields, required SharePoint fields, and non-empty aliases.

- [ ] **Step 4: Run tests and verify GREEN**

Run the same unittest command.

Expected: both config validation tests pass.

## Task 3: Test Matching And Filename Rendering

**Files:**
- Modify: `tests/test_inspection_uploader.py`
- Modify: `scripts/inspection_uploader.py`

- [ ] **Step 1: Write failing tests**

Add tests:

```python
class MatchingTests(unittest.TestCase):
    def test_matches_customer_by_longest_alias(self):
        customers = [
            {"id": "a", "display_name": "A", "aliases": ["ACME"]},
            {"id": "b", "display_name": "B", "aliases": ["ACME Korea"]},
        ]

        result = uploader.match_customer("Inspection Report for ACME Korea", customers)

        self.assertEqual(result["status"], "matched")
        self.assertEqual(result["customer_id"], "b")
        self.assertIn("ACME Korea", result["evidence"])

    def test_ambiguous_matches_are_not_auto_selected(self):
        customers = [
            {"id": "a", "display_name": "A", "aliases": ["ACME"]},
            {"id": "b", "display_name": "B", "aliases": ["Beta"]},
        ]

        result = uploader.match_customer("ACME and Beta appear together", customers)

        self.assertEqual(result["status"], "ambiguous")
        self.assertEqual(result["customer_id"], None)

    def test_unmatched_text_is_reported(self):
        result = uploader.match_customer("No configured customer", [{"id": "a", "display_name": "A", "aliases": ["ACME"]}])

        self.assertEqual(result["status"], "unmatched")
        self.assertEqual(result["customer_id"], None)


class FilenameRenderingTests(unittest.TestCase):
    def test_renders_filename_template(self):
        rendered = uploader.render_filename(
            "{date:%Y%m%d}_{customer}_{original_stem}.pdf",
            received_at="2026-06-24T13:48:00Z",
            customer_name="ACME Korea",
            original_filename="240620261348.pdf",
        )

        self.assertEqual(rendered, "20260624_ACME Korea_240620261348.pdf")

    def test_rejects_path_separator_in_rendered_filename(self):
        with self.assertRaises(ValueError):
            uploader.render_filename(
                "{customer}/{original_stem}.pdf",
                received_at="2026-06-24T13:48:00Z",
                customer_name="ACME",
                original_filename="scan.pdf",
            )
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```powershell
& 'C:\Users\wooch\AppData\Local\Programs\Python\Python313\python.exe' -m unittest C:\Users\wooch\.codex\skills\inspection-uploader\tests\test_inspection_uploader.py -v
```

Expected: FAIL because `match_customer` and `render_filename` do not exist.

- [ ] **Step 3: Implement matching and filename rendering**

Implement `match_customer(text, customers)` with deterministic alias matching and ambiguity detection. Implement `render_filename(...)` with `{date:<strftime>}`, `{customer}`, and `{original_stem}` support and reject path separators.

- [ ] **Step 4: Run tests and verify GREEN**

Run the same unittest command.

Expected: all tests pass.

## Task 4: Test State And Preview Rows

**Files:**
- Modify: `tests/test_inspection_uploader.py`
- Modify: `scripts/inspection_uploader.py`

- [ ] **Step 1: Write failing tests**

Add tests:

```python
class StateTests(unittest.TestCase):
    def test_state_round_trips_json(self):
        state = {"candidates": [{"id": "c1", "status": "ready"}]}
        path = ROOT / "tests" / "tmp-state.json"
        try:
            uploader.write_state(path, state)
            self.assertEqual(uploader.read_state(path), state)
        finally:
            if path.exists():
                path.unlink()


class PreviewTests(unittest.TestCase):
    def test_build_preview_candidate_includes_target(self):
        customer = {
            "id": "acme",
            "display_name": "ACME Korea",
            "sharepoint": {
                "site_url": "https://tenant.sharepoint.com/sites/Inspection",
                "drive_name": "Documents",
                "folder_path": "Customers/ACME/Inspection",
            },
            "filename_template": "{date:%Y%m%d}_{customer}_{original_stem}.pdf",
        }
        message = {
            "id": "m1",
            "received_at": "2026-06-24T13:48:00Z",
            "sender": "scanner@example.com",
            "subject": "Scan Data",
        }
        attachment = {"id": "a1", "filename": "240620261348.pdf"}

        row = uploader.build_preview_candidate(message, attachment, customer, {"status": "matched", "customer_id": "acme", "evidence": "ACME"})

        self.assertEqual(row["id"], "m1:a1")
        self.assertEqual(row["target"]["folder_path"], "Customers/ACME/Inspection")
        self.assertEqual(row["target"]["filename"], "20260624_ACME Korea_240620261348.pdf")
        self.assertEqual(row["upload_status"], "pending")
```

- [ ] **Step 2: Run tests and verify RED**

Expected: FAIL because state and preview helpers do not exist.

- [ ] **Step 3: Implement state and preview helpers**

Implement JSON read/write with UTF-8 and deterministic preview row creation.

- [ ] **Step 4: Run tests and verify GREEN**

Expected: all deterministic tests pass.

## Task 5: Add CLI Shell With Safe Stubbed Live Operations

**Files:**
- Modify: `scripts/inspection_uploader.py`

- [ ] **Step 1: Add CLI argument parser tests if needed**

Use direct function tests for pure logic. For CLI behavior, verify manually with `--help`.

- [ ] **Step 2: Implement commands**

Implement `auth`, `validate-config`, `scan`, `show`, and `upload` commands. `validate-config` must work fully. `scan`, `auth`, and `upload` may report missing optional live dependencies or credentials with actionable messages until Graph/OCR dependencies are configured.

- [ ] **Step 3: Verify CLI help**

Run:

```powershell
& 'C:\Users\wooch\AppData\Local\Programs\Python\Python313\python.exe' C:\Users\wooch\.codex\skills\inspection-uploader\scripts\inspection_uploader.py --help
```

Expected: command list is shown.

## Task 6: Write Skill Instructions And Resources

**Files:**
- Modify: `SKILL.md`
- Modify: `agents/openai.yaml`
- Create: `references/config-schema.md`
- Create: `assets/config.example.yaml`

- [ ] **Step 1: Expand SKILL.md**

Include the required workflow: validate config, scan, show preview, ask user which rows to upload, upload only selected rows, report results. Explicitly prohibit automatic upload without user approval.

- [ ] **Step 2: Write config schema reference**

Document required YAML fields, alias matching, filename variables, and SharePoint target fields.

- [ ] **Step 3: Write example config**

Provide a safe placeholder config with no real tenant secrets.

## Task 7: Validate And Commit

**Files:**
- All files above

- [ ] **Step 1: Run unit tests**

Run:

```powershell
& 'C:\Users\wooch\AppData\Local\Programs\Python\Python313\python.exe' -m unittest C:\Users\wooch\.codex\skills\inspection-uploader\tests\test_inspection_uploader.py -v
```

Expected: all tests pass.

- [ ] **Step 2: Validate skill shape**

Check that `SKILL.md` frontmatter has only `name` and `description`, skill name uses lowercase hyphen-case, and `agents/openai.yaml` exists.

- [ ] **Step 3: Commit workspace plan**

Commit the implementation plan in the workspace. The personal skill directory may live outside this repository and should not be committed here unless explicitly copied into the repo.
