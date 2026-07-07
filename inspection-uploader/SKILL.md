---
name: inspection-uploader
description: Use when the user wants Codex to process scanned inspection PDF emails from Outlook, identify the customer, preview candidates, or upload approved files to SharePoint.
---

# Inspection Uploader

Use this skill for on-demand inspection document intake from Outlook to SharePoint. Default UX is to prepare renamed PDFs and open the correct SharePoint folder for manual upload; direct Graph upload is optional only when admin consent is available.

## Required Workflow

1. Locate the config file. If the user does not provide one, create a starter config:

```powershell
& 'C:\Users\wooch\AppData\Local\Programs\Python\Python313\python.exe' 'C:\Users\wooch\.codex\skills\inspection-uploader\scripts\inspection_uploader.py' init-config --out 'C:\Users\wooch\.codex\inspection-uploader\config.yaml' --account-email <outlook-email>
```

Then ask the user to fill `graph.client_id` and each customer SharePoint mapping. A customer target may use either `sharepoint.site_url` + `drive_name` + `folder_path`, `site_url` + `drive_name` + `folder_path_template` for monthly folders, or a folder `sharepoint.share_link`.
2. For live Outlook/SharePoint use, ensure the config has `graph.client_id`. Never put the user's Microsoft password into any command, file, or script. Use device-code OAuth:

```powershell
& 'C:\Users\wooch\AppData\Local\Programs\Python\Python313\python.exe' 'C:\Users\wooch\.codex\skills\inspection-uploader\scripts\inspection_uploader.py' auth --config <config-path>
```

3. Run config validation:

```powershell
& 'C:\Users\wooch\AppData\Local\Programs\Python\Python313\python.exe' 'C:\Users\wooch\.codex\skills\inspection-uploader\scripts\inspection_uploader.py' validate-config --config <config-path>
```

4. Run scan when live dependencies are configured. This downloads PDF attachments and renders each first page to a `preview_image` PNG for Codex inspection:

```powershell
& 'C:\Users\wooch\AppData\Local\Programs\Python\Python313\python.exe' 'C:\Users\wooch\.codex\skills\inspection-uploader\scripts\inspection_uploader.py' scan --config <config-path> --since-days 7 --out <state-path>
```

5. Show candidates:

```powershell
& 'C:\Users\wooch\AppData\Local\Programs\Python\Python313\python.exe' 'C:\Users\wooch\.codex\skills\inspection-uploader\scripts\inspection_uploader.py' show --state <state-path>
```

6. For rows with `match.status = needs_codex_vision`, open each `preview_image`, read the customer name from the first page yourself, and assign the configured customer:

```powershell
& 'C:\Users\wooch\AppData\Local\Programs\Python\Python313\python.exe' 'C:\Users\wooch\.codex\skills\inspection-uploader\scripts\inspection_uploader.py' set-customer --config <config-path> --state <state-path> --id <candidate-id> --customer-id <customer-id> --evidence "Codex read the first-page preview image."
```

7. Show candidates again and ask the user which candidate IDs to handle. Do not proceed with unmatched, ambiguous, or `needs_codex_vision` rows.
8. For the normal/manual workflow, open the approved rows' SharePoint target folder links and let the user upload the prepared PDFs:

```powershell
& 'C:\Users\wooch\AppData\Local\Programs\Python\Python313\python.exe' 'C:\Users\wooch\.codex\skills\inspection-uploader\scripts\inspection_uploader.py' open-targets --state <state-path> --ids <id,id> --open
```

9. Tell the user the prepared local PDF path and the opened SharePoint folder. If admin-approved Graph upload is later enabled, `upload --config <config-path> --state <state-path> --ids <id,id>` remains available as an optional command.

## Safety Rules

- Never directly upload without showing the preview and receiving explicit user approval. The default workflow only opens the target folder for manual upload.
- Never overwrite an existing SharePoint file by default.
- Treat OCR customer matching as evidence, not certainty.
- Stop and ask for config updates when there is no match or multiple customer matches.
- Keep OAuth tokens, tenant secrets, and generated state files out of git.
- Do not use username/password auth. Microsoft documents device-code and interactive OAuth as the secure public-client options.
- Do not require Tesseract or another OCR engine for the default workflow. Codex should inspect generated first-page preview images directly.

## Config Reference

Read `references/config-schema.md` when creating or editing the metadata file. Use `assets/config.example.yaml` as a starting point.

Filename and folder-path templates may use `{date:%Y%m%d}`, `{year}`, `{month}`, `{customer}`, `{document_label}`, and `{original_stem}`.

## Current Live Integration Status

The bundled CLI includes tested deterministic logic for config validation, alias matching, filename rendering, preview row construction, Codex-assisted customer assignment, state files, Graph request helpers, OAuth config, and command routing. Live scan requires Microsoft Graph permissions and renders first-page images for Codex review instead of requiring an external OCR engine.
