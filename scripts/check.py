#!/usr/bin/env python3
"""检查 rules/ 目录下生成的 YAML 规则文件是否合法。"""

import os
import re
import sys

# 规则文件目录
RULES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "rules")

# 需要检查的文件
REQUIRED_FILES = [
    "tailscale-derp-classical.yaml",
    "tailscale-derp-domain.yaml",
    "tailscale-derp-ipcidr.yaml",
    "tailscale-derp-lite.yaml",
]

# IP-CIDR 格式: x.x.x.x/xx
IP_CIDR_PATTERN = re.compile(
    r"^IP-CIDR,("
    r"(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\."
    r"(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\."
    r"(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\."
    r"(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)"
    r"/([12]?\d|3[0-2])),no-resolve$"
)

# IP-CIDR6 格式: 标准 IPv6 地址/掩码
IP_CIDR6_PATTERN = re.compile(
    r"^IP-CIDR6,([0-9a-fA-F:]+)/(\d{1,3}),no-resolve$"
)


def check_file_exists(filename: str) -> list[str]:
    """检查文件是否存在。"""
    errors = []
    filepath = os.path.join(RULES_DIR, filename)
    if not os.path.isfile(filepath):
        errors.append(f"错误: 文件不存在 - {filepath}")
    return errors


def parse_payload(filepath: str) -> list[str]:
    """解析 YAML 文件中的 payload 规则列表。"""
    rules = []
    with open(filepath, "r", encoding="utf-8") as f:
        in_payload = False
        for line in f:
            line = line.rstrip("\n")
            if line == "payload:":
                in_payload = True
                continue
            if in_payload and line.startswith("  - "):
                rule = line[4:]  # 去掉 "  - " 前缀
                rules.append(rule)
            elif in_payload and line and not line.startswith("  - "):
                # 遇到非规则行，payload 部分结束
                break
    return rules


def check_payload_not_empty(filename: str, rules: list[str]) -> list[str]:
    """检查 payload 是否为空。"""
    errors = []
    if not rules:
        errors.append(f"错误: {filename} 的 payload 为空")
    return errors


def check_classical_content(filename: str, rules: list[str]) -> list[str]:
    """检查 classical 文件是否包含必需的固定规则。"""
    errors = []
    if filename != "tailscale-derp-classical.yaml":
        return errors

    if "DOMAIN-SUFFIX,tailscale.com" not in rules:
        errors.append("错误: tailscale-derp-classical.yaml 缺少 DOMAIN-SUFFIX,tailscale.com")
    if "IP-CIDR,100.64.0.0/10,no-resolve" not in rules:
        errors.append("错误: tailscale-derp-classical.yaml 缺少 IP-CIDR,100.64.0.0/10,no-resolve")
    return errors


def check_ip_formats(filename: str, rules: list[str]) -> list[str]:
    """检查 IP-CIDR 和 IP-CIDR6 格式是否合法。"""
    errors = []
    for rule in rules:
        if rule.startswith("IP-CIDR6,"):
            if not IP_CIDR6_PATTERN.match(rule):
                errors.append(f"错误: {filename} 中 IP-CIDR6 格式不合法 - {rule}")
        elif rule.startswith("IP-CIDR,"):
            if not IP_CIDR_PATTERN.match(rule):
                errors.append(f"错误: {filename} 中 IP-CIDR 格式不合法 - {rule}")
    return errors


def main() -> int:
    all_errors = []

    for filename in REQUIRED_FILES:
        print(f"检查 {filename} ...")

        # 1. 文件存在
        errors = check_file_exists(filename)
        if errors:
            all_errors.extend(errors)
            continue

        filepath = os.path.join(RULES_DIR, filename)
        rules = parse_payload(filepath)

        # 2. payload 不为空
        all_errors.extend(check_payload_not_empty(filename, rules))

        # 3. classical 文件包含必需规则
        all_errors.extend(check_classical_content(filename, rules))

        # 4. IP-CIDR / IP-CIDR6 格式合法
        all_errors.extend(check_ip_formats(filename, rules))

        if not any(filename in e for e in all_errors[-4:]):
            print(f"  ✓ {filename} 检查通过 ({len(rules)} 条规则)")

    if all_errors:
        print(f"\n检查失败，共 {len(all_errors)} 个错误:")
        for error in all_errors:
            print(f"  {error}")
        return 1

    print(f"\n所有检查通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
