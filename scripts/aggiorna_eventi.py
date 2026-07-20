#!/usr/bin/env python3
"""Scarica gli eventi da certenotti.eu/eventi e genera eventi.md."""

import html
import json
import re
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

TZ_IT = ZoneInfo("Europe/Rome")

EVENTI_URL = "https://www.certenotti.eu/eventi/"
API_POST = "https://www.certenotti.eu/wp-json/wp/v2/posts/{}?_fields=id,title,content,link"
OUTPUT = "eventi.md"

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CerteNottiEventiBot/1.0)"}

EMOJI_RE = re.compile(
    "["
    "\U0001F000-\U0001FAFF"  # blocchi emoji principali
    "\U00002600-\U000027BF"  # simboli vari e dingbats
    "\U00002B00-\U00002BFF"  # frecce e stelle
    "\U0001F1E6-\U0001F1FF"  # bandiere
    "\U0000FE00-\U0000FE0F"  # variation selector
    "\U0000200D"             # zero width joiner
    "\U000020E3"             # keycap
    "\U000E0020-\U000E007F"  # tag characters
    "]+",
    flags=re.UNICODE,
)


def clean_text(txt: str) -> str:
    """Rimuove emoji e normalizza spazi e righe vuote."""
    txt = EMOJI_RE.sub("", txt)
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in txt.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="ignore")


def strip_html(raw: str) -> str:
    """Converte l'HTML del contenuto in testo pulito."""
    txt = re.sub(r"<(script|style).*?</\1>", " ", raw, flags=re.S | re.I)
    txt = re.sub(r"<br\s*/?>", "\n", txt, flags=re.I)
    txt = re.sub(r"</(p|h[1-6]|div|li)>", "\n", txt, flags=re.I)
    txt = re.sub(r"<[^>]+>", " ", txt)
    txt = html.unescape(txt)
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in txt.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)


def parse_eventi_page(page: str) -> list[dict]:
    """Estrae gli eventi dalla griglia Elementor della pagina /eventi/."""
    items = re.findall(
        r'<div data-elementor-type="loop-item".*?(?=<div data-elementor-type="loop-item"|Carica altri|</body>)',
        page,
        re.S,
    )
    eventi = []
    for item in items:
        m_id = re.search(r"e-loop-item-(\d+)", item)
        m_link = re.search(r'<a href="(https://www\.certenotti\.eu/[^"]+)"', item)
        m_title = re.search(r'elementor-heading-title[^"]*">(.*?)</h2>', item, re.S)
        m_date = re.search(r"(\d{2}/\d{2}/\d{4})\s*&#8211;\s*(\d{2}:\d{2})", item)
        if not (m_id and m_title and m_date):
            continue
        giorno, ora = m_date.group(1), m_date.group(2)
        eventi.append(
            {
                "id": m_id.group(1),
                "title": clean_text(html.unescape(strip_html(m_title.group(1)))).strip(),
                "link": m_link.group(1) if m_link else "",
                "datetime": datetime.strptime(
                    f"{giorno} {ora}", "%d/%m/%Y %H:%M"
                ).replace(tzinfo=TZ_IT),
            }
        )
    return eventi


def get_descrizione(post_id: str) -> str:
    try:
        data = json.loads(fetch(API_POST.format(post_id)))
        return clean_text(strip_html(data["content"]["rendered"]))
    except Exception:
        return ""


def main() -> None:
    page = fetch(EVENTI_URL)
    eventi = parse_eventi_page(page)
    if not eventi:
        raise SystemExit("Nessun evento trovato: struttura della pagina cambiata?")

    eventi.sort(key=lambda e: e["datetime"])
    adesso = datetime.now(TZ_IT)
    futuri = [e for e in eventi if e["datetime"] >= adesso] or eventi

    out = [
        "# Eventi in programma - Certe Notti Spa & Privee",
        "",
        f"Ultimo aggiornamento: {adesso.strftime('%d/%m/%Y %H:%M')} (ora italiana)",
        "",
        f"Prossimi eventi: {len(futuri)}",
        "",
        "---",
        "",
    ]
    giorni_it = ["lunedi", "martedi", "mercoledi", "giovedi", "venerdi", "sabato", "domenica"]
    mesi_it = [
        "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
        "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre",
    ]
    for e in futuri:
        dt = e["datetime"]
        data_lunga = (
            f"{giorni_it[dt.weekday()]} {dt.day} {mesi_it[dt.month - 1]} {dt.year}"
        )
        out.append(f"## {e['title']}")
        out.append("")
        out.append(f"- **Data:** {data_lunga}")
        out.append(f"- **Ora:** {dt.strftime('%H:%M')}")
        out.append("")
        desc = get_descrizione(e["id"])
        if desc:
            out.append(desc)
            out.append("")
        out.append("---")
        out.append("")

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"Generato {OUTPUT} con {len(futuri)} eventi.")


if __name__ == "__main__":
    main()
