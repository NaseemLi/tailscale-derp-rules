# Tailscale DERP Rules

每天自动从 Tailscale 官方 DERP Map 生成 [Mihomo](https://github.com/MetaCubeX/mihomo) / [OpenClash](https://github.com/vernesong/OpenClash) 可用的规则集，用于将 Tailscale 流量路由到代理或直连通道。

## 数据来源

- **DERP Map**: [https://controlplane.tailscale.com/derpmap/default](https://controlplane.tailscale.com/derpmap/default)
- **更新频率**: 每天北京时间 05:00（UTC 21:00）自动更新
- **规则文件**: 位于 `rules/` 目录

## 规则文件说明

| 文件                            | 内容                                              |
| ------------------------------- | ------------------------------------------------- |
| `tailscale-derp-classical.yaml` | 域名 + DERP 节点 IP + 100.64.0.0/10               |
| `tailscale-derp-domain.yaml`    | 仅域名规则（含所有 DERP 节点 HostName）           |
| `tailscale-derp-ipcidr.yaml`    | 仅 DERP 节点 IPv4/IPv6 规则                       |
| `tailscale-derp-lite.yaml`      | 精简版：仅 `tailscale.com` 域名 + `100.64.0.0/10` |

## 注意事项

- **Tailscale 版本要求**: DERP Map 会随 Tailscale 客户端版本更新而变化，本规则集基于最新 DERP Map 生成。
- **CGNAT 地址**: `100.64.0.0/10` 是 Tailscale 分配给设备的虚拟 IP 网段，所有 Tailscale 设备都在此网段内。
- **DERP 节点变化**: Tailscale 会不定期增减 DERP 中继节点，本规则集每日自动同步，无需手动维护。
- **规则行为**: `no-resolve` 表示对 IP-CIDR 规则不进行域名解析，避免解析环路。
- 如果你需要将 Tailscale 流量直连，将规则动作改为 `DIRECT` 即可。
- 原始 DERP Map 数据文件: [derpmap/default](https://controlplane.tailscale.com/derpmap/default)

## 手动生成

```bash
# 生成规则文件
python scripts/generate.py

# 检查规则文件
python scripts/check.py
```
