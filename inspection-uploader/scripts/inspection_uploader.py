from __future__ import annotations

import argparse
import base64
import datetime as _dt
import json
import pathlib
import re
import sys
import urllib.parse
import webbrowser


DEFAULT_GRAPH_SCOPES = ["Mail.Read", "Files.ReadWrite.All", "Sites.ReadWrite.All", "User.Read"]
DEFAULT_TOKEN_CACHE = str(pathlib.Path.home() / ".codex" / "inspection-uploader" / "msal_token_cache.bin")


def validate_config(config: dict) -> list[str]:
    errors: list[str] = []
    customers = config.get("customers")
    if not isinstance(customers, list) or not customers:
        return ["customers must contain at least one customer"]

    required_customer_fields = ("id", "display_name", "filename_template")
    required_sharepoint_fields = ("site_url", "drive_name", "folder_path")

    for index, customer in enumerate(customers):
        prefix = f"customers[{index}]"
        if not isinstance(customer, dict):
            errors.append(f"{prefix} must be an object")
            continue

        for field in required_customer_fields:
            if not customer.get(field):
                errors.append(f"{prefix}.{field} is required")

        aliases = customer.get("aliases")
        if not isinstance(aliases, list) or not any(str(alias).strip() for alias in aliases):
            errors.append(f"{prefix}.aliases must contain at least one alias")

        sharepoint = customer.get("sharepoint")
        if not isinstance(sharepoint, dict):
            sharepoint = {}
        if not sharepoint.get("share_link"):
            for field in required_sharepoint_fields:
                if not sharepoint.get(field):
                    errors.append(f"{prefix}.sharepoint.{field} is required")

    return errors


def get_graph_settings(config: dict) -> dict:
    graph = config.get("graph") or {}
    client_id = graph.get("client_id")
    if not client_id:
        raise ValueError("graph.client_id is required for Microsoft OAuth")
    tenant = graph.get("tenant", "organizations")
    scopes = graph.get("scopes") or DEFAULT_GRAPH_SCOPES
    return {
        "client_id": client_id,
        "tenant": tenant,
        "authority": f"https://login.microsoftonline.com/{tenant}",
        "scopes": scopes,
        "token_cache": graph.get("token_cache", DEFAULT_TOKEN_CACHE),
    }


def graph_headers(access_token: str) -> dict:
    return {"Authorization": f"Bearer {access_token}"}


def graph_url(path: str) -> str:
    if path.startswith("https://"):
        return path
    return "https://graph.microsoft.com/v1.0/" + path.lstrip("/")


def graph_get(session, access_token: str, path: str, *, params: dict | None = None) -> dict:
    response = session.get(graph_url(path), headers=graph_headers(access_token), params=params)
    response.raise_for_status()
    return response.json()


def graph_put_bytes(session, access_token: str, path: str, content: bytes, content_type: str) -> dict:
    headers = graph_headers(access_token)
    headers["Content-Type"] = content_type
    response = session.put(graph_url(path), headers=headers, data=content)
    response.raise_for_status()
    return response.json()


def parse_sharepoint_site_url(site_url: str) -> tuple[str, str]:
    parsed = urllib.parse.urlparse(site_url)
    if not parsed.hostname or not parsed.path:
        raise ValueError(f"invalid SharePoint site_url: {site_url}")
    return parsed.hostname, parsed.path.rstrip("/")


def drive_root_path(drive_id: str, folder_path: str) -> str:
    escaped = "/".join(urllib.parse.quote(part) for part in folder_path.strip("/").split("/") if part)
    return f"/drives/{drive_id}/root:/{escaped}"


def encode_share_url(share_url: str) -> str:
    encoded = base64.urlsafe_b64encode(share_url.encode("utf-8")).decode("ascii").rstrip("=")
    return f"u!{encoded}"


def decode_file_attachment(attachment: dict) -> bytes:
    if attachment.get("@odata.type") != "#microsoft.graph.fileAttachment":
        raise ValueError("only fileAttachment objects can be decoded")
    content = attachment.get("contentBytes")
    if not content:
        raise ValueError("fileAttachment contentBytes is missing")
    return base64.b64decode(content)


def message_summary(message: dict) -> dict:
    email = (
        message.get("sender", {})
        .get("emailAddress", {})
        .get("address", "")
    )
    return {
        "id": message.get("id", ""),
        "received_at": message.get("receivedDateTime", ""),
        "sender": email,
        "subject": message.get("subject", ""),
    }


def is_pdf_attachment(attachment: dict) -> bool:
    return (
        attachment.get("@odata.type") == "#microsoft.graph.fileAttachment"
        and str(attachment.get("name", "")).casefold().endswith(".pdf")
    )


def list_recent_messages(session, access_token: str, *, since_days: int, max_messages: int) -> list[dict]:
    since = (_dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(days=since_days)).replace(microsecond=0)
    params = {
        "$select": "id,receivedDateTime,sender,subject,hasAttachments",
        "$top": max_messages,
        "$orderby": "receivedDateTime desc",
        "$filter": f"receivedDateTime ge {since.isoformat().replace('+00:00', 'Z')} and hasAttachments eq true",
    }
    return graph_get(session, access_token, "/me/messages", params=params).get("value", [])


def list_message_attachments(session, access_token: str, message_id: str) -> list[dict]:
    return graph_get(session, access_token, f"/me/messages/{message_id}/attachments").get("value", [])


def get_message_attachment(session, access_token: str, message_id: str, attachment_id: str) -> dict:
    return graph_get(session, access_token, f"/me/messages/{message_id}/attachments/{attachment_id}")


def find_customer_by_id(customers: list[dict], customer_id: str) -> dict | None:
    for customer in customers:
        if customer.get("id") == customer_id:
            return customer
    return None


def resolve_site(session, access_token: str, site_url: str) -> dict:
    hostname, path = parse_sharepoint_site_url(site_url)
    return graph_get(session, access_token, f"/sites/{hostname}:{path}")


def resolve_drive(session, access_token: str, site_id: str, drive_name: str) -> dict:
    drives = graph_get(session, access_token, f"/sites/{site_id}/drives").get("value", [])
    for drive in drives:
        if str(drive.get("name", "")).casefold() == drive_name.casefold():
            return drive
    raise ValueError(f"SharePoint drive not found: {drive_name}")


def resolve_folder(session, access_token: str, drive_id: str, folder_path: str) -> dict:
    return graph_get(session, access_token, drive_root_path(drive_id, folder_path))


def resolve_target_folder(session, access_token: str, target: dict) -> dict:
    if target.get("share_link"):
        item = graph_get(session, access_token, f"/shares/{encode_share_url(target['share_link'])}/driveItem")
        drive_id = item.get("parentReference", {}).get("driveId")
        if not drive_id:
            raise ValueError("shared folder did not include parentReference.driveId")
        return {"drive_id": drive_id, "folder_id": item["id"], "folder_path": ""}

    site = resolve_site(session, access_token, target["site_url"])
    drive = resolve_drive(session, access_token, site["id"], target["drive_name"])
    folder = resolve_folder(session, access_token, drive["id"], target["folder_path"])
    return {"drive_id": drive["id"], "folder_id": folder["id"], "folder_path": target["folder_path"]}


def target_file_exists(session, access_token: str, drive_id: str, folder_path: str, filename: str) -> bool:
    path = drive_root_path(drive_id, f"{folder_path.rstrip('/')}/{filename}")
    try:
        graph_get(session, access_token, path)
        return True
    except Exception:
        return False


def upload_candidate(session, access_token: str, row: dict) -> dict:
    if row.get("upload_status") != "pending":
        row.setdefault("warnings", []).append("candidate is not pending")
        row["upload_status"] = "skipped"
        return row

    target = row["target"]
    attachment = get_message_attachment(
        session,
        access_token,
        row["message"]["id"],
        row["attachment"]["id"],
    )
    content = decode_file_attachment(attachment)
    filename = target["filename"]

    if target.get("share_link"):
        folder = resolve_target_folder(session, access_token, target)
        drive_id = folder["drive_id"]
    else:
        site = resolve_site(session, access_token, target["site_url"])
        drive = resolve_drive(session, access_token, site["id"], target["drive_name"])
        drive_id = drive["id"]
        if target_file_exists(session, access_token, drive_id, target["folder_path"], filename):
            row.setdefault("warnings", []).append("target file already exists; not overwriting")
            row["upload_status"] = "skipped"
            return row
        folder_item = resolve_folder(session, access_token, drive_id, target["folder_path"])
        folder = {"drive_id": drive_id, "folder_id": folder_item["id"], "folder_path": target["folder_path"]}

    upload_path = f"/drives/{drive_id}/items/{folder['folder_id']}:/{urllib.parse.quote(filename)}:/content"
    result = graph_put_bytes(session, access_token, upload_path, content, "application/pdf")
    row["upload_status"] = "uploaded"
    row["upload_result"] = {"id": result.get("id"), "name": result.get("name")}
    return row


def extract_first_page_text(pdf_bytes: bytes, *, language: str) -> str:
    try:
        import pytesseract  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "OCR requires pytesseract and a Tesseract executable on PATH."
        ) from exc

    try:
        import pypdfium2 as pdfium  # type: ignore
    except ImportError as exc:
        raise RuntimeError("PDF rendering requires pypdfium2.") from exc

    document = pdfium.PdfDocument(pdf_bytes)
    if len(document) == 0:
        return ""
    bitmap = document[0].render(scale=2).to_pil()
    return pytesseract.image_to_string(bitmap, lang=language)


def render_first_page_preview(pdf_bytes: bytes, output_path: str | pathlib.Path) -> None:
    try:
        import pypdfium2 as pdfium  # type: ignore
    except ImportError as exc:
        raise RuntimeError("PDF rendering requires pypdfium2.") from exc

    target = pathlib.Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    document = pdfium.PdfDocument(pdf_bytes)
    if len(document) == 0:
        raise ValueError("PDF has no pages")
    image = document[0].render(scale=2).to_pil()
    image.save(target)


def scan_outlook_candidates(config: dict, *, since_days: int, session, preview_dir: str | pathlib.Path) -> dict:
    token = acquire_graph_token(config, interactive=False)
    mail = config.get("mail") or {}
    sender_allowlist = {str(sender).casefold() for sender in mail.get("sender_allowlist", [])}
    subject_keywords = [str(keyword).casefold() for keyword in mail.get("subject_keywords", [])]
    max_messages = int(mail.get("max_messages", 50))
    customers = config.get("customers", [])

    candidates = []
    warnings = []

    for message in list_recent_messages(session, token, since_days=since_days, max_messages=max_messages):
        summary = message_summary(message)
        if sender_allowlist and summary["sender"].casefold() not in sender_allowlist:
            continue
        if subject_keywords and not any(keyword in summary["subject"].casefold() for keyword in subject_keywords):
            continue

        for attachment in list_message_attachments(session, token, summary["id"]):
            if not is_pdf_attachment(attachment):
                continue
            try:
                pdf_bytes = decode_file_attachment(attachment)
                safe_id = re.sub(r"[^A-Za-z0-9_.-]+", "_", f"{summary['id']}_{attachment.get('id', '')}")
                preview_path = pathlib.Path(preview_dir) / f"{safe_id}.png"
                render_first_page_preview(pdf_bytes, preview_path)
                candidates.append(
                    build_codex_vision_candidate(
                        summary,
                        {"id": attachment.get("id", ""), "filename": attachment.get("name", "")},
                        str(preview_path),
                    )
                )
            except Exception as exc:
                candidates.append(
                    {
                        "id": f"{summary['id']}:{attachment.get('id', '')}",
                        "message": summary,
                        "attachment": {"id": attachment.get("id", ""), "filename": attachment.get("name", "")},
                        "match": {"status": "error", "customer_id": None, "evidence": ""},
                        "target": {},
                        "upload_status": "blocked",
                        "warnings": [str(exc)],
                    }
                )

    return {"candidates": candidates, "warnings": warnings}


def acquire_graph_token(config: dict, *, interactive: bool) -> str:
    settings = get_graph_settings(config)
    try:
        import msal  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Microsoft OAuth requires the 'msal' Python package.") from exc

    cache_path = pathlib.Path(settings["token_cache"])
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache = msal.SerializableTokenCache()
    if cache_path.exists():
        cache.deserialize(cache_path.read_text(encoding="utf-8"))

    app = msal.PublicClientApplication(
        settings["client_id"],
        authority=settings["authority"],
        token_cache=cache,
    )

    result = None
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(settings["scopes"], account=accounts[0])

    if not result and interactive:
        flow = app.initiate_device_flow(scopes=settings["scopes"])
        if "user_code" not in flow:
            raise RuntimeError(f"Device-code flow failed: {json.dumps(flow, ensure_ascii=False)}")
        print(flow["message"])
        sys.stdout.flush()
        result = app.acquire_token_by_device_flow(flow)

    if cache.has_state_changed:
        cache_path.write_text(cache.serialize(), encoding="utf-8")

    if not result or "access_token" not in result:
        error = (result or {}).get("error", "no_token")
        description = (result or {}).get("error_description", "Run auth to sign in.")
        raise RuntimeError(f"Token acquisition failed: {error}: {description}")
    return result["access_token"]


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold()).strip()


def match_customer(text: str, customers: list[dict]) -> dict:
    normalized_text = _normalize_text(text)
    matches: list[dict] = []

    for customer in customers:
        for alias in customer.get("aliases", []):
            alias_text = str(alias).strip()
            if not alias_text:
                continue
            if _normalize_text(alias_text) in normalized_text:
                matches.append(
                    {
                        "customer_id": customer.get("id"),
                        "display_name": customer.get("display_name"),
                        "alias": alias_text,
                        "alias_length": len(alias_text),
                    }
                )

    if not matches:
        return {"status": "unmatched", "customer_id": None, "evidence": ""}

    longest_length = max(match["alias_length"] for match in matches)
    longest_matches = [match for match in matches if match["alias_length"] == longest_length]
    customer_ids = {match["customer_id"] for match in longest_matches}
    if len(customer_ids) > 1:
        evidence = ", ".join(sorted({match["alias"] for match in longest_matches}))
        return {"status": "ambiguous", "customer_id": None, "evidence": evidence}

    best = longest_matches[0]
    return {
        "status": "matched",
        "customer_id": best["customer_id"],
        "evidence": best["alias"],
    }


class _TemplateValues:
    def __init__(self, received_at: str, customer_name: str, original_filename: str, document_label: str = ""):
        self.date = _dt.datetime.fromisoformat(received_at.replace("Z", "+00:00"))
        self.year = str(self.date.year)
        self.month = str(self.date.month)
        self.customer = customer_name
        self.document_label = document_label or customer_name
        self.original_stem = pathlib.Path(original_filename).stem

    def __getitem__(self, key: str):
        if key == "date":
            return self.date
        if key == "year":
            return self.year
        if key == "month":
            return self.month
        if key == "customer":
            return self.customer
        if key == "document_label":
            return self.document_label
        if key == "original_stem":
            return self.original_stem
        raise KeyError(key)


def render_template(
    template: str,
    *,
    received_at: str,
    customer_name: str,
    document_label: str = "",
    original_filename: str,
) -> str:
    return template.format_map(
        _TemplateValues(
            received_at=received_at,
            customer_name=customer_name,
            document_label=document_label,
            original_filename=original_filename,
        )
    )


def render_filename(
    template: str,
    *,
    received_at: str,
    customer_name: str,
    document_label: str = "",
    original_filename: str,
) -> str:
    rendered = render_template(
        template,
        received_at=received_at,
        customer_name=customer_name,
        document_label=document_label,
        original_filename=original_filename,
    )
    if "/" in rendered or "\\" in rendered:
        raise ValueError("rendered filename must not contain path separators")
    return rendered

def write_state(path: str | pathlib.Path, state: dict) -> None:
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def read_state(path: str | pathlib.Path) -> dict:
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def target_manual_upload_url(target: dict) -> str:
    if target.get("page_url"):
        return str(target["page_url"])
    if target.get("share_link"):
        return str(target["share_link"])
    site_url = str(target.get("site_url", "")).rstrip("/")
    folder_path = str(target.get("folder_path", "")).strip("/")
    if not site_url or not folder_path:
        return ""
    encoded_folder = urllib.parse.quote("/" + folder_path, safe="")
    return f"{site_url}/Shared%20Documents/Forms/AllItems.aspx?id={encoded_folder}"


def selected_candidate_rows(state: dict, ids: str) -> list[dict]:
    requested_ids = {item.strip() for item in ids.split(",") if item.strip()}
    if not requested_ids:
        raise ValueError("--ids must contain at least one candidate id")
    rows = [row for row in state.get("candidates", []) if row.get("id") in requested_ids]
    missing = requested_ids - {row.get("id") for row in rows}
    if missing:
        raise ValueError(f"candidate id not found: {', '.join(sorted(missing))}")
    return rows


def build_preview_candidate(
    message: dict,
    attachment: dict,
    customer: dict,
    match: dict,
) -> dict:
    filename = render_filename(
        customer["filename_template"],
        received_at=message["received_at"],
        customer_name=customer["display_name"],
        document_label=customer.get("document_label", customer["display_name"]),
        original_filename=attachment["filename"],
    )
    sharepoint = customer["sharepoint"]
    target = {"filename": filename}
    if sharepoint.get("share_link"):
        target["share_link"] = sharepoint["share_link"]
    else:
        folder_path_template = sharepoint.get("folder_path_template") or sharepoint["folder_path"]
        folder_path = render_template(
            folder_path_template,
            received_at=message["received_at"],
            customer_name=customer["display_name"],
            document_label=customer.get("document_label", customer["display_name"]),
            original_filename=attachment["filename"],
        )
        target.update(
            {
                "site_url": sharepoint["site_url"],
                "drive_name": sharepoint["drive_name"],
                "folder_path": folder_path,
            }
        )
        if sharepoint.get("folder_path_template"):
            target["folder_path_template"] = sharepoint["folder_path_template"]
    return {
        "id": f"{message['id']}:{attachment['id']}",
        "message": {
            "id": message["id"],
            "received_at": message["received_at"],
            "sender": message.get("sender", ""),
            "subject": message.get("subject", ""),
        },
        "attachment": {
            "id": attachment["id"],
            "filename": attachment["filename"],
        },
        "match": match,
        "target": target,
        "upload_status": "pending",
    }


def build_codex_vision_candidate(message: dict, attachment: dict, preview_image: str) -> dict:
    return {
        "id": f"{message['id']}:{attachment['id']}",
        "message": {
            "id": message["id"],
            "received_at": message["received_at"],
            "sender": message.get("sender", ""),
            "subject": message.get("subject", ""),
        },
        "attachment": {
            "id": attachment["id"],
            "filename": attachment["filename"],
        },
        "match": {"status": "needs_codex_vision", "customer_id": None, "evidence": ""},
        "target": {},
        "preview_image": preview_image,
        "upload_status": "blocked",
        "warnings": ["Codex must inspect preview_image and assign a customer before upload."],
    }


def apply_customer_to_candidate(
    state: dict,
    candidate_id: str,
    customers: list[dict],
    customer_id: str,
    *,
    evidence: str,
) -> dict:
    customer = find_customer_by_id(customers, customer_id)
    if customer is None:
        raise ValueError(f"customer id not found: {customer_id}")

    for row in state.get("candidates", []):
        if row.get("id") != candidate_id:
            continue
        updated = build_preview_candidate(
            row["message"],
            row["attachment"],
            customer,
            {"status": "matched_by_codex", "customer_id": customer_id, "evidence": evidence},
        )
        if "preview_image" in row:
            updated["preview_image"] = row["preview_image"]
        row.clear()
        row.update(updated)
        return state

    raise ValueError(f"candidate id not found: {candidate_id}")


def load_config(path: str | pathlib.Path) -> dict:
    source = pathlib.Path(path)
    text = source.read_text(encoding="utf-8")
    if source.suffix.casefold() == ".json":
        return json.loads(text)

    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "YAML config requires PyYAML. Install it or use a .json config file."
        ) from exc
    loaded = yaml.safe_load(text)
    if not isinstance(loaded, dict):
        raise ValueError("config root must be an object")
    return loaded


def build_initial_config(*, account_email: str = "") -> dict:
    return {
        "mail": {
            "sender_allowlist": ["scanner@example.com"],
            "subject_keywords": ["Scan Data"],
            "max_messages": 50,
        },
        "ocr": {"mode": "codex_vision"},
        "graph": {
            "account_email": account_email,
            "client_id": "00000000-0000-0000-0000-000000000000",
            "tenant": "organizations",
            "scopes": DEFAULT_GRAPH_SCOPES,
        },
        "customers": [
            {
                "id": "customer-id",
                "display_name": "Customer Name",
                "aliases": ["Customer Name"],
                "sharepoint": {
                    "site_url": "https://tenant.sharepoint.com/sites/Inspection",
                    "drive_name": "Documents",
                    "folder_path": "Customers/Customer Name/Inspection",
                },
                "filename_template": "{date:%Y%m%d}_{customer}_{original_stem}.pdf",
            }
        ],
    }


def write_initial_config(path: str | pathlib.Path, *, account_email: str = "") -> None:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise RuntimeError("init-config requires PyYAML.") from exc
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        yaml.safe_dump(build_initial_config(account_email=account_email), sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def _cmd_validate_config(args: argparse.Namespace) -> int:
    try:
        config = load_config(args.config)
    except Exception as exc:
        print(f"Config load failed: {exc}", file=sys.stderr)
        return 2

    errors = validate_config(config)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Config OK")
    return 0


def _cmd_init_config(args: argparse.Namespace) -> int:
    try:
        target = pathlib.Path(args.out)
        if target.exists() and not args.force:
            print(f"Config already exists: {target}. Use --force to overwrite.", file=sys.stderr)
            return 1
        write_initial_config(target, account_email=args.account_email)
    except Exception as exc:
        print(f"Init config failed: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote config template: {target}")
    return 0


def _cmd_show(args: argparse.Namespace) -> int:
    state = read_state(args.state)
    candidates = state.get("candidates", [])
    if not candidates:
        print("No candidates in state.")
        return 0

    print("ID | Received | Sender | Customer | Target | Link | Status")
    print("-- | -------- | ------ | -------- | ------ | ---- | ------")
    for row in candidates:
        message = row.get("message", {})
        match = row.get("match", {})
        target = row.get("target", {})
        target_path = "/".join(
            part
            for part in [target.get("folder_path", ""), target.get("filename", "")]
            if part
        )
        print(
            " | ".join(
                [
                    str(row.get("id", "")),
                    str(message.get("received_at", "")),
                    str(message.get("sender", "")),
                    str(match.get("customer_id") or match.get("status", "")),
                    target_path,
                    target_manual_upload_url(target),
                    str(row.get("upload_status", "")),
                ]
            )
        )
    return 0


def _cmd_not_configured(command: str) -> int:
    print(
        f"{command} is not configured yet. Configure Microsoft Graph OAuth, "
        "PDF rendering, and OCR dependencies before live Outlook/SharePoint use.",
        file=sys.stderr,
    )
    return 3


def _cmd_auth(args: argparse.Namespace) -> int:
    try:
        config = load_config(args.config)
        acquire_graph_token(config, interactive=True)
    except Exception as exc:
        print(f"Auth failed: {exc}", file=sys.stderr)
        return 1
    print("Auth OK")
    return 0


def _cmd_scan(args: argparse.Namespace) -> int:
    try:
        import requests

        config = load_config(args.config)
        errors = validate_config(config)
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        preview_dir = pathlib.Path(args.out).with_suffix("")
        state = scan_outlook_candidates(
            config,
            since_days=args.since_days,
            session=requests.Session(),
            preview_dir=preview_dir,
        )
        write_state(args.out, state)
    except Exception as exc:
        print(f"Scan failed: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote scan state: {args.out}")
    return 0


def _cmd_set_customer(args: argparse.Namespace) -> int:
    try:
        config = load_config(args.config)
        state = read_state(args.state)
        updated = apply_customer_to_candidate(
            state,
            args.id,
            config.get("customers", []),
            args.customer_id,
            evidence=args.evidence,
        )
        write_state(args.state, updated)
    except Exception as exc:
        print(f"Set customer failed: {exc}", file=sys.stderr)
        return 1
    print(f"Updated candidate {args.id} with customer {args.customer_id}")
    return 0


def _cmd_open_targets(args: argparse.Namespace) -> int:
    try:
        state = read_state(args.state)
        rows = selected_candidate_rows(state, args.ids)
        for row in rows:
            target = row.get("target", {})
            url = target_manual_upload_url(target)
            filename = target.get("filename", "")
            if not url:
                print(f"No target URL for {row.get('id', '')}", file=sys.stderr)
                return 1
            print(f"{row.get('id', '')} | {filename} | {url}")
            if args.open:
                webbrowser.open(url)
    except Exception as exc:
        print(f"Open target failed: {exc}", file=sys.stderr)
        return 1
    return 0


def _cmd_upload(args: argparse.Namespace) -> int:
    try:
        import requests

        config = load_config(args.config)
        state = read_state(args.state)
        requested_ids = {item.strip() for item in args.ids.split(",") if item.strip()}
        if not requested_ids:
            print("Upload failed: --ids must contain at least one candidate id", file=sys.stderr)
            return 1
        token = acquire_graph_token(config, interactive=False)
        session = requests.Session()
        for row in state.get("candidates", []):
            if row.get("id") in requested_ids:
                upload_candidate(session, token, row)
        write_state(args.state, state)
    except Exception as exc:
        print(f"Upload failed: {exc}", file=sys.stderr)
        return 1
    print(f"Updated upload state: {args.state}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preview Outlook inspection PDFs and upload approved files to SharePoint."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    auth = subparsers.add_parser("auth", help="Run Microsoft OAuth sign-in.")
    auth.add_argument("--config", required=True, help="Path to YAML or JSON config with graph.client_id.")
    auth.set_defaults(func=_cmd_auth)

    init_config = subparsers.add_parser("init-config", help="Write a starter config file.")
    init_config.add_argument("--out", required=True, help="Path to write YAML config.")
    init_config.add_argument("--account-email", default="", help="Expected Outlook account email metadata.")
    init_config.add_argument("--force", action="store_true", help="Overwrite an existing config file.")
    init_config.set_defaults(func=_cmd_init_config)

    validate = subparsers.add_parser("validate-config", help="Validate customer metadata config.")
    validate.add_argument("--config", required=True, help="Path to YAML or JSON config.")
    validate.set_defaults(func=_cmd_validate_config)

    scan = subparsers.add_parser("scan", help="Fetch Outlook candidates and write preview state.")
    scan.add_argument("--config", required=True, help="Path to YAML or JSON config.")
    scan.add_argument("--since-days", type=int, default=7, help="How many days of mail to inspect.")
    scan.add_argument("--out", required=True, help="Path to write scan state JSON.")
    scan.set_defaults(func=_cmd_scan)

    show = subparsers.add_parser("show", help="Print a compact preview table from state.")
    show.add_argument("--state", required=True, help="Path to scan state JSON.")
    show.set_defaults(func=_cmd_show)

    open_targets = subparsers.add_parser("open-targets", help="Print or open SharePoint target folders for manual upload.")
    open_targets.add_argument("--state", required=True, help="Path to scan state JSON.")
    open_targets.add_argument("--ids", required=True, help="Comma-separated candidate ids to open.")
    open_targets.add_argument("--open", action="store_true", help="Open target folders in the default browser.")
    open_targets.set_defaults(func=_cmd_open_targets)

    upload = subparsers.add_parser("upload", help="Upload selected candidate ids.")
    upload.add_argument("--config", required=True, help="Path to YAML or JSON config.")
    upload.add_argument("--state", required=True, help="Path to scan state JSON.")
    upload.add_argument("--ids", required=True, help="Comma-separated candidate ids to upload.")
    upload.set_defaults(func=_cmd_upload)

    set_customer = subparsers.add_parser("set-customer", help="Assign a customer after Codex inspects preview_image.")
    set_customer.add_argument("--config", required=True, help="Path to YAML or JSON config.")
    set_customer.add_argument("--state", required=True, help="Path to scan state JSON.")
    set_customer.add_argument("--id", required=True, help="Candidate id to update.")
    set_customer.add_argument("--customer-id", required=True, help="Configured customer id.")
    set_customer.add_argument("--evidence", default="Codex inspected first-page preview image.")
    set_customer.set_defaults(func=_cmd_set_customer)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
