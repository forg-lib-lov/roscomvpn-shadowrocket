# Changelog

## 2026-06-08

### Что изменилось

- Google Play оставлен в VPN-правилах. Бесплатные приложения обычно доступны в России, но платные приложения, платежи и часть обновлений ограничены, поэтому через VPN поведение магазина предсказуемее.
- Добавлен `force-proxy.list` для важных зарубежных сервисов: ChatGPT/OpenAI, Instagram/Facebook и TikTok.
- Telegram, YouTube, Google Play и GitHub по-прежнему идут через VPN отдельными списками.
- Добавлен `microsoft-store.list`: Microsoft Store теперь идёт через VPN не только по `apps.microsoft.com`, но и по адресам каталога, лицензирования, картинок и скачивания пакетов.
- Добавлен `manual-direct.list` для ручных DIRECT-исключений: `avto.ru`, `autowp.ru`, `appstorrent.ru`, `lava.ru`, `zr.ru`. `avto.ru` нужен для стилей и скриптов Журнала Auto.ru (`auto.ru/mag/`), которые грузятся с `st.avto.ru`; `lava.ru` и `zr.ru` добавлены, потому что их нет в текущих upstream DIRECT-списках.
- Домены Happ `happ.su` и `happ.info` добавлены в ручные DIRECT-исключения, потому что сайт Happ может плохо открываться при текущем роутинге.
- GitBook-ресурсы Happ и `aliexpress.ru` добавлены в ручные DIRECT-исключения: Happ использует GitBook для стилей и скриптов, а российская версия AliExpress может сбоить через VPN.
- `rdp-onedash.ru` добавлен в ручные DIRECT-исключения, потому что сайт может не открываться при маршрутизации через VPN.
- `aviasales.ru` и `usmall.ru` добавлены в ручные DIRECT-исключения, потому что эти российские сайты могут плохо открываться через VPN.
- Tailscale peer-сеть `100.64.0.0/10` убрана из `skip-proxy` и `tun-excluded-routes`, чтобы Shadowrocket не создавал маршруты через LAN gateway и не перекрывал Tailscale `utun`. Tailscale оставлен только в ранних DIRECT-правилах без отдельных kernel routes.
- Рекламные правила отключены: убраны общий `category-ads` REJECT-список и отдельный `twitch-ads` routing-слой. Это снижает риск сломать картинки, скрипты и вёрстку сайтов.
- В README добавлено честное пояснение: `torrent-domains.list` помогает вести известные torrent-домены напрямую, но обычный доменный список не может гарантировать, что весь BitTorrent-обмен с пирами всегда пойдёт мимо VPN.
- Публикация переведена с jsDelivr на GitHub Raw. GitHub Actions теперь просто пересобирает `roscomvpn.conf` и `lists/*.list`, без очистки CDN-кеша и ожидания jsDelivr.

### Что нужно сделать пользователям

Если конфиг уже добавлен в Shadowrocket, достаточно обновить его:

```text
Configurations -> свайп по конфигу -> Update Config
```

Если конфиг добавляется впервые, используйте ссылку:

```text
https://raw.githubusercontent.com/forg-lib-lov/roscomvpn-shadowrocket/main/roscomvpn.conf
```
