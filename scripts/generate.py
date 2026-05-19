#!/usr/bin/env python3
"""从 Tailscale 官方 DERP Map 生成 Mihomo/OpenClash 规则集。

数据源: https://controlplane.tailscale.com/derpmap/default
"""

import json
import os
import sys
from datetime import datetime, timezone
from urllib.request import urlopen

# 数据源 URL
DERPMAP_URL = "https://controlplane.tailscale.com/derpmap/default"

# 输出目录
RULES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "rules")

# 固定规则
TAILSCALE_DOMAIN = "DOMAIN-SUFFIX,tailscale.com"
CGNAT_CIDR = "IP-CIDR,100.64.0.0/10,no-resolve"


def fetch_derpmap() -> dict:
    """从 Tailscale API 获取 DERP Map 数据。"""
    print(f"正在从 {DERPMAP_URL} 获取 DERP Map 数据...")
    with urlopen(DERPMAP_URL, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    print(f"获取成功，状态码: {resp.status}")
    return data


def extract_rules(derpmap: dict) -> tuple[list[str], list[str], list[str]]:
    """从 DERP Map 中提取域名、IPv4、IPv6 规则。

    Returns:
        (domain_rules, ipv4_rules, ipv6_rules)
    """
    hostnames: set[str] = set()
    ipv4s: set[str] = set()
    ipv6s: set[str] = set()

    regions = derpmap.get("Regions", {})
    for region_id, region in regions.items():
        nodes = region.get("Nodes", [])
        for node in nodes:
            hostname = node.get("HostName")
            if hostname:
                hostnames.add(hostname)

            ipv4 = node.get("IPv4")
            if ipv4:
                ipv4s.add(ipv4)

            ipv6 = node.get("IPv6")
            if ipv6:
                # 去掉 IPv6 地址中的方括号（如有）
                ipv6 = ipv6.strip("[]")
                ipv6s.add(ipv6)

    # 排序以保证输出稳定
    domain_rules = [f"DOMAIN-SUFFIX,{h}" for h in sorted(hostnames)]
    ipv4_rules = [f"IP-CIDR,{ip}/32,no-resolve" for ip in sorted(ipv4s)]
    ipv6_rules = [f"IP-CIDR6,{ip}/128,no-resolve" for ip in sorted(ipv6s)]

    return domain_rules, ipv4_rules, ipv6_rules


def generate_header(source_url: str) -> str:
    """生成 YAML 文件头部注释。"""
    utc_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return (
        f"# Tailscale DERP 规则集\n"
        f"# 数据源: {source_url}\n"
        f"# 更新时间 (UTC): {utc_time}\n"
        f"# 由 scripts/generate.py 自动生成，请勿手动编辑\n"
    )


def write_yaml(filepath: str, header: str, payload_lines: list[str]) -> None:
    """写入 Mihomo/OpenClash rule-provider 格式的 YAML 文件。"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(header)
        f.write("payload:\n")
        for line in payload_lines:
            f.write(f"  - {line}\n")
    print(f"已生成: {filepath} ({len(payload_lines)} 条规则)")


def main() -> None:
    derpmap = fetch_derpmap()
    domain_rules, ipv4_rules, ipv6_rules = extract_rules(derpmap)
    header = generate_header(DERPMAP_URL)

    # 1. classical: 域名 + DERP 节点 IP + CGNAT 网段
    classical_rules = []
    classical_rules.append(TAILSCALE_DOMAIN)
    classical_rules.extend(domain_rules)
    classical_rules.extend(ipv4_rules)
    classical_rules.extend(ipv6_rules)
    classical_rules.append(CGNAT_CIDR)
    write_yaml(os.path.join(RULES_DIR, "tailscale-derp-classical.yaml"), header, classical_rules)

    # 2. domain: 仅域名规则
    domain_payload = [TAILSCALE_DOMAIN] + domain_rules
    write_yaml(os.path.join(RULES_DIR, "tailscale-derp-domain.yaml"), header, domain_payload)

    # 3. ipcidr: 仅 DERP 节点 IP 规则
    ipcidr_payload = ipv4_rules + ipv6_rules
    write_yaml(os.path.join(RULES_DIR, "tailscale-derp-ipcidr.yaml"), header, ipcidr_payload)

    # 4. lite: 仅 tailscale.com 域名 + CGNAT 网段
    lite_payload = [TAILSCALE_DOMAIN, CGNAT_CIDR]
    write_yaml(os.path.join(RULES_DIR, "tailscale-derp-lite.yaml"), header, lite_payload)

    print("\n所有规则文件生成完毕。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
