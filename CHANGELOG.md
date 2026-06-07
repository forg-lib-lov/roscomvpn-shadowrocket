# Changelog

## 2026-06-08

### Что изменилось

- Google Play оставлен в VPN-правилах. Бесплатные приложения обычно доступны в России, но платные приложения, платежи и часть обновлений ограничены, поэтому через VPN поведение магазина предсказуемее.
- Добавлен `force-proxy.list` для важных зарубежных сервисов: ChatGPT/OpenAI, Instagram/Facebook и TikTok.
- Telegram, YouTube, Google Play и GitHub по-прежнему идут через VPN отдельными списками.
- Добавлен `microsoft-store.list`: Microsoft Store теперь идёт через VPN не только по `apps.microsoft.com`, но и по адресам каталога, лицензирования, картинок и скачивания пакетов.
- Добавлен `manual-direct.list` для ручных DIRECT-исключений: `autowp.ru`, `appstorrent.ru`.
- Рекламные правила отключены: убраны общий `category-ads` REJECT-список и отдельный `twitch-ads` routing-слой. Это снижает риск сломать картинки, скрипты и вёрстку сайтов.
- В README добавлено честное пояснение: `torrent-domains.list` помогает вести известные torrent-домены напрямую, но обычный доменный список не может гарантировать, что весь BitTorrent-обмен с пирами всегда пойдёт мимо VPN.
- GitHub Actions теперь автоматически очищает кеш jsDelivr после обновления `roscomvpn.conf` и подключённых списков.

### Что нужно сделать пользователям

Если конфиг уже добавлен в Shadowrocket, достаточно обновить его:

```text
Configurations -> свайп по конфигу -> Update Config
```

Если конфиг добавляется впервые, используйте ссылку:

```text
https://cdn.jsdelivr.net/gh/forg-lib-lov/roscomvpn-shadowrocket@main/roscomvpn.conf
```
