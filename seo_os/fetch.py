"""Téléchargement et extraction du texte d'une page web ou d'un PDF."""

from __future__ import annotations

import io
import os
import ssl
import urllib.request
from dataclasses import dataclass, field
from urllib.error import HTTPError, URLError

import trafilatura
from lxml import html as lxml_html

USER_AGENT = "Mozilla/5.0 (compatible; SEO-OS research bot; +internal tool)"
MAX_BYTES = 10 * 1024 * 1024
MIN_TEXT_CHARS = 200  # en dessous : page vide, JavaScript requis ou protection anti-bot
MAX_HEADINGS = 40


@dataclass
class FetchedPage:
    url: str
    ok: bool
    final_url: str = ""
    title: str = ""
    text: str = ""
    headings: list[str] = field(default_factory=list)
    content_type: str = ""
    error: str | None = None


def _ssl_context() -> ssl.SSLContext:
    cafile = os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE")
    return ssl.create_default_context(cafile=cafile) if cafile else ssl.create_default_context()


def _download(url: str, timeout: float) -> tuple[bytes, str, str]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "fr-CH,fr;q=0.9"})
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=_ssl_context()))
    with opener.open(request, timeout=timeout) as resp:
        data = resp.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError("document trop volumineux")
        return data, resp.headers.get("Content-Type", ""), resp.geturl()


def _extract_pdf(data: bytes) -> tuple[str, str]:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    text = "\n\n".join((page.extract_text() or "") for page in reader.pages)
    title = (reader.metadata.title if reader.metadata and reader.metadata.title else "") or ""
    return title, text


def _extract_html(raw_html: str, url: str) -> tuple[str, str, list[str]]:
    text = (
        trafilatura.extract(
            raw_html, url=url, output_format="markdown", include_tables=True, include_links=False
        )
        or ""
    )
    meta = trafilatura.extract_metadata(raw_html)
    title = (meta.title if meta and meta.title else "") or ""
    headings: list[str] = []
    try:
        tree = lxml_html.fromstring(raw_html)
        for node in tree.xpath("//h1|//h2|//h3"):
            heading = " ".join(node.text_content().split())
            if heading:
                headings.append(f"{node.tag.upper()}: {heading}")
            if len(headings) >= MAX_HEADINGS:
                break
    except (ValueError, lxml_html.etree.ParserError):
        pass
    return title, text, headings


def fetch_page(url: str, timeout: float = 30.0) -> FetchedPage:
    try:
        data, content_type, final_url = _download(url, timeout)
    except HTTPError as e:
        return FetchedPage(url=url, ok=False, error=f"HTTP {e.code}")
    except (URLError, TimeoutError, ValueError, OSError) as e:
        return FetchedPage(url=url, ok=False, error=f"{type(e).__name__}: {e}")

    try:
        if "pdf" in content_type.lower() or url.lower().endswith(".pdf"):
            title, text = _extract_pdf(data)
            headings: list[str] = []
        else:
            charset = "utf-8"
            if "charset=" in content_type:
                charset = content_type.split("charset=")[-1].split(";")[0].strip() or "utf-8"
            title, text, headings = _extract_html(data.decode(charset, errors="replace"), final_url)
    except Exception as e:  # PDF corrompu, HTML inexploitable…
        return FetchedPage(url=url, ok=False, final_url=final_url, error=f"extraction: {e}")

    text = text.strip()
    if len(text) < MIN_TEXT_CHARS:
        return FetchedPage(
            url=url,
            ok=False,
            final_url=final_url,
            title=title,
            content_type=content_type,
            error="contenu vide (JavaScript requis ou protection anti-bot)",
        )
    return FetchedPage(
        url=url,
        ok=True,
        final_url=final_url,
        title=title,
        text=text,
        headings=headings,
        content_type=content_type,
    )
