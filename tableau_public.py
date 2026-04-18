"""
Tableau Public workbook field extraction.
Parses a Tableau Public URL, downloads the .twb XML, and returns the field list.
"""
import re
import xml.etree.ElementTree as ET
import requests

# Tableau XML datatype → app field type
DATATYPE_MAP = {
    "string":   "String",
    "integer":  "Number",
    "real":     "Number",
    "boolean":  "Boolean",
    "date":     "Date",
    "datetime": "Date",
}

# Tableau built-in fields that are never user-defined — skip them
SKIP_NAMES = {
    "[Number of Records]", "[Measure Names]", "[Measure Values]",
    "[:Measure Names]", "[:Measure Values]", "[]",
    "[Latitude (generated)]", "[Longitude (generated)]",
}

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def parse_tableau_public_url(url: str) -> dict | None:
    """
    Return {username, workbook_slug, view_name} from a Tableau Public URL.
    Handles new format (/app/profile/…) and old format (/views/…).
    Returns None if the URL is not recognisable.
    """
    url = url.strip()

    # New format: https://public.tableau.com/app/profile/{user}/viz/{wb}/{view}
    m = re.search(
        r"public\.tableau\.com/app/profile/([^/?#]+)/viz/([^/?#]+)(?:/([^/?#]+))?",
        url,
    )
    if m:
        return {
            "username":      m.group(1),
            "workbook_slug": m.group(2),
            "view_name":     m.group(3) or "",
        }

    # Old format: https://public.tableau.com/views/{wb}/{view}
    m = re.search(r"public\.tableau\.com/views/([^/?#]+)(?:/([^/?#]+))?", url)
    if m:
        return {
            "username":      None,
            "workbook_slug": m.group(1),
            "view_name":     m.group(2) or "",
        }

    # Profile-only URL — no specific workbook
    m = re.search(r"public\.tableau\.com/(?:app/)?profile/([^/?#]+)", url)
    if m:
        return {
            "username":      m.group(1),
            "workbook_slug": None,
            "view_name":     None,
        }

    return None


def fetch_profile_workbooks(username: str) -> list[dict]:
    """
    Return the list of workbooks published by a Tableau Public user.
    """
    api_url = (
        f"https://public.tableau.com/profile/api/{username}/workbooks"
        "?count=100&index=0"
    )
    resp = requests.get(api_url, headers=BROWSER_HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.json()


def fetch_twb_fields(workbook_slug: str) -> list[dict]:
    """
    Download a Tableau Public workbook's .twb XML and return its fields.
    Each field is {name: str, type: str}.
    """
    twb_url = f"https://public.tableau.com/workbooks/{workbook_slug}.twb"
    resp = requests.get(twb_url, headers=BROWSER_HEADERS, timeout=20)
    resp.raise_for_status()

    root = ET.fromstring(resp.content)

    fields = []
    seen: set[str] = set()

    for datasource in root.iter("datasource"):
        # Skip the built-in Parameters datasource
        if datasource.get("name") == "Parameters":
            continue

        for column in datasource.findall("column"):
            raw_name = column.get("name", "")

            # Skip system/internal fields
            if (
                raw_name in SKIP_NAMES
                or raw_name.startswith("[:]")
                or raw_name.startswith("[::")
                or not raw_name
            ):
                continue

            # Prefer caption (friendly name), else strip brackets
            caption = column.get("caption", "").strip()
            display_name = caption if caption else raw_name.strip("[]")

            if not display_name or display_name in seen:
                continue
            seen.add(display_name)

            datatype = column.get("datatype", "string")
            field_type = DATATYPE_MAP.get(datatype, "String")

            fields.append({"name": display_name, "type": field_type})

    return fields


def import_fields_from_url(url: str) -> dict:
    """
    Main entry point for the Tableau Public import feature.

    Returns:
        {
          "success":       bool,
          "fields":        list[{name, type}],
          "workbook_name": str | None,
          "error":         str | None,
        }
    """
    parsed = parse_tableau_public_url(url)

    if not parsed:
        return {
            "success": False,
            "fields": [],
            "workbook_name": None,
            "error": (
                "Couldn't parse this URL. Paste the full Tableau Public workbook URL — "
                "e.g. https://public.tableau.com/app/profile/yourname/viz/WorkbookName/ViewName"
            ),
        }

    workbook_slug = parsed.get("workbook_slug")
    username = parsed.get("username")

    # Profile-only URL: show available workbooks instead of failing silently
    if not workbook_slug and username:
        try:
            workbooks = fetch_profile_workbooks(username)
            names = [w.get("name") or w.get("contentUrl", "") for w in workbooks[:5]]
            names_str = ", ".join(f'"{n}"' for n in names if n)
            return {
                "success": False,
                "fields": [],
                "workbook_name": None,
                "error": (
                    f"That's a profile URL. Paste a specific workbook URL. "
                    f"Workbooks found for {username}: {names_str}"
                ),
            }
        except Exception:
            return {
                "success": False,
                "fields": [],
                "workbook_name": None,
                "error": "That looks like a profile URL. Paste a specific workbook URL instead.",
            }

    if not workbook_slug:
        return {
            "success": False,
            "fields": [],
            "workbook_name": None,
            "error": "Couldn't find a workbook slug in this URL.",
        }

    try:
        fields = fetch_twb_fields(workbook_slug)
        if not fields:
            return {
                "success": False,
                "fields": [],
                "workbook_name": workbook_slug,
                "error": (
                    "Workbook found but no fields were extracted. "
                    "The workbook may use a packaged extract (.twbx) that can't be read this way. "
                    "Try adding fields manually instead."
                ),
            }
        return {
            "success": True,
            "fields": fields,
            "workbook_name": workbook_slug,
            "error": None,
        }

    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "?"
        if status == 404:
            return {
                "success": False,
                "fields": [],
                "workbook_name": None,
                "error": (
                    f"Workbook not found (404). Check that the URL is correct and the "
                    f"workbook is published publicly on Tableau Public."
                ),
            }
        return {
            "success": False,
            "fields": [],
            "workbook_name": None,
            "error": f"HTTP {status} fetching workbook. It may not be publicly downloadable.",
        }

    except ET.ParseError:
        return {
            "success": False,
            "fields": [],
            "workbook_name": workbook_slug,
            "error": (
                "Downloaded the workbook file but couldn't parse it as XML. "
                "It may be a packaged workbook (.twbx). Try adding fields manually."
            ),
        }

    except Exception as e:
        return {
            "success": False,
            "fields": [],
            "workbook_name": None,
            "error": f"Unexpected error: {str(e)}",
        }
