#!/usr/bin/env python3
"""Deterministic, SSRF-guarded source fetcher for the research stage.

Reads ``request.json``, fetches every requested URL under a strict egress
policy, and writes a plain-text corpus plus ``fetch-report.json`` into the
run scratch directory. The research agent then reads only these local files
and has no network tools at all.

Egress policy, enforced before any connection:

- http(s) schemes only, and only ports 80 and 443;
- no userinfo or credentials in the URL;
- the hostname must resolve exclusively to public, globally reachable
  addresses: loopback, RFC1918, carrier-grade NAT, link-local (including
  cloud metadata), multicast, reserved, and unspecified addresses are
  rejected;
- validated DNS answers are pinned for the process (socket.getaddrinfo is
  filtered to validated answers) so DNS rebinding cannot swap in a private
  address between check and connect;
- redirects are followed manually, up to 4 hops, with every hop revalidated;
- responses are capped at 5 MiB per source and 20 MiB total, 20 s timeout.

Exit code 0 even when some sources fail: the report informs the agent. Exit
code 1 only for infrastructure bugs (bad arguments, unreadable request).
"""

from __future__ import annotations

import argparse
import hashlib
import html.parser
import ipaddress
import json
import re
import socket
import ssl
import subprocess
import sys
import time
from datetime import datetime, timezone
from http.client import HTTPConnection, HTTPSConnection
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

MAX_BYTES_PER_SOURCE = 5 * 1024 * 1024
MAX_BYTES_TOTAL = 20 * 1024 * 1024
MAX_REDIRECTS = 4
TIMEOUT_SECONDS = 20
MAX_TEXT_CHARS = 150_000
MAX_PDF_PAGES = 80
TEXT_CONTENT_PREFIXES = ("text/html", "text/plain", "application/xhtml+xml",
                         "application/json", "application/xml", "text/")
USER_AGENT = "open-knowledge-agent/1.0 (+https://github.com/kirksw/open-knowledge)"

_original_getaddrinfo = socket.getaddrinfo
_pinned: dict[str, list[tuple]] = {}


class BlockedDestination(ValueError):
    pass


def _validate_host(host: str) -> list[tuple]:
    """Resolve ``host`` and return getaddrinfo answers containing only public IPs."""
    try:
        answers = _original_getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    except OSError as exc:
        raise BlockedDestination(f"DNS resolution failed for {host!r}: {exc}") from exc
    validated: list[tuple] = []
    for answer in answers:
        addr = answer[4][0]
        try:
            ip = ipaddress.ip_address(addr.split("%")[0])
        except ValueError as exc:
            raise BlockedDestination(f"invalid address {addr!r} for {host!r}") from exc
        if not ip.is_global:
            raise BlockedDestination(
                f"{host!r} resolves to non-global address {ip}; private, loopback, "
                "link-local, and metadata destinations are blocked"
            )
        validated.append(answer)
    if not validated:
        raise BlockedDestination(f"no usable addresses for {host!r}")
    return validated


def _guarded_getaddrinfo(host, port, *args, **kwargs):
    pinned = _pinned.get(host)
    if pinned is None:
        return _original_getaddrinfo(host, port, *args, **kwargs)
    rebuilt = []
    for family, socktype, proto, canonname, sockaddr in pinned:
        if sockaddr[1:2] == (0,) or port is None:
            # Rebuild the address tuple with the port the caller asked for.
            if family == socket.AF_INET6 and len(sockaddr) == 4:
                new_sockaddr = (sockaddr[0], port or 0, sockaddr[2], sockaddr[3])
            else:
                new_sockaddr = (sockaddr[0], port or 0)
        else:
            new_sockaddr = sockaddr
        rebuilt.append((family, socktype, proto, canonname, new_sockaddr))
    return rebuilt


def _check_url(url: str) -> None:
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        raise BlockedDestination(f"{url!r}: only http(s) URLs are fetched")
    if not parts.hostname:
        raise BlockedDestination(f"{url!r}: missing hostname")
    if "@" in parts.netloc:
        raise BlockedDestination(f"{url!r}: userinfo is not allowed")
    if parts.port is not None and parts.port not in (80, 443):
        raise BlockedDestination(f"{url!r}: only ports 80 and 443 are fetched, got {parts.port}")
    _pinned[parts.hostname] = _validate_host(parts.hostname)


class _HTMLText(html.parser.HTMLParser):
    BLOCK = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6",
             "section", "article", "blockquote", "pre", "table", "ul", "ol", "hr"}
    DROP = {"script", "style", "noscript", "template", "svg", "nav", "footer"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []
        self._drop_depth = 0
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag in self.DROP:
            self._drop_depth += 1
        if tag == "title":
            self._in_title = True
        if tag in self.BLOCK:
            self._chunks.append("\n")

    def handle_endtag(self, tag):
        if tag in self.DROP and self._drop_depth:
            self._drop_depth -= 1
        if tag == "title":
            self._in_title = False
        if tag in self.BLOCK:
            self._chunks.append("\n")

    def handle_data(self, data):
        if self._drop_depth:
            return
        if self._in_title:
            self.title += data
            return
        self._chunks.append(data)

    def text(self) -> str:
        raw = "".join(self._chunks)
        out: list[str] = []
        blank = False
        for line in raw.splitlines():
            line = line.strip()
            if line:
                out.append(line)
                blank = False
            elif not blank:
                out.append("")
                blank = True
        return "\n".join(out).strip()


def _charset(header: str) -> str:
    m = re.search(r"charset=([A-Za-z0-9_.:-]+)", header)
    return m.group(1) if m else "utf-8"


class Fetcher:
    def __init__(self, corpus_dir: Path):
        self.corpus_dir = corpus_dir
        self.total_bytes = 0

    def fetch(self, url: str, stem: str) -> dict:
        result = {
            "url": url,
            "final_url": url,
            "status": None,
            "content_type": None,
            "text_path": None,
            "title": None,
            "bytes": 0,
            "sha256": None,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "error": None,
        }
        current = url
        conn = None
        try:
            for _hop in range(MAX_REDIRECTS + 1):
                _check_url(current)
                parts = urlsplit(current)
                host = parts.hostname
                request_path = urlunsplit(("", "", parts.path or "/", parts.query, ""))
                if parts.scheme == "https":
                    conn = HTTPSConnection(host, port=parts.port or 443, timeout=TIMEOUT_SECONDS,
                                           context=ssl.create_default_context())
                else:
                    conn = HTTPConnection(host, port=parts.port or 80, timeout=TIMEOUT_SECONDS)
                conn.request("GET", request_path, headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "text/html, text/plain, application/xhtml+xml, application/json, "
                              "application/pdf;q=0.9, */*;q=0.1",
                    "Accept-Language": "en",
                })
                response = conn.getresponse()
                result["status"] = response.status
                location = response.getheader("Location")
                if 300 <= response.status < 400 and location:
                    current = urljoin(current, location)
                    result["final_url"] = current
                    conn.close()
                    conn = None
                    continue
                content_type = (response.getheader("Content-Type") or "").split(";")[0].strip().lower()
                result["content_type"] = content_type or None
                if response.status != 200:
                    result["error"] = f"HTTP {response.status}"
                    return result
                budget = min(MAX_BYTES_PER_SOURCE, MAX_BYTES_TOTAL - self.total_bytes)
                if budget <= 0:
                    result["error"] = "total fetch budget exhausted"
                    return result
                body = response.read(budget + 1)
                if len(body) > budget:
                    result["error"] = "source exceeds per-run size budget; skipped"
                    return result
                result["bytes"] = len(body)
                result["sha256"] = hashlib.sha256(body).hexdigest()
                self.total_bytes += len(body)
                if content_type == "application/pdf":
                    return self._pdf(result, body, stem)
                if not content_type.startswith(TEXT_CONTENT_PREFIXES):
                    result["error"] = f"unsupported content type {content_type!r}; not added to corpus"
                    return result
                text = body.decode(_charset(response.getheader("Content-Type") or ""), errors="replace")
                if "html" in content_type or "xml" in content_type:
                    extractor = _HTMLText()
                    try:
                        extractor.feed(text)
                        text = extractor.text()
                        result["title"] = extractor.title.strip() or None
                    except Exception:
                        pass
                self._write(result, stem, text[:MAX_TEXT_CHARS])
                return result
            result["error"] = "too many redirects"
            return result
        except BlockedDestination as exc:
            result["error"] = str(exc)
            return result
        except OSError as exc:
            result["error"] = f"network error: {exc}"
            return result
        finally:
            if conn is not None:
                try:
                    conn.close()
                except OSError:
                    pass

    def _pdf(self, result: dict, body: bytes, stem: str) -> dict:
        pdf_path = self.corpus_dir / f"{stem}.pdf"
        pdf_path.write_bytes(body)
        try:
            proc = subprocess.run(
                ["pdftotext", "-l", str(MAX_PDF_PAGES), str(pdf_path), "-"],
                capture_output=True, timeout=60,
            )
        except (OSError, subprocess.TimeoutExpired):
            result["error"] = "PDF fetched but pdftotext is unavailable; rely on other sources"
            return result
        if proc.returncode != 0:
            result["error"] = "PDF fetched but text extraction failed"
            return result
        text = proc.stdout.decode("utf-8", errors="replace")
        self._write(result, stem, text[:MAX_TEXT_CHARS])
        return result

    def _write(self, result: dict, stem: str, text: str) -> None:
        rel = f"{stem}.txt"
        header = (
            f"source-url: {result['final_url']}\n"
            f"fetched-at: {result['fetched_at']}\n"
            f"content-type: {result['content_type']}\n"
            + (f"page-title: {result['title']}\n" if result.get("title") else "")
            + "\n"
        )
        (self.corpus_dir / rel).write_text(header + text, encoding="utf-8")
        result["text_path"] = f"corpus/{rel}"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True, help="path to request.json")
    parser.add_argument("--out-dir", required=True,
                        help="work directory; corpus/ and fetch-report.json are written here")
    args = parser.parse_args(argv)

    request = json.loads(Path(args.request).read_text(encoding="utf-8"))
    work = Path(args.out_dir)
    corpus = work / "corpus"
    corpus.mkdir(parents=True, exist_ok=True)

    socket.getaddrinfo = _guarded_getaddrinfo
    try:
        fetcher = Fetcher(corpus)
        report = []
        for index, entry in enumerate(request.get("urls", [])):
            stem = f"{index:02d}-{entry['id']}"
            result = fetcher.fetch(entry["url"], stem)
            report.append(result)
            status = "ok" if result.get("text_path") else f"unavailable ({result.get('error')})"
            print(f"fetch: {entry['id']} {entry['url']} -> {status}")
            time.sleep(1.0)
        fetched = sum(1 for r in report if r.get("text_path"))
        payload = {
            "version": 1,
            "issue": request["issue"]["number"],
            "fetched": fetched,
            "requested": len(report),
            "total_bytes": fetcher.total_bytes,
            "results": report,
        }
        (work / "fetch-report.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"fetch-sources: {fetched}/{len(report)} sources in corpus")
        return 0
    finally:
        socket.getaddrinfo = _original_getaddrinfo


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
