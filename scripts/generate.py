#!/usr/bin/env python3
"""
Shadowrocket-адаптация DEFAULT-профиля roscomvpn-routing.
Источники списков: roscomvpn-geosite, roscomvpn-geoip, v2fly и дополнительный RU-whitelist.
"""

from __future__ import annotations

import ipaddress
import os
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# ─── настройки ───────────────────────────────────────────────────────────────

GEOSITE_DATA = "https://raw.githubusercontent.com/hydraponique/roscomvpn-geosite/master/data/{}"
GEOIP_TEXT = "https://raw.githubusercontent.com/hydraponique/roscomvpn-geoip/master/release/text/{}"
V2FLY_DATA = "https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/{}"

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "lists")
CONF_PATH = os.path.join(os.path.dirname(__file__), "..", "roscomvpn.conf")

# GitHub repo подставляется через env-переменную GITHUB_REPO (owner/repo).
GITHUB_REPO = os.environ.get("GITHUB_REPO", "forg-lib-lov/roscomvpn-shadowrocket")
GITHUB_BRANCH = os.environ.get("GITHUB_BRANCH", "main")
PUBLISH_BASE = os.environ.get(
    "PUBLISH_BASE",
    f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}",
).rstrip("/")
RAW_BASE = f"{PUBLISH_BASE}/lists"
CONF_URL = f"{PUBLISH_BASE}/roscomvpn.conf"

USER_AGENT = f"roscomvpn-shadowrocket/{GITHUB_REPO}"

DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$"
)


class SourceError(RuntimeError):
    """Ошибка источника или конвертации, при которой нельзя публиковать конфиг."""


# ─── категории ───────────────────────────────────────────────────────────────
# Формат DOMAIN_RULES: (source_name, type, action, output_filename)
# Формат IP_RULES:     (source_name, type, action, output_filename, no_resolve)
#
# ПОРЯДОК ВАЖЕН! Shadowrocket обрабатывает правила сверху вниз:
# 0. private-ips — локальная сеть
# 1. REJECT      — блокировка
# 2. PROXY       — сервисы через VPN, включая ручные исключения
# 3. DIRECT      — российские/локальные/игровые сервисы и ручные DIRECT-исключения

DOMAIN_RULES = [
    # BLOCK
    ("win-spy", "geosite", "REJECT", "win-spy.list"),
    # PROXY — базовые правила roscomvpn-routing и ручные VPN-исключения
    ("google-play", "geosite", "PROXY", "google-play.list"),
    ("youtube", "geosite", "PROXY", "youtube.list"),
    ("telegram", "geosite", "PROXY", "telegram.list"),
    ("github", "geosite", "PROXY", "github.list"),
    ("force-proxy", "v2fly-force", "PROXY", "force-proxy.list"),
    ("microsoft-store", "manual-proxy", "PROXY", "microsoft-store.list"),
    # DIRECT
    ("manual-direct", "manual", "DIRECT", "manual-direct.list"),
    ("private", "geosite", "DIRECT", "private-domains.list"),
    ("torrent", "geosite", "DIRECT", "torrent-domains.list"),
    ("epicgames", "geosite", "DIRECT", "epicgames.list"),
    ("origin", "geosite", "DIRECT", "origin.list"),
    ("riot", "geosite", "DIRECT", "riot.list"),
    ("escapefromtarkov", "geosite", "DIRECT", "escapefromtarkov.list"),
    ("steam", "geosite", "DIRECT", "steam.list"),
    ("faceit", "geosite", "DIRECT", "faceit.list"),
    ("twitch", "geosite", "DIRECT", "twitch.list"),
    ("microsoft", "geosite", "DIRECT", "microsoft.list"),
    ("apple", "geosite", "DIRECT", "apple.list"),
    ("pinterest", "geosite", "DIRECT", "pinterest.list"),
    ("whitelist", "geosite", "DIRECT", "whitelist-domains.list"),
    ("category-ru", "geosite", "DIRECT", "category-ru.list"),
]

IP_RULES = [
    ("private", "geoip", "DIRECT", "private-ips.list", True),
    ("whitelist", "geoip", "DIRECT", "whitelist-ips.list", True),
    # direct-ips нужен только для прямых IP-коннектов, поэтому DNS-резолв тут не нужен.
    ("direct", "geoip", "DIRECT", "direct-ips.list", True),
]

# Дополнительный слой. Это не часть roscomvpn-routing, поэтому README описывает его отдельно.
PLAIN_URL_RULES = [
    (
        "https://raw.githubusercontent.com/hxehex/russia-mobile-internet-whitelist/main/whitelist.txt",
        "DIRECT",
        "hxehex-whitelist.list",
    ),
]

FORCE_PROXY_CATEGORIES = [
    "openai",
    "instagram",
    "facebook",
    "tiktok",
]

TAILSCALE_IPV4_ROUTE = "100.64.0.0/10"
TAILSCALE_DNS_ROUTE = "100.100.100.100/32"

SKIP_PROXY_ENTRIES = [
    "192.168.0.0/16",
    "10.0.0.0/8",
    "172.16.0.0/12",
    "localhost",
    "*.local",
    "captive.apple.com",
]

TUN_EXCLUDED_ROUTES = [
    "10.0.0.0/8",
    "127.0.0.0/8",
    "169.254.0.0/16",
    "172.16.0.0/12",
    "192.0.0.0/24",
    "192.0.2.0/24",
    "192.88.99.0/24",
    "192.168.0.0/16",
    "198.51.100.0/24",
    "203.0.113.0/24",
    "224.0.0.0/4",
    "255.255.255.255/32",
    "239.255.255.250/32",
]

TAILSCALE_DIRECT_RULES = [
    # Do not add Tailscale peer routes to skip-proxy/tun-excluded-routes:
    # Shadowrocket on macOS can turn them into LAN gateway routes and override Tailscale.
    f"IP-CIDR,{TAILSCALE_IPV4_ROUTE},DIRECT,no-resolve",
    f"IP-CIDR,{TAILSCALE_DNS_ROUTE},DIRECT,no-resolve",
    "DOMAIN-SUFFIX,ts.net,DIRECT",
    "DOMAIN-SUFFIX,tailscale.com,DIRECT",
]

MANUAL_DIRECT_DOMAINS = [
    # Пользовательские исключения: эти сайты должны открываться напрямую.
    # Журнал Auto.ru грузит стили и скрипты с домена avto.ru, а не auto.ru.
    "avto.ru",
    "autowp.ru",
    "appstorrent.ru",
    "lava.ru",
    "zr.ru",
    "happ.su",
    "happ.info",
    "static-2v.gitbook.com",
    "api.gitbook.com",
    "integrations.gitbook.com",
    "ka-p.fontawesome.com",
    "aliexpress.ru",
    "rdp-onedash.ru",
]

MICROSOFT_STORE_PROXY_DOMAINS = [
    "apps.microsoft.com",
    "get.microsoft.com",
    "displaycatalog.mp.microsoft.com",
    "purchase.md.mp.microsoft.com",
    "licensing.mp.microsoft.com",
    "storeedgefd.dsx.mp.microsoft.com",
    "dl.delivery.mp.microsoft.com",
    "store-images.s-microsoft.com",
    "img-prod-cms-rt-microsoft-com.akamaized.net",
]


def fetch_text(url: str, timeout: int = 30) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            text = response.read().decode(charset, errors="replace")
    except (HTTPError, URLError, TimeoutError) as exc:
        raise SourceError(f"не удалось загрузить {url}: {exc}") from exc

    if not text.strip():
        raise SourceError(f"источник пустой: {url}")
    return text


def unique(entries: list[str]) -> list[str]:
    result = []
    seen = set()
    for entry in entries:
        if entry not in seen:
            seen.add(entry)
            result.append(entry)
    return result


def normalize_domain(value: str) -> str:
    domain = value.split("@", 1)[0].strip().lower().strip(",;")
    domain = domain.removeprefix("*.").removeprefix(".").rstrip(".")
    return domain if DOMAIN_RE.match(domain) else ""


def normalize_keyword(value: str) -> str:
    keyword = value.split("@", 1)[0].strip().lower().strip(",;")
    if not keyword or "," in keyword or any(ch.isspace() for ch in keyword):
        return ""
    return keyword


# ─── парсер plain-text доменных списков ─────────────────────────────────────

def fetch_plain_domains(url: str) -> list[str]:
    """
    Загружает plain-text список доменов.

    Поддерживает оба формата:
    - один домен на строку;
    - много доменов в одной строке через пробел.
    """
    text = fetch_text(url, timeout=30)
    entries = []

    for line in text.splitlines():
        line = line.split("#", 1)[0]
        for raw in re.split(r"\s+", line):
            domain = normalize_domain(raw)
            if domain:
                entries.append(f"DOMAIN-SUFFIX,{domain}")

    return unique(entries)


# ─── парсер geosite source-формата ───────────────────────────────────────────

def geosite_line_to_shadowrocket(line: str) -> str:
    line = line.split("#", 1)[0].strip()
    if not line or line.startswith("@"):
        return ""

    if line.startswith("full:"):
        domain = normalize_domain(line[5:])
        return f"DOMAIN,{domain}" if domain else ""

    if line.startswith("domain:"):
        domain = normalize_domain(line[7:])
        return f"DOMAIN-SUFFIX,{domain}" if domain else ""

    if line.startswith("keyword:"):
        keyword = normalize_keyword(line[8:])
        return f"DOMAIN-KEYWORD,{keyword}" if keyword else ""

    if line.startswith("regexp:"):
        # Shadowrocket RULE-SET не поддерживает geosite regexp-строки.
        return ""

    domain = normalize_domain(line)
    return f"DOMAIN-SUFFIX,{domain}" if domain else ""


def fetch_geosite(category: str, seen_categories: set[str] | None = None) -> list[str]:
    """Загружает data/<category> и конвертирует в Shadowrocket-строки."""
    if seen_categories is None:
        seen_categories = set()
    if category in seen_categories:
        return []
    seen_categories.add(category)

    content = fetch_text(GEOSITE_DATA.format(category), timeout=30)
    lines = []
    for raw in content.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("@"):
            continue
        if line.startswith("include:"):
            sub = line[8:].split("@", 1)[0].strip().lower()
            if sub:
                lines.extend(fetch_geosite(sub, seen_categories))
            continue

        rule = geosite_line_to_shadowrocket(line)
        if rule:
            lines.append(rule)

    return unique(lines)


def fetch_v2fly_category(category: str, seen_categories: set[str] | None = None) -> list[str]:
    """Загружает v2fly/domain-list-community data/<category>."""
    if seen_categories is None:
        seen_categories = set()
    if category in seen_categories:
        return []
    seen_categories.add(category)

    content = fetch_text(V2FLY_DATA.format(category), timeout=30)
    lines = []
    for raw in content.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("@"):
            continue
        if "@ads" in line:
            continue
        if line.startswith("include:"):
            sub = line[8:].split("@", 1)[0].strip().lower()
            if sub:
                lines.extend(fetch_v2fly_category(sub, seen_categories))
            continue

        rule = geosite_line_to_shadowrocket(line)
        if rule:
            lines.append(rule)

    return unique(lines)


def fetch_v2fly_force_proxy(categories: list[str]) -> list[str]:
    entries = []
    for category in categories:
        entries.extend(fetch_v2fly_category(category))
    return unique(entries)


def manual_domains_to_rules(domains: list[str]) -> list[str]:
    entries = []
    for value in domains:
        domain = normalize_domain(value)
        if domain:
            entries.append(f"DOMAIN-SUFFIX,{domain}")
    return unique(entries)


# ─── парсер geoip text-формата ───────────────────────────────────────────────

def fetch_geoip(name: str, no_resolve: bool = True) -> list[str]:
    """Загружает release/text/<name>.txt и конвертирует CIDR в IP-CIDR строки."""
    text = fetch_text(GEOIP_TEXT.format(f"{name}.txt"), timeout=60)

    suffix = ",no-resolve" if no_resolve else ""
    lines = []
    for raw in text.splitlines():
        cidr = raw.split("#", 1)[0].strip()
        if not cidr:
            continue
        try:
            network = ipaddress.ip_network(cidr, strict=False)
        except ValueError:
            continue

        rule_type = "IP-CIDR6" if network.version == 6 else "IP-CIDR"
        lines.append(f"{rule_type},{network.with_prefixlen}{suffix}")

    return unique(lines)


def ensure_entries(label: str, entries: list[str]) -> None:
    if not entries:
        raise SourceError(f"{label}: после конвертации не осталось правил")


def validate_action_conflicts(generated: list[tuple[str, str, list[str]]]) -> None:
    seen = {}
    for filename, action, entries in generated:
        for entry in entries:
            key = entry.removesuffix(",no-resolve")
            previous = seen.get(key)
            if previous and previous[0] != action:
                raise SourceError(
                    "конфликт действий для правила "
                    f"{key}: {previous[1]}={previous[0]}, {filename}={action}"
                )
            seen[key] = (action, filename)


# ─── запись .list файлов ──────────────────────────────────────────────────────

def write_list(filename: str, entries: list[str], source: str) -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    entries = unique(entries)
    header = [
        f"# NAME: {filename}",
        f"# SOURCE: {source}",
        f"# TOTAL: {len(entries)}",
        "",
    ]
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(header + entries) + "\n")
    print(f"  ✓ lists/{filename}  ({len(entries)} rules)")


# ─── генератор .conf ─────────────────────────────────────────────────────────

def build_conf(domain_rules, ip_rules) -> str:
    skip_proxy = ",".join(SKIP_PROXY_ENTRIES)
    tun_excluded_routes = ",".join(TUN_EXCLUDED_ROUTES)

    private_ip = next((r for r in ip_rules if r[3] == "private-ips.list"), None)
    other_ip_rules = [r for r in ip_rules if r[3] != "private-ips.list"]

    general = f"""# roscomvpn-shadowrocket - auto-generated
# Routing baseline: https://github.com/hydraponique/roscomvpn-routing
# Rule sources: roscomvpn-geosite, roscomvpn-geoip, v2fly/domain-list-community, hxehex/russia-mobile-internet-whitelist, manual overrides
# Repo:   https://github.com/{GITHUB_REPO}

[General]
bypass-system = true
ipv6 = false
prefer-ipv6 = false
private-ip-answer = true
dns-direct-system = false
dns-fallback-system = true
dns-direct-fallback-proxy = true

# Яндекс DNS для прямого трафика, Google DNS для проксированного трафика
dns-server = https://77.88.8.8/dns-query, https://8.8.8.8/dns-query
fallback-dns-server = system
hijack-dns = :53

skip-proxy = {skip_proxy}
tun-excluded-routes = {tun_excluded_routes}
tun-included-routes =

always-real-ip = time.*.com,ntp.*.com,*.cloudflareclient.com,*.apple.com
icmp-auto-reply = false
always-reject-url-rewrite = false
udp-policy-not-supported-behaviour = REJECT

# Shadowrocket будет проверять обновления по этому URL
update-url = {CONF_URL}
"""

    rule_lines = ["", "[Rule]"]

    rule_lines.append("# ── Tailscale compatibility ──")
    rule_lines.extend(TAILSCALE_DIRECT_RULES)
    rule_lines.append("")

    if private_ip:
        _, _, _, outfile, _ = private_ip
        url = f"{RAW_BASE}/{outfile}"
        rule_lines.append("# ── Локальная сеть ── выход без проверки остальных правил ──")
        rule_lines.append(f"RULE-SET,{url},DIRECT,no-resolve")
        rule_lines.append("")

    all_rules = domain_rules + other_ip_rules
    processed_actions = []

    for _, _, act, outfile, *flags in all_rules:
        no_resolve = flags[0] if flags else False
        headers = {
            "REJECT": "# ═══ BLOCK ═══════════════════════════════════════════",
            "PROXY": "# ═══ PROXY (через VPN) ══════════════════════════════",
            "DIRECT": "# ═══ DIRECT (напрямую) ══════════════════════════════",
        }
        if act not in processed_actions:
            rule_lines.append(headers.get(act, f"# ═══ {act} ═══"))
            processed_actions.append(act)

        url = f"{RAW_BASE}/{outfile}"
        suffix = ",no-resolve" if no_resolve else ""
        rule_lines.append(f"RULE-SET,{url},{act}{suffix}")

    if PLAIN_URL_RULES:
        rule_lines.append("")
        rule_lines.append("# ── Дополнительные DIRECT-домены из RU-whitelist ──")
        for _, _, outfile in PLAIN_URL_RULES:
            rule_lines.append(f"RULE-SET,{RAW_BASE}/{outfile},DIRECT")

    rule_lines.append("")
    rule_lines.append("# ── GEOIP: fallback для РФ/BY адресов вне списков ──")
    rule_lines.append("GEOIP,RU,DIRECT")
    rule_lines.append("GEOIP,BY,DIRECT")
    rule_lines.append("")
    rule_lines.append("FINAL,PROXY")
    rule_lines.append("")

    result_lines = []
    prev_empty = False
    for line in rule_lines:
        if line == "":
            if not prev_empty:
                result_lines.append(line)
            prev_empty = True
            continue
        result_lines.append(line)
        prev_empty = False

    return general + "\n".join(result_lines)


# ─── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=== Генерация Shadowrocket-адаптации RoscomVPN ===\n")
    generated = []

    print("── Domain lists ───────────────────────────────────────")
    for name, rtype, action, outfile in DOMAIN_RULES:
        if rtype == "geosite":
            print(f"  Fetching geosite/{name}...")
            entries = fetch_geosite(name)
            source = f"https://github.com/hydraponique/roscomvpn-geosite/blob/master/data/{name}"
        elif rtype == "v2fly-force":
            print(f"  Fetching force-proxy categories: {', '.join(FORCE_PROXY_CATEGORIES)}...")
            entries = fetch_v2fly_force_proxy(FORCE_PROXY_CATEGORIES)
            source = "https://github.com/v2fly/domain-list-community"
        elif rtype == "manual":
            print("  Building manual direct list...")
            entries = manual_domains_to_rules(MANUAL_DIRECT_DOMAINS)
            source = "manual DIRECT overrides"
        elif rtype == "manual-proxy":
            print(f"  Building manual proxy list for {name}...")
            entries = manual_domains_to_rules(MICROSOFT_STORE_PROXY_DOMAINS)
            source = "manual PROXY overrides"
        else:
            raise SourceError(f"неизвестный тип доменного списка: {rtype}")

        ensure_entries(name, entries)
        write_list(outfile, entries, source)
        generated.append((outfile, action, entries))

    print("\n── IP lists (geoip) ───────────────────────────────────")
    for name, rtype, action, outfile, no_resolve in IP_RULES:
        if rtype != "geoip":
            continue
        print(f"  Fetching geoip/{name}.txt (no-resolve={no_resolve})...")
        entries = fetch_geoip(name, no_resolve=no_resolve)
        ensure_entries(f"geoip/{name}", entries)
        write_list(
            outfile,
            entries,
            f"https://github.com/hydraponique/roscomvpn-geoip/blob/master/release/text/{name}.txt",
        )
        generated.append((outfile, action, entries))

    if PLAIN_URL_RULES:
        print("\n── Plain-URL domain lists ─────────────────────────────")
        for src_url, action, outfile in PLAIN_URL_RULES:
            print(f"  Fetching {src_url}...")
            entries = fetch_plain_domains(src_url)
            ensure_entries(outfile, entries)
            write_list(outfile, entries, src_url)
            generated.append((outfile, action, entries))

    validate_action_conflicts(generated)

    print("\n── Генерация roscomvpn.conf ───────────────────────────")
    conf_content = build_conf(DOMAIN_RULES, IP_RULES)
    with open(CONF_PATH, "w", encoding="utf-8") as f:
        f.write(conf_content)
    print("  ✓ roscomvpn.conf")

    print("\n=== Готово! ===")


if __name__ == "__main__":
    try:
        main()
    except SourceError as exc:
        raise SystemExit(f"ERROR: {exc}") from exc
