import unittest
from pathlib import Path

from scripts import generate


ROOT = Path(__file__).resolve().parents[1]


class GenerateConfigTests(unittest.TestCase):
    def test_manual_direct_contains_expected_domains(self):
        rules = set(generate.manual_domains_to_rules(generate.MANUAL_DIRECT_DOMAINS))

        expected = {
            "DOMAIN-SUFFIX,happ.su",
            "DOMAIN-SUFFIX,happ.info",
            "DOMAIN-SUFFIX,static-2v.gitbook.com",
            "DOMAIN-SUFFIX,api.gitbook.com",
            "DOMAIN-SUFFIX,integrations.gitbook.com",
            "DOMAIN-SUFFIX,ka-p.fontawesome.com",
            "DOMAIN-SUFFIX,aliexpress.ru",
            "DOMAIN-SUFFIX,rdp-onedash.ru",
            "DOMAIN-SUFFIX,aviasales.ru",
            "DOMAIN-SUFFIX,aviasales.com",
            "DOMAIN-SUFFIX,usmall.ru",
            "DOMAIN-SUFFIX,setka.ru",
            "DOMAIN-SUFFIX,cdn.setka.ru",
            "DOMAIN-SUFFIX,cdn-assets.setka.ru",
        }

        self.assertLessEqual(expected, rules)

    def test_early_proxy_rules_precede_private_ip_bypass(self):
        conf = generate.build_conf(generate.DOMAIN_RULES, generate.IP_RULES)
        private_bypass = (
            "RULE-SET,https://raw.githubusercontent.com/forg-lib-lov/"
            "roscomvpn-shadowrocket/main/lists/private-ips.list,DIRECT,no-resolve"
        )

        self.assertLess(
            conf.index("DOMAIN-SUFFIX,redgifs.com,PROXY"),
            conf.index(private_bypass),
        )

        for domain in [
            "capcut.com",
            "capcutstatic.com",
            "ibyteimg.com",
            "byteplus.com",
            "bytepluscdn.com",
            "gcloudcache.com",
            "byteintl.com",
            "ibytedtos.com",
        ]:
            self.assertLess(
                conf.index(f"DOMAIN-SUFFIX,{domain},PROXY"),
                conf.index(private_bypass),
            )

    def test_tailscale_routes_do_not_create_kernel_bypass_entries(self):
        forbidden_kernel_bypass_entries = {
            generate.TAILSCALE_IPV4_ROUTE,
            generate.TAILSCALE_DNS_ROUTE,
        }

        self.assertFalse(forbidden_kernel_bypass_entries & set(generate.SKIP_PROXY_ENTRIES))
        self.assertFalse(forbidden_kernel_bypass_entries & set(generate.TUN_EXCLUDED_ROUTES))

    def test_tailscale_direct_rules_are_early_in_generated_config(self):
        conf = generate.build_conf(generate.DOMAIN_RULES, generate.IP_RULES)
        first_rule_set = conf.index("RULE-SET,")
        tailscale_block = conf.index("# ── Tailscale compatibility ──")

        self.assertLess(tailscale_block, first_rule_set)
        self.assertIn("IP-CIDR,100.64.0.0/10,DIRECT,no-resolve", conf)
        self.assertIn("IP-CIDR,100.100.100.100/32,DIRECT,no-resolve", conf)
        self.assertIn("DOMAIN-SUFFIX,ts.net,DIRECT", conf)
        self.assertIn("DOMAIN-SUFFIX,tailscale.com,DIRECT", conf)

    def test_tailscale_ipv6_is_not_advertised_while_ipv6_is_disabled(self):
        conf = generate.build_conf(generate.DOMAIN_RULES, generate.IP_RULES)

        self.assertIn("ipv6 = false", conf)
        self.assertNotIn("fd7a:115c:a1e0::/48", conf)

    def test_generated_config_keeps_ru_by_fallback_before_final_proxy(self):
        conf = generate.build_conf(generate.DOMAIN_RULES, generate.IP_RULES)
        final_proxy = conf.index("FINAL,PROXY")

        self.assertLess(conf.index("GEOIP,RU,DIRECT"), final_proxy)
        self.assertLess(conf.index("GEOIP,BY,DIRECT"), final_proxy)

    def test_generated_config_uses_expected_dns_defaults(self):
        conf = generate.build_conf(generate.DOMAIN_RULES, generate.IP_RULES)

        self.assertIn("private-ip-answer = true", conf)
        self.assertIn("dns-fallback-system = false", conf)
        self.assertIn("dns-server = https://dns.comss.one/dns-query", conf)
        self.assertIn(
            "fallback-dns-server = https://dns.google/dns-query, "
            "https://cloudflare-dns.com/dns-query, "
            "https://dns.quad9.net/dns-query, "
            "https://unfiltered.adguard-dns.com/dns-query",
            conf,
        )

    def test_generated_manual_direct_file_matches_generator(self):
        manual_direct = ROOT / "lists" / "manual-direct.list"
        generated_rules = [
            line.strip()
            for line in manual_direct.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")
        ]

        self.assertEqual(
            generate.manual_domains_to_rules(generate.MANUAL_DIRECT_DOMAINS),
            generated_rules,
        )

    def test_generated_outputs_do_not_contain_dynamic_timestamp_markers(self):
        manual_direct = (ROOT / "lists" / "manual-direct.list").read_text(encoding="utf-8")
        conf = (ROOT / "roscomvpn.conf").read_text(encoding="utf-8")

        self.assertNotIn("# UPDATED:", manual_direct)
        self.assertEqual("# roscomvpn-shadowrocket - auto-generated", conf.splitlines()[0])


if __name__ == "__main__":
    unittest.main()
