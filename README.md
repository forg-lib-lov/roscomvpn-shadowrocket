# roscomvpn-shadowrocket

Готовый конфиг [Shadowrocket](https://apps.apple.com/ru/app/shadowrocket/id932747118) для России: по умолчанию трафик идёт через VPN, а российские, локальные и явно разрешённые сервисы идут напрямую.

Проект адаптирует DEFAULT-профиль [roscomvpn-routing](https://github.com/hydraponique/roscomvpn-routing) под формат Shadowrocket. Домены и IP берутся из [roscomvpn-geosite](https://github.com/hydraponique/roscomvpn-geosite), [roscomvpn-geoip](https://github.com/hydraponique/roscomvpn-geoip) и дополнительного RU-whitelist от [hxehex](https://github.com/hxehex/russia-mobile-internet-whitelist).

## Принцип роутинга

| Действие | Что идёт |
|----------|----------|
| REJECT | Windows телеметрия, рекламные домены |
| PROXY | Google Play, Twitch Ads, YouTube, Telegram, GitHub и весь остальной трафик, который не попал в DIRECT/REJECT |
| DIRECT | локальные адреса, РФ/BY домены и IP, белые списки российских сервисов, Steam, Epic, Riot, EFT, Twitch, Microsoft, Apple, Pinterest, Faceit |

Если домен не попал в доменные списки, Shadowrocket сначала проверит `GEOIP,RU` и `GEOIP,BY`. Российские и белорусские IP пойдут напрямую, всё остальное уйдёт через VPN по `FINAL,PROXY`.

## Быстрый старт

Добавь готовый конфиг в Shadowrocket:

```text
https://cdn.jsdelivr.net/gh/forg-lib-lov/roscomvpn-shadowrocket@main/roscomvpn.conf
```

В Shadowrocket: `Configurations` → `+` → вставь URL → нажми на конфиг → `Use Config`.

## Настройка GeoLite2

Для `GEOIP,RU,DIRECT` и `GEOIP,BY,DIRECT` нужна актуальная GeoLite2 Country база.

В Shadowrocket: `Settings` → `GeoLite2 Database` → поле **Country** → вставь URL → `Download`:

```text
https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-Country.mmdb
```

## Обновление

Конфиг в репозитории обновляется каждый день в 09:00 MSK через GitHub Actions.

Вручную: `Configurations` → свайп влево по конфигу → `Update Config`.

Автоматически: `Settings` → `Auto Update` → включи обновление конфигов и выставь интервал. Для фонового обновления в iOS должен быть включён `Background App Refresh` для Shadowrocket.

`.list`-файлы подключены через CDN URL и обновляются Shadowrocket при применении или компиляции конфига.

## Кастомизация

1. Сделай fork репозитория. Репозиторий должен быть публичным, если ты хочешь использовать jsDelivr URL.
2. В своём репозитории открой `Actions` → `Update Shadowrocket Config` → `Run workflow`.
3. Добавь свой конфиг в Shadowrocket:

```text
https://cdn.jsdelivr.net/gh/YOUR_GITHUB_USERNAME/roscomvpn-shadowrocket@main/roscomvpn.conf
```

Если у форка другая ветка, замени `@main` на её имя.

Правила редактируются в `scripts/generate.py`. Основные списки:

```python
DOMAIN_RULES = [
    ("youtube", "geosite", "PROXY", "youtube.list"),
    ("category-ru", "geosite", "DIRECT", "category-ru.list"),
]

IP_RULES = [
    ("direct", "geoip", "DIRECT", "direct-ips.list", True),
]
```

Генератор падает с ошибкой, если источник недоступен или после конвертации категория стала пустой. Это сделано специально, чтобы GitHub Actions не публиковал частично сломанный конфиг.

## Как это работает

```text
roscomvpn-geosite              ──┐
roscomvpn-geoip                ──┼──► scripts/generate.py ──► lists/*.list + roscomvpn.conf
hxehex/russia-mobile-internet-whitelist ──┘

Shadowrocket ──► update-url ──► свежий roscomvpn.conf
             └─► RULE-SET URLs ──► списки правил
```

По умолчанию опубликованные ссылки строятся через jsDelivr:

```text
https://cdn.jsdelivr.net/gh/{owner}/{repo}@{branch}/...
```

Для нестандартной публикации можно задать переменные окружения:

| Переменная | Назначение |
|------------|------------|
| `GITHUB_REPO` | `owner/repo` текущего репозитория |
| `GITHUB_BRANCH` | ветка для публичных URL |
| `PUBLISH_BASE` | полный базовый URL, если не нужен jsDelivr |

## Структура файлов

```text
roscomvpn-shadowrocket/
├── .github/workflows/update.yml  # ежедневное обновление
├── scripts/generate.py           # генератор Shadowrocket-правил
├── lists/                        # опубликованные RULE-SET списки
└── roscomvpn.conf                # готовый конфиг
```

## Источники правил

- Логика профиля: [hydraponique/roscomvpn-routing](https://github.com/hydraponique/roscomvpn-routing)
- Домены: [hydraponique/roscomvpn-geosite](https://github.com/hydraponique/roscomvpn-geosite)
- IP-адреса: [hydraponique/roscomvpn-geoip](https://github.com/hydraponique/roscomvpn-geoip)
- Дополнительный DIRECT-слой: [hxehex/russia-mobile-internet-whitelist](https://github.com/hxehex/russia-mobile-internet-whitelist)
