# roscomvpn-shadowrocket

Автоматически обновляемый конфиг [Shadowrocket](https://apps.apple.com/ru/app/shadowrocket/id932747118) на базе правил [roscomvpn-routing](https://github.com/hydraponique/roscomvpn-routing) от сообщества.

## Как работает

```
roscomvpn-geosite (домены)           ──┐
roscomvpn-geoip   (IP CIDR)          ──┼──► GitHub Actions → lists/*.list + roscomvpn.conf
hxehex/russia-mobile-internet-whitelist┘        ↑ обновляется каждый день в 09:00 MSK

Shadowrocket ──► update-url ──► подтягивает свежий roscomvpn.conf
```

- **GitHub Actions** запускается каждый день, скачивает свежие данные из roscomvpn и пересобирает конфиг
- **Shadowrocket** сам периодически проверяет `update-url` и применяет обновления
- Источник правил всегда актуален — привязан к репозиториям roscomvpn-routing

## Логика роутинга

| Действие | Что идёт |
|----------|----------|
| 🚫 REJECT | Windows телеметрия, реклама VK/OK |
| 🌐 PROXY  | YouTube, Telegram, GitHub, Twitch-ads |
| ✅ DIRECT | Все РФ/BY домены и IP-адреса, банки, Steam, Epic, Riot, EFT, Apple push, Microsoft updates, Twitch (трафик), Pinterest, Faceit |
| 🌐 PROXY  | Всё остальное (FINAL) |

## Установка (шаги)

### 1. Создай свой репозиторий

Форкни или клонируй этот репо на GitHub. Репозиторий должен быть **публичным** — тогда Shadowrocket может обращаться к raw-ссылкам без авторизации.

```bash
# Клонируй
git clone https://github.com/YOUR_GITHUB_USERNAME/roscomvpn-shadowrocket

# Или создай новый репо и залей файлы:
git init
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/roscomvpn-shadowrocket
git add .
git commit -m "initial commit"
git push -u origin main
```

### 2. Запусти первый build

В твоём репо на GitHub:
- Открой вкладку **Actions**
- Найди workflow `Update Shadowrocket Config`
- Нажми **Run workflow** → **Run workflow**

Через ~2 минуты в репо появятся `lists/*.list` и свежий `roscomvpn.conf`.

### 3. Добавь конфиг в Shadowrocket

Открой ссылку на своём iPhone:

```
https://raw.githubusercontent.com/YOUR_GITHUB_USERNAME/roscomvpn-shadowrocket/main/roscomvpn.conf
```

Или через Shadowrocket:
1. `Конфигурации` → `+` → вставь URL выше
2. Нажми на конфиг → `Использовать конфигурацию`

### 4. Добавь GeoLite2 базу данных

Это нужно для корректной работы правила `GEOIP,RU,DIRECT` — без неё часть российских IP определяется неверно.

В Shadowrocket:
1. `Настройки` → `GeoLite2 Database` → поле **Country**
2. Вставь URL и нажми **Download**:
```
https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-Country.mmdb
```

### 5. Включи авто-обновление

В Shadowrocket:
1. `Конфигурации` → нажми и удержи на конфиге → `Редактировать`
2. Включи **Обновлять автоматически** (или задай период — например, еженедельно)

## Автоматическое обновление

GitHub Actions запускает скрипт каждый день в **09:00 MSK**. Если roscomvpn обновил свои списки — конфиг и `.list` файлы пересобираются и коммитятся в репо автоматически.

Ты также можешь запустить вручную: Actions → `Update Shadowrocket Config` → `Run workflow`.

## Кастомизация

Хочешь добавить или убрать правила? Отредактируй списки в `scripts/generate.py`:

```python
DOMAIN_RULES = [
    # добавь свою категорию:
    ("my-category", "geosite", "PROXY", "my-category.list"),
    ...
]
```

Или добавь дополнительные `RULE-SET` прямо в итоговый конфиг — раскомментируй секцию ниже в `generate.py` после строки `FINAL,PROXY`.

## Структура файлов

```
roscomvpn-shadowrocket/
├── .github/workflows/
│   └── update.yml          # GitHub Actions: ежедневный auto-update
├── scripts/
│   └── generate.py         # Конвертер roscomvpn → Shadowrocket
├── lists/
│   ├── win-spy.list         # Windows телеметрия → REJECT
│   ├── category-ads.list    # Реклама → REJECT
│   ├── youtube.list         # YouTube → PROXY
│   ├── telegram.list        # Telegram → PROXY
│   ├── github.list          # GitHub → PROXY
│   ├── twitch-ads.list      # Twitch ads → PROXY
│   ├── steam.list           # Steam → DIRECT
│   ├── ...                  # (все остальные категории)
│   ├── whitelist-ips.list      # Спец IP РФ-сервисов → DIRECT
│   ├── direct-ips.list         # ~35k РФ+BY CIDR → DIRECT
│   └── hxehex-whitelist.list   # Российские сервисы (Сбер, Госуслуги, РЖД…) → DIRECT
└── roscomvpn.conf              # Готовый конфиг для Shadowrocket
```

## Источники правил

- Домены: [hydraponique/roscomvpn-geosite](https://github.com/hydraponique/roscomvpn-geosite)
- IP-адреса: [hydraponique/roscomvpn-geoip](https://github.com/hydraponique/roscomvpn-geoip)
- Логика роутинга: [hydraponique/roscomvpn-routing](https://github.com/hydraponique/roscomvpn-routing)
- Российские сервисы (доп.): [hxehex/russia-mobile-internet-whitelist](https://github.com/hxehex/russia-mobile-internet-whitelist) — 2600+ доменов, обновляется ежедневно
