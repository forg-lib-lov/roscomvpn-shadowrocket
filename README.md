# roscomvpn-shadowrocket

Готовый конфиг [Shadowrocket](https://apps.apple.com/ru/app/shadowrocket/id932747118) для России: **весь трафик через VPN**, кроме российских сервисов — они идут напрямую.

Правила обновляются автоматически каждый день из [roscomvpn-routing](https://github.com/hydraponique/roscomvpn-routing).

## Принцип роутинга

| Действие | Что идёт |
|----------|----------|
| 🚫 REJECT | Windows телеметрия, реклама (VK, OK) |
| 🌐 PROXY  | YouTube, Telegram, GitHub и всё остальное зарубежное |
| ✅ DIRECT | РФ/BY домены и IP, Сбербанк, Госуслуги, РЖД, ВКонтакте, Яндекс, Steam, Epic, Riot, EFT, Twitch, Microsoft, Apple, Google Play, Pinterest, Faceit |

> Если сервис не попал ни в одно правило — идёт через VPN (`FINAL,PROXY`).

## Быстрый старт — без fork'а

Если тебя устраивают правила как есть, просто добавь готовый конфиг:

```
https://raw.githubusercontent.com/forg-lib-lov/roscomvpn-shadowrocket/main/roscomvpn.conf
```

В Shadowrocket: `Configurations` → `+` → вставь URL → нажми на конфиг → `Use Config`.

Конфиг обновляется в репо каждый день в 09:00 MSK. Чтобы подтянуть свежую версию — смотри раздел [Обновление конфига](#обновление-конфига).

## Настройка (один раз)

### 1. GeoLite2 — база геолокации

Без неё правило `GEOIP,RU,DIRECT` работает неточно (часть российских IP не распознаётся).

В Shadowrocket: `Settings` → `GeoLite2 Database` → поле **Country** → вставь URL → `Download`:

```
https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-Country.mmdb
```

## Обновление конфига

Конфиг в репо обновляется сам каждый день в 09:00 MSK. Shadowrocket не подтягивает его автоматически — нужно настроить или обновить вручную.

**Вручную:** `Configurations` → свайп влево по конфигу → `Update Config`

**Автоматически:** `Settings` → `Auto Update` → включи обновление конфигов, выставь интервал (1–7 дней). Требует **Background App Refresh** в iOS Settings → General → Background App Refresh → Shadowrocket.

> Правила в `.list` файлах обновляются отдельно при каждом нажатии **Use Config** или **Compile Config**.

---

## Хочешь кастомизировать — сделай fork

Если нужно добавить/убрать правила под себя:

### 1. Создай репо на GitHub

Форкни этот репо (кнопка Fork вверху страницы). Репо должно быть **публичным**.

### 2. Запусти первый build

В своём репо: вкладка **Actions** → `Update Shadowrocket Config` → **Run workflow**.

Через ~2 минуты появятся `lists/*.list` и свежий `roscomvpn.conf`.

### 3. Добавь свой конфиг в Shadowrocket

```
https://raw.githubusercontent.com/YOUR_GITHUB_USERNAME/roscomvpn-shadowrocket/main/roscomvpn.conf
```

### 4. Кастомизация правил

Отредактируй `scripts/generate.py`:

```python
DOMAIN_RULES = [
    # добавь свою категорию:
    ("my-category", "geosite", "PROXY", "my-category.list"),
    ...
]
```

После изменений — запусти workflow вручную или подожди автообновления в 09:00 MSK.

---

## Как это работает

```
roscomvpn-geosite (домены)            ──┐
roscomvpn-geoip   (IP CIDR)           ──┼──► GitHub Actions → lists/*.list + roscomvpn.conf
hxehex/russia-mobile-internet-whitelist┘        ↑ каждый день в 09:00 MSK

Shadowrocket ──► update-url ──► подтягивает свежий roscomvpn.conf
```

## Структура файлов

```
roscomvpn-shadowrocket/
├── .github/workflows/
│   └── update.yml              # GitHub Actions: ежедневный auto-update
├── scripts/
│   └── generate.py             # Конвертер roscomvpn → Shadowrocket
├── lists/
│   ├── win-spy.list            # Windows телеметрия → REJECT
│   ├── category-ads.list       # Реклама → REJECT
│   ├── youtube.list            # YouTube → PROXY
│   ├── telegram.list           # Telegram → PROXY
│   ├── github.list             # GitHub → PROXY
│   ├── twitch-ads.list         # Twitch ads → PROXY
│   ├── steam.list              # Steam → DIRECT
│   ├── ...                     # (все остальные категории)
│   ├── whitelist-ips.list      # Спец IP РФ-сервисов → DIRECT
│   ├── direct-ips.list         # ~35k РФ+BY CIDR → DIRECT
│   └── hxehex-whitelist.list   # Сбер, Госуслуги, РЖД и др. → DIRECT
└── roscomvpn.conf              # Готовый конфиг для Shadowrocket
```

## Источники правил

- Домены: [hydraponique/roscomvpn-geosite](https://github.com/hydraponique/roscomvpn-geosite)
- IP-адреса: [hydraponique/roscomvpn-geoip](https://github.com/hydraponique/roscomvpn-geoip)
- Логика роутинга: [hydraponique/roscomvpn-routing](https://github.com/hydraponique/roscomvpn-routing)
- Российские сервисы (доп.): [hxehex/russia-mobile-internet-whitelist](https://github.com/hxehex/russia-mobile-internet-whitelist) — 2600+ доменов, обновляется ежедневно
