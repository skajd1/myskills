# Inspection Uploader Skill Design

## Goal

Create a reusable Codex skill named `inspection-uploader` that helps Codex run an on-demand workflow for scanned inspection PDFs received in Outlook. The workflow identifies the customer from OCR text on the first PDF page, previews upload candidates, waits for user approval, and uploads selected files to the configured SharePoint folder with the configured filename.

The workflow is manual/on-demand. It is not a scheduled job.

## User Experience

The user asks Codex to run the inspection upload workflow. Codex loads the `inspection-uploader` skill and runs the bundled CLI in preview mode.

The preview lists candidate PDF attachments from Outlook:

- message received time
- sender
- subject
- attachment filename
- OCR customer match
- confidence or match reason
- planned SharePoint target folder
- planned upload filename
- warnings such as duplicate target filename, missing customer match, or low confidence

Codex shows this list to the user and asks which rows to upload. Only selected rows are uploaded. Items with no customer match, ambiguous match, or target conflict are not uploaded unless the user explicitly chooses a supported override path in a later version.

## Skill Package

Default location:

`C:\Users\wooch\.codex\skills\inspection-uploader`

Files:

- `SKILL.md`: trigger conditions and required workflow for Codex
- `scripts/inspection_uploader.py`: deterministic CLI for Microsoft Graph, OCR, matching, preview, and upload
- `references/config-schema.md`: metadata schema and naming-template rules
- `assets/config.example.yaml`: starter customer mapping config

The skill is the reusable entrypoint. The script performs the live automation.

## CLI Commands

The bundled Python CLI should expose these commands:

- `auth`: complete Microsoft OAuth sign-in and cache the token
- `validate-config --config <path>`: validate customer metadata before scanning
- `scan --config <path> --since-days <n> --out <path>`: fetch Outlook PDF attachment candidates, OCR first pages, match customers, and write a preview state file
- `show --state <path>`: print a compact table of scan results for Codex to relay
- `upload --state <path> --ids <id,id,...>`: upload selected candidates to SharePoint and write results back to the state file

The default flow is `validate-config`, `scan`, `show`, then `upload` after user approval.

## Configuration

Use YAML for customer metadata. The first implementation supports one config file selected by command line. The user can keep it inside the skill directory, the workspace, or another local path.

Example:

```yaml
mail:
  sender_allowlist:
    - "scanner@example.com"
  subject_keywords:
    - "Scan Data"
  max_messages: 50

ocr:
  language: "kor+eng"
  min_confidence: 0.70

customers:
  - id: "acme"
    display_name: "ACME Korea"
    aliases:
      - "ACME"
      - "ACME Korea"
    sharepoint:
      site_url: "https://tenant.sharepoint.com/sites/Inspection"
      drive_name: "Documents"
      folder_path: "Customers/ACME/Inspection"
    filename_template: "{date:%Y%m%d}_{customer}_{original_stem}.pdf"
```

Required customer fields:

- `id`
- `display_name`
- `aliases`
- `sharepoint.site_url`
- `sharepoint.drive_name`
- `sharepoint.folder_path`
- `filename_template`

## Customer Detection

PDFs are expected to be scanned images. The implementation renders only the first page to an image and runs OCR.

Matching rules:

1. Normalize OCR text and aliases for whitespace and case where appropriate.
2. Match by configured aliases.
3. Prefer exact or longest alias matches over shorter partial matches.
4. Mark multiple customer matches as ambiguous.
5. Mark no match as unmatched.

The first version does not use an LLM for customer recognition. Deterministic alias matching keeps upload decisions auditable.

## Microsoft Integration

Use Microsoft Graph with delegated personal-account OAuth.

Required capabilities:

- read Outlook messages and PDF attachments from the signed-in mailbox
- upload files to the configured SharePoint document library and folder
- check whether the target filename already exists before uploading

The implementation should prefer the least broad permissions that still work. If site-scoped SharePoint permissions are practical, prefer them over broad file access. If not, document the required permission set in `SKILL.md`.

OAuth tokens are cached locally. Secrets and tokens must not be committed to git.

## State And Idempotency

Each scan writes a local state file containing:

- stable candidate id
- Outlook message id
- attachment id or attachment name
- attachment hash if available
- OCR text excerpt or match evidence
- matched customer id
- planned SharePoint target
- upload status

The upload command updates the state file after each attempted upload.

Duplicate protection:

- skip or warn when a candidate was already uploaded in local history
- check SharePoint target existence before upload
- do not overwrite existing SharePoint files by default

## Error Handling

Expected errors should produce concise, actionable messages:

- Microsoft login required or expired
- Graph permission denied
- no candidate messages found
- PDF rendering/OCR failure
- no customer match
- ambiguous customer match
- invalid config
- SharePoint folder not found
- target filename already exists

The preview command should keep partial results when individual PDFs fail.

## Testing Strategy

Use test-first development for deterministic logic:

- config validation
- filename template rendering
- customer alias matching
- ambiguity detection
- duplicate target handling
- state-file read/write behavior

Mock or fake Microsoft Graph for unit tests. Live Microsoft Graph calls are not required for normal automated tests.

Provide a dry-run path so the workflow can be exercised without uploading.

## Non-Goals

- scheduled execution
- automatic upload without user preview and approval
- editing PDF content
- managing SharePoint folder creation in the first version
- learning new customer mappings automatically without user-edited YAML
- LLM-based customer recognition in the first version

## Implementation Choices

No open product decisions remain for the first implementation. Implementation may choose the exact Python packages for Graph, PDF rendering, and OCR based on what is available locally and compatible with Windows.
