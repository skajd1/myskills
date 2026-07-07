# Inspection Uploader Config Schema

Use one YAML or JSON file to map OCR customer names to SharePoint destinations and filename rules.

## Top-Level Fields

| Field | Required | Purpose |
| --- | --- | --- |
| `mail.sender_allowlist` | No | Scanner or service sender addresses to include. |
| `mail.subject_keywords` | No | Subject keywords such as `Scan Data`. |
| `mail.max_messages` | No | Maximum messages to inspect per scan. |
| `ocr.mode` | No | Default workflow is `codex_vision`, where Codex reads rendered first-page preview images. |
| `graph.client_id` | Live auth | Public-client app registration id for Microsoft OAuth. |
| `graph.tenant` | No | Tenant segment for authority. Default: `organizations`. |
| `graph.scopes` | No | Microsoft Graph delegated scopes. |
| `graph.token_cache` | No | Local MSAL token cache path. |
| `customers` | Yes | Customer mappings. Must contain at least one item. |

## Customer Fields

Each `customers` item requires:

| Field | Purpose |
| --- | --- |
| `id` | Stable machine id, lowercase recommended. |
| `display_name` | Human-readable customer name and `{customer}` filename value. |
| `document_label` | Optional filename label for a service/document under the customer. Defaults to `display_name`. |
| `aliases` | Names that may appear in OCR text. Longest alias wins. |
| `sharepoint.site_url` | SharePoint site URL. |
| `sharepoint.drive_name` | Document library or drive name. |
| `sharepoint.folder_path` | Target folder path inside the drive. |
| `sharepoint.folder_path_template` | Optional date/customer template for monthly folders; when present it overrides `folder_path` at candidate-build time. |
| `sharepoint.share_link` | Alternative to `site_url`/`drive_name`/`folder_path`; use a SharePoint folder sharing URL. |
| `filename_template` | Upload filename format. |

## Filename Templates

Supported variables:

| Variable | Example | Notes |
| --- | --- | --- |
| `{date:%Y%m%d}` | `20260624` | Uses Outlook received time. Any Python `strftime` format can be used after `:`. |
| `{year}` | `2026` | Four-digit year from the document/received date. Useful for folder paths. |
| `{month}` | `6` | Non-padded month number. Useful for folders named `6월`, `7월`, etc. |
| `{customer}` | `ACME Korea` | Uses `display_name`. |
| `{document_label}` | `재외국민_ocr` | Uses `document_label`, or `display_name` when omitted. |
| `{original_stem}` | `240620261348` | Original attachment filename without extension. |

Rendered filenames must not contain `/` or `\`.


## Monthly Folder Templates

For customers that create a new monthly SharePoint folder, use `sharepoint.folder_path_template` instead of hard-coding the month. Example:

```yaml
sharepoint:
  site_url: https://supportmetsakuur.sharepoint.com/sites/msteams_98957d
  drive_name: 문서
  folder_path: 고객사/정기점검보고서 스캔본/2026/6월
  folder_path_template: 고객사/정기점검보고서 스캔본/{year}/{month}월
```

When the candidate date is in July 2026, the target folder becomes `고객사/정기점검보고서 스캔본/2026/7월`.

## Customer Recognition

Default mode does not require Tesseract or another OCR engine. The CLI renders the first page of each scanned PDF to a PNG and records it as `preview_image`. Codex opens that image, reads the customer name from the page, then runs `set-customer` to apply the matching configured customer.

The deterministic alias matcher is still available for text inputs and future OCR engines. If aliases from multiple customers match with the same longest length, the row is ambiguous and must not be uploaded automatically.

## Microsoft OAuth

Use delegated device-code OAuth. Do not store Microsoft account passwords in this config.

Default scopes:

- `Mail.Read`
- `Files.ReadWrite.All`
- `Sites.ReadWrite.All`
- `User.Read`

`graph.client_id` must refer to an app registration that allows public-client/device-code authentication and has the required delegated Graph permissions.
