from __future__ import annotations

from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
import hashlib
import json


MODEL_FILES_URL = "https://www.dinoloket.nl/modelbestanden-aanvragen"
OFFICIAL_HOSTS = {"www.dinoloket.nl", "dinoloket.nl", "www.tno.nl", "tno.nl"}
MARKERS = (
    "GeoTOP",
    "modelbestanden",
    "referentielijst",
    "referentielijsten",
    "lithoklasse",
    "geologische eenheid",
    "download",
    "zip",
    "csv",
    "xlsx",
    "aanvragen",
)


@dataclass(frozen=True)
class GeoTopModelFilesPageConfig:
    url: str = MODEL_FILES_URL
    max_response_bytes: int = 3_000_000
    timeout_s: int = 60
    user_agent: str = "wdm-lhm-geotop-model-files/0.8 (+research; inspect official page only; no form submit)"

    def as_dict(self) -> dict:
        return asdict(self)


class _PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []
        self.forms: list[dict] = []
        self._form: dict | None = None

    def handle_starttag(self, tag: str, attrs) -> None:
        attrs_dict = {str(k).lower(): ("" if v is None else str(v)) for k, v in attrs}
        lower = tag.lower()
        if lower == "a" and attrs_dict.get("href"):
            self.hrefs.append(attrs_dict["href"])
            return
        if lower == "form":
            self._form = {
                "action": attrs_dict.get("action", ""),
                "method": attrs_dict.get("method", "get").lower(),
                "id": attrs_dict.get("id", ""),
                "input_names": [],
            }
            return
        if lower in {"input", "select", "textarea", "button"} and self._form is not None:
            name = attrs_dict.get("name", "")
            if name and name not in self._form["input_names"]:
                self._form["input_names"].append(name)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "form" and self._form is not None:
            self.forms.append(self._form)
            self._form = None


class GeoTopModelFilesPageClient:
    def __init__(
        self,
        timeout_s: int,
        user_agent: str,
        get_transport: Callable[[str, dict[str, str], int, int], tuple[bytes, dict[str, str], str]] | None = None,
    ) -> None:
        self.timeout_s = timeout_s
        self.user_agent = user_agent
        self.get_transport = get_transport or self._get

    @staticmethod
    def _get(url: str, headers: dict[str, str], timeout_s: int, max_bytes: int) -> tuple[bytes, dict[str, str], str]:
        req = Request(url, headers=headers, method="GET")
        with urlopen(req, timeout=timeout_s) as response:
            payload = response.read(max_bytes + 1)
            if len(payload) > max_bytes:
                raise ValueError(f"GeoTOP model-files page exceeds guardrail: > {max_bytes} bytes")
            return payload, {k.lower(): v for k, v in response.headers.items()}, response.geturl()

    def get(self, url: str, *, max_bytes: int) -> tuple[bytes, dict[str, str], str]:
        return self.get_transport(
            url,
            {"User-Agent": self.user_agent, "Accept": "text/html,*/*"},
            self.timeout_s,
            max_bytes,
        )


def _validate_config(cfg: GeoTopModelFilesPageConfig) -> None:
    if cfg.url != MODEL_FILES_URL:
        raise ValueError("GeoTOP model-files discovery is pinned to the exact Gate-3C link")


def _validate_final_url(final_url: str) -> None:
    parsed = urlparse(final_url)
    if parsed.scheme != "https":
        raise ValueError("GeoTOP model-files final URL is not HTTPS")
    if parsed.netloc.lower() not in OFFICIAL_HOSTS:
        raise ValueError("GeoTOP model-files redirect escaped official DINOloket/TNO hosts")
    if parsed.query or parsed.fragment:
        raise ValueError("GeoTOP model-files final URL contains unexpected query or fragment")


def _normalise_official_links(base_url: str, hrefs: list[str]) -> list[dict]:
    records: dict[str, dict] = {}
    for href in hrefs:
        absolute = urljoin(base_url, href)
        parsed = urlparse(absolute)
        if parsed.scheme not in {"http", "https"} or parsed.netloc.lower() not in OFFICIAL_HOSTS:
            continue
        records[absolute] = {
            "url": absolute,
            "host": parsed.netloc.lower(),
            "path": parsed.path,
            "suffix": Path(parsed.path).suffix.lower(),
        }
    return [records[url] for url in sorted(records)]


def _normalise_forms(base_url: str, forms: list[dict]) -> list[dict]:
    output: list[dict] = []
    for form in forms:
        action = urljoin(base_url, form["action"] or base_url)
        parsed = urlparse(action)
        output.append({
            "action": action,
            "action_is_official": parsed.scheme in {"http", "https"} and parsed.netloc.lower() in OFFICIAL_HOSTS,
            "method": form["method"],
            "id": form["id"],
            "input_names": sorted(form["input_names"]),
        })
    return output


def acquire_geotop_model_files_page(
    output_dir: str | Path,
    config: GeoTopModelFilesPageConfig | None = None,
    *,
    get_transport: Callable[[str, dict[str, str], int, int], tuple[bytes, dict[str, str], str]] | None = None,
) -> dict:
    """Acquire the official model-files page and inspect links/forms without following or submitting them."""
    cfg = config or GeoTopModelFilesPageConfig()
    _validate_config(cfg)
    client = GeoTopModelFilesPageClient(cfg.timeout_s, cfg.user_agent, get_transport)
    payload, headers, final_url = client.get(cfg.url, max_bytes=cfg.max_response_bytes)
    if not payload:
        raise ValueError("GeoTOP model-files page response is empty")
    _validate_final_url(final_url)
    content_type = headers.get("content-type", "")
    if "html" not in content_type.lower():
        raise ValueError(f"Unexpected GeoTOP model-files content type: {content_type!r}")

    text = payload.decode("utf-8", errors="strict")
    parser = _PageParser()
    parser.feed(text)
    links = _normalise_official_links(final_url, parser.hrefs)
    forms = _normalise_forms(final_url, parser.forms)
    marker_hits = [m for m in MARKERS if m.casefold() in text.casefold()]
    candidate_links = [
        rec for rec in links
        if rec["suffix"] in {".csv", ".xlsx", ".xls", ".zip", ".json", ".xml"}
        or any(token in rec["path"].casefold() for token in ("referentie", "download", "modelbestand", "geotop"))
    ]

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    raw_name = "geotop_model_files_page.html"
    (out / raw_name).write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    manifest = {
        "capability": "STAGE_B_GEOTOP_161_MODEL_FILES_AUTHORITY_DISCOVERY",
        "state": "OFFICIAL_MODEL_FILES_PAGE_ACQUIRED_NO_ACTIONS_INVOKED",
        "config": cfg.as_dict(),
        "request": {"url": cfg.url, "final_url": final_url},
        "response": {
            "artifact_file": raw_name,
            "bytes": len(payload),
            "sha256": digest,
            "content_type": content_type,
        },
        "marker_hits": marker_hits,
        "official_links": links,
        "candidate_authority_links": candidate_links,
        "forms": forms,
        "guardrails": {
            "exact_gate3c_link_only": True,
            "official_redirect_only": True,
            "links_followed": False,
            "forms_submitted": False,
            "form_actions_invoked": False,
            "generic_web_search_performed": False,
            "code_translation_performed": False,
            "version_compatibility_established": False,
            "geological_interpretation_performed": False,
            "hydraulic_interpretation_performed": False,
            "admission_decision_performed": False,
            "allow_admissible_enabled": False,
        },
    }
    (out / "geotop_model_files_page_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return manifest
