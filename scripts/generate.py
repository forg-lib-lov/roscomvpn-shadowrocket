#!/usr/bin/env python3
"""
Конвертер roscomvpn-routing → Shadowrocket .list + .conf
Источник правил: https://github.com/hydraponique/roscomvpn-routing
"""

import os
import re
import base64
import requests
from datetime import datetime, timezone

# ─── настройки ───────────────────────────────────────────────────────────────

GEOSITE_API = "https://api.github.com/repos/hydraponique/roscomvpn-geosite/contents/data/{}"
GEOIP_TEXT  = "https://cdn.jsdelivr.net/gh/hydraponique/roscomvpn-geoip/release/text/{}"

OUTPUT_DIR  = os.path.join(os.path.dirname(__file__), "..", "lists")
CONF_PATH   = os.path.join(os.path.dirname(__file__), "..", "roscomvpn.conf")

# GitHub username подставляется через env-переменную GITHUB_REPO (owner/repo)
GITHUB_REPO = os.environ.get("GITHUB_REPO", "<YOUR_GITHUB_USERNAME>/roscomvpn-shadowrocket")
RAW_BASE    = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/lists"
CONF_URL    = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/roscomvpn.conf"

# ─── категории: (имя, тип, action) ───────────────────────────────────────────
# тип: "geosite" | "geoip"
# action: "PROXY" | "DIRECT" | "REJECT"

# Формат: (source_name, type, action, output_filename, no_resolve)
# no_resolve=True  → RULE-SET,...,DIRECT,no-resolve  (не резолвить домены)
# no_resolve=False → RULE-SET,...,DIRECT             (резолвить домены → проверить IP)
#
# ПОРЯДОК ВАЖЕН! Shadowrocket обрабатывает правила сверху вниз:
# 0. private-ips  — самое первое (быстрый выход для локальной сети)
# 1. REJECT       — блокировка
# 2. PROXY        — сервисы через VPN (ДО русских, т.e. YouTube выше category-ru)
# 3. DIRECT       — всё остальное напрямую
DOMAIN_RULES = [
    # BLOCK
    ("win-spy",           "geosite", "REJECT",  "win-spy.list"),
    ("category-ads",      "geosite", "REJECT",  "category-ads.list"),
    # PROXY (важно: идут ДО всех DIRECT-правил)
    ("twitch-ads",        "geosite", "PROXY",   "twitch-ads.list"),
    ("youtube",           "geosite", "PROXY",   "youtube.list"),
    ("telegram",          "geosite", "PROXY",   "telegram.list"),
    ("github",            "geosite", "PROXY",   "github.list"),
    # DIRECT — сервисы без VPN
    ("private",           "geosite", "DIRECT",  "private-domains.list"),
    ("torrent",           "geosite", "DIRECT",  "torrent-domains.list"),
    ("epicgames",         "geosite", "DIRECT",  "epicgames.list"),
    ("origin",            "geosite", "DIRECT",  "origin.list"),
    ("riot",              "geosite", "DIRECT",  "riot.list"),
    ("escapefromtarkov",  "geosite", "DIRECT",  "escapefromtarkov.list"),
    ("steam",             "geosite", "DIRECT",  "steam.list"),
    ("faceit",            "geosite", "DIRECT",  "faceit.list"),
    ("twitch",            "geosite", "DIRECT",  "twitch.list"),
    ("microsoft",         "geosite", "DIRECT",  "microsoft.list"),
    ("apple",             "geosite", "DIRECT",  "apple.list"),
    ("google-play",       "geosite", "DIRECT",  "google-play.list"),
    ("pinterest",         "geosite", "DIRECT",  "pinterest.list"),
    ("whitelist",         "geosite", "DIRECT",  "whitelist-domains.list"),
    ("category-ru",       "geosite", "DIRECT",  "category-ru.list"),
]

# Формат: (source_name, type, action, output_filename, no_resolve)
IP_RULES = [
    # private-ips идёт первым правилом в конфиге (до BLOCK/PROXY)
    # no_resolve=True: локальные IP никогда не нужно резолвить
    ("private",   "geoip", "DIRECT", "private-ips.list",   True),
    # whitelist: специфичные IP сервисов — тоже no-resolve
    ("whitelist", "geoip", "DIRECT", "whitelist-ips.list",  True),
    # direct: ~35k РФ+BY CIDR — БЕЗ no-resolve, чтобы резолвить домены
    # (именно это позволяет sberbank.ru и другим РФ-доменам идти DIRECT)
    ("direct",    "geoip", "DIRECT", "direct-ips.list",    False),
]

# ─── парсер geosite source-формата ───────────────────────────────────────────

def fetch_geosite(category: str) -> list[str]:
    """Загружает data/<category> через GitHub API и конвертирует в Shadowrocket-строки."""
    url = GEOSITE_API.format(category)
    r = requests.get(url, timeout=30)
    if r.status_code != 200:
        print(f"  WARN: {category} → HTTP {r.status_code}")
        return []

    content = base64.b64decode(r.json()["content"]).decode("utf-8", errors="replace")
    lines = []
    for raw in content.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("@"):
            continue
        if line.startswith("include:"):
            # рекурсивно подтягиваем вложенные категории
            sub = line[8:].strip().lower()
            lines.extend(fetch_geosite(sub))
        elif line.startswith("full:"):
            lines.append(f"DOMAIN,{line[5:].strip()}")
        elif line.startswith("domain:"):
            lines.append(f"DOMAIN-SUFFIX,{line[7:].strip()}")
        elif line.startswith("keyword:"):
            lines.append(f"DOMAIN-KEYWORD,{line[8:].strip()}")
        elif line.startswith("regexp:"):
            # regexp не поддерживается в RULE-SET, пропускаем
            pass
        else:
            # просто домен без префикса
            if re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9\-\.]+)\.[a-zA-Z]{2,}$", line):
                lines.append(f"DOMAIN-SUFFIX,{line}")
    return lines

# ─── парсер geoip text-формата ───────────────────────────────────────────────

def fetch_geoip(name: str, no_resolve: bool = True) -> list[str]:
    """Загружает release/text/<name>.txt и конвертирует CIDR в IP-CIDR строки."""
    url = GEOIP_TEXT.format(f"{name}.txt")
    r = requests.get(url, timeout=60)
    if r.status_code != 200:
        print(f"  WARN: geoip/{name} → HTTP {r.status_code}")
        return []

    suffix = ",no-resolve" if no_resolve else ""
    lines = []
    for raw in r.text.splitlines():
        cidr = raw.strip()
        if not cidr or cidr.startswith("#"):
            continue
        # базовая валидация CIDR
        if re.match(r"^\d{1,3}(\.\d{1,3}){3}/\d{1,2}$", cidr):
            lines.append(f"IP-CIDR,{cidr}{suffix}")
        elif re.match(r"^[0-9a-fA-F:]+/\d{1,3}$", cidr):
            lines.append(f"IP-CIDR6,{cidr}{suffix}")
    return lines

# ─── запись .list файлов ──────────────────────────────────────────────────────

def write_list(filename: str, entries: list[str], source: str):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    header = [
        f"# NAME: {filename}",
        f"# SOURCE: {source}",
        f"# UPDATED: {now}",
        f"# TOTAL: {len(entries)}",
        "",
    ]
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w") as f:
        f.write("\n".join(header + entries) + "\n")
    print(f"  ✓ lists/{filename}  ({len(entries)} rules)")

# ─── генератор .conf ─────────────────────────────────────────────────────────

def build_conf(domain_rules, ip_rules):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Находим private-ips для вставки первым правилом
    private_ip = next((r for r in ip_rules if r[3] == "private-ips.list"), None)
    other_ip_rules = [r for r in ip_rules if r[3] != "private-ips.list"]

    general = f"""# roscomvpn-shadowrocket — auto-generated {now}
# Source: https://github.com/hydraponique/roscomvpn-routing
# Repo:   https://github.com/{GITHUB_REPO}

[General]
bypass-system = true
ipv6 = false
prefer-ipv6 = false
private-ip-answer = true
dns-direct-system = false
dns-fallback-system = true
dns-direct-fallback-proxy = true

# Яндекс DNS для прямого трафика (работает везде в РФ)
# Google DNS для проксированного трафика
dns-server = https://77.88.8.8/dns-query, https://8.8.8.8/dns-query
fallback-dns-server = system
hijack-dns = :53

skip-proxy = 192.168.0.0/16,10.0.0.0/8,172.16.0.0/12,localhost,*.local,captive.apple.com
tun-excluded-routes = 10.0.0.0/8,100.64.0.0/10,127.0.0.0/8,169.254.0.0/16,172.16.0.0/12,192.0.0.0/24,192.0.2.0/24,192.88.99.0/24,192.168.0.0/16,198.51.100.0/24,203.0.113.0/24,224.0.0.0/4,255.255.255.255/32,239.255.255.250/32
tun-included-routes =

always-real-ip = time.*.com,ntp.*.com,*.cloudflareclient.com,*.apple.com
icmp-auto-reply = false
always-reject-url-rewrite = false
udp-policy-not-supported-behaviour = REJECT

# Shadowrocket будет проверять обновления по этому URL
update-url = {CONF_URL}
"""

    rule_lines = ["", "[Rule]"]

    # ── 0. private-ips первым (быстрый выход для локальной сети) ──────────────
    if private_ip:
        _, _, _, outfile, _ = private_ip
        url = f"{RAW_BASE}/{outfile}"
        rule_lines.append("# ── Локальная сеть ── выход без проверки остальных правил ──")
        rule_lines.append(f"RULE-SET,{url},DIRECT,no-resolve")
        rule_lines.append("")

    # ── 1-3. Все остальные правила (BLOCK → PROXY → DIRECT) ──────────────────
    all_rules = domain_rules + other_ip_rules
    processed_actions = []

    for name, rtype, act, outfile, *flags in all_rules:
        no_resolve = flags[0] if flags else False
        # Вставляем заголовок группы при смене action
        headers = {
            "REJECT": "# ═══ BLOCK ═══════════════════════════════════════════",
            "PROXY":  "# ═══ PROXY (через VPN) ══════════════════════════════",
            "DIRECT": "# ═══ DIRECT (напрямую) ══════════════════════════════",
        }
        if act not in processed_actions:
            rule_lines.append(headers.get(act, f"# ═══ {act} ═══"))
            processed_actions.append(act)

        url = f"{RAW_BASE}/{outfile}"
        if no_resolve:
            rule_lines.append(f"RULE-SET,{url},{act},no-resolve")
        else:
            rule_lines.append(f"RULE-SET,{url},{act}")

    # ── 4. GEOIP catch-all для РФ/BY доменов не попавших в списки ────────────
    rule_lines.append("")
    rule_lines.append("# ── GEOIP: страховка для РФ/BY доменов вне category-ru ──")
    rule_lines.append("GEOIP,RU,DIRECT")
    rule_lines.append("GEOIP,BY,DIRECT")
    rule_lines.append("")
    rule_lines.append("FINAL,PROXY")
    rule_lines.append("")

    # Убираем дублирующиеся пустые строки
    result_lines = []
    prev_empty = False
    for line in rule_lines:
        if line == "":
            if not prev_empty:
                result_lines.append(line)
            prev_empty = True
        else:
            result_lines.append(line)
            prev_empty = False

    return general + "\n".join(result_lines)

# ─── main ─────────────────────────────────────────────────────────────────────

def main():
    print("=== Генерация Shadowrocket конфига из roscomvpn-routing ===\n")

    # 1. Конвертируем geosite категории
    print("── Domain lists (geosite) ─────────────────────────────")
    for name, rtype, action, outfile in DOMAIN_RULES:
        if rtype != "geosite":
            continue
        print(f"  Fetching geosite/{name}...")
        entries = fetch_geosite(name)
        if not entries:
            print(f"  SKIP: {name} (empty)")
            continue
        write_list(
            outfile,
            entries,
            f"https://github.com/hydraponique/roscomvpn-geosite/blob/master/data/{name}"
        )

    # 2. Конвертируем geoip IP-листы
    print("\n── IP lists (geoip) ───────────────────────────────────")
    for name, rtype, action, outfile, no_resolve in IP_RULES:
        if rtype != "geoip":
            continue
        print(f"  Fetching geoip/{name}.txt (no-resolve={no_resolve})...")
        entries = fetch_geoip(name, no_resolve=no_resolve)
        if not entries:
            print(f"  SKIP: {name} (empty)")
            continue
        write_list(
            outfile,
            entries,
            f"https://github.com/hydraponique/roscomvpn-geoip/blob/master/release/text/{name}.txt"
        )

    # 3. Генерируем .conf
    print("\n── Генерация roscomvpn.conf ───────────────────────────")
    conf_content = build_conf(DOMAIN_RULES, IP_RULES)
    with open(CONF_PATH, "w") as f:
        f.write(conf_content)
    print(f"  ✓ roscomvpn.conf")

    print("\n=== Готово! ===")

if __name__ == "__main__":
    main()
