# roscomvpn-shadowrocket

Готовый конфиг [Shadowrocket](https://apps.apple.com/ru/app/shadowrocket/id932747118) для России: по умолчанию трафик идёт через VPN, а российские, локальные и явно разрешённые сервисы идут напрямую.

Проект адаптирует DEFAULT-профиль [roscomvpn-routing](https://github.com/hydraponique/roscomvpn-routing) под формат Shadowrocket. Домены и IP берутся из [roscomvpn-geosite](https://github.com/hydraponique/roscomvpn-geosite), [roscomvpn-geoip](https://github.com/hydraponique/roscomvpn-geoip), [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community) и дополнительного RU-whitelist от [hxehex](https://github.com/hxehex/russia-mobile-internet-whitelist).

## Принцип роутинга

| Действие | Что идёт |
|----------|----------|
| REJECT | Windows телеметрия |
| PROXY | Google Play, YouTube, Telegram, GitHub, ChatGPT/OpenAI, Instagram/Facebook, TikTok, Microsoft Store и весь остальной трафик, который не попал в DIRECT/REJECT |
| DIRECT | локальные адреса, РФ/BY домены и IP, белые списки российских сервисов, Steam, Epic, Riot, EFT, Twitch, основная часть Microsoft, Apple, Pinterest, Faceit, torrent-домены и ручные DIRECT-исключения |

Если домен не попал в доменные списки, Shadowrocket сначала проверит `GEOIP,RU` и `GEOIP,BY`. Российские и белорусские IP пойдут напрямую, всё остальное уйдёт через VPN по `FINAL,PROXY`.

## Ручные исключения

В конфиге есть два небольших ручных слоя.

`force-proxy.list` - важные зарубежные сервисы, которые должны идти через VPN явно: ChatGPT/OpenAI, Instagram/Facebook и TikTok. Telegram, YouTube, Google Play и GitHub тоже идут через VPN отдельными списками.

`microsoft-store.list` - Microsoft Store через VPN: сайт `apps.microsoft.com`, каталог, лицензирование и домены скачивания пакетов.

`manual-direct.list` - сайты, которые должны идти напрямую: `autowp.ru`, `appstorrent.ru`.

Google Play идёт через VPN не потому, что весь магазин полностью заблокирован. Бесплатные приложения обычно доступны, но платные приложения, платежи и часть обновлений для российских аккаунтов ограничены. Через VPN поведение Google Play обычно предсказуемее.

Microsoft Store вынесен в отдельный VPN-список, потому что одного `apps.microsoft.com` мало. Сам сайт может открываться, но каталог, кнопки установки и скачивание пакетов используют отдельные адреса Microsoft, например `displaycatalog.mp.microsoft.com`, `storeedgefd.dsx.mp.microsoft.com` и `dl.delivery.mp.microsoft.com`.

## Торренты

Torrent-домены из базового roscomvpn-списка идут напрямую через `torrent-domains.list`.

Важно: это не гарантирует, что весь BitTorrent-обмен с пирами всегда пойдёт мимо VPN. BitTorrent подключается к случайным IP других пользователей, и обычный доменный список не всегда может отличить такой трафик от любого другого соединения. Если твой VPN-провайдер запрещает торренты, самый надёжный вариант - выключать VPN/Shadowrocket на время torrent-клиента или настраивать torrent-клиент/устройство отдельно.

Рекламные правила отключены специально: задача этого конфига - маршрутизация, а не блокировка рекламы. Так меньше риск сломать загрузку картинок, скриптов и вёрстку обычных сайтов.

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

После публикации изменений GitHub Actions автоматически очищает кеш jsDelivr для `roscomvpn.conf` и всех подключённых `lists/*.list`, чтобы Shadowrocket быстрее получал свежую версию.

Вручную: `Configurations` → свайп влево по конфигу → `Update Config`.

Автоматически: `Settings` → `Auto Update` → включи обновление конфигов и выставь интервал. Для фонового обновления в iOS должен быть включён `Background App Refresh` для Shadowrocket.

`.list`-файлы подключены через CDN URL и обновляются Shadowrocket при применении или компиляции конфига.

Если нужно срочно очистить CDN-кеш вручную, открой:

```text
https://purge.jsdelivr.net/gh/forg-lib-lov/roscomvpn-shadowrocket@main/roscomvpn.conf
```

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

Ручные списки редактируются там же:

```python
FORCE_PROXY_CATEGORIES = [
    "openai",
    "instagram",
    "facebook",
    "tiktok",
]

MANUAL_DIRECT_DOMAINS = [
    "autowp.ru",
    "appstorrent.ru",
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
```

Генератор падает с ошибкой, если источник недоступен или после конвертации категория стала пустой. Это сделано специально, чтобы GitHub Actions не публиковал частично сломанный конфиг.

## Как это работает

```text
roscomvpn-geosite                       ──┐
roscomvpn-geoip                         ──┤
hxehex/russia-mobile-internet-whitelist ──┤
v2fly/domain-list-community             ──┘
                                             ► scripts/generate.py ──► lists/*.list + roscomvpn.conf

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
- Важные зарубежные сервисы: [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community)
- Ручные исключения: `scripts/generate.py`
