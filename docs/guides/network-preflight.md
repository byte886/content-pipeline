# 网络环境预检 SOP（Network Preflight）

> 跨机器、只读的网络环境诊断与上游代理选择。任何会临时修改系统代理的采集
> （视频号 / 公众号等）开始前先跑预检，把"用不用代理、用哪个端口"从 AI 临场
> 判断变成**配置驱动的确定性结论**。

- 脚本：`scripts/net_preflight.py`
- 配置：`config/network.json`（随仓默认）

---

## 1. 为什么需要

采集器（MITM 探针）启动时会把系统代理临时指向本地探针端口（默认 8899），停止时
恢复。动手前必须确认三件事，否则可能在采集期间断网或与 Tailscale 冲突：

1. 国内网络是否通（采集源都是国内服务）；
2. 是否存在**真正能翻墙**的本地代理（端口在监听 ≠ 能翻墙，节点可能失效）；
3. Tailscale 是否运行、其网络服务上是否残留旧代理。

预检严格只读：不 set/state proxy、不改 pf/route、不连接或断开 VPN、不杀进程。

## 2. 命令

```bash
python3 scripts/net_preflight.py                   # 完整 JSON 报告
python3 scripts/net_preflight.py --upstream-only   # 只打印推荐 upstream（编排脚本用）
python3 scripts/net_preflight.py -o preflight.json  # 同时存档
```

`collect_channels.py --upstream auto`（默认）会自动调用预检，无需手动跑。

## 3. 探测什么

| 类别 | 项目 | 依赖 |
|---|---|---|
| 核心 | 默认路由 / 出口网卡（`route get`、`ip route`） | 不依赖 networksetup |
| 核心 | 各候选代理端口 TCP 连通 | socket |
| 核心 | 经每个端口实测国内（百度）/ 外网（gstatic 204）能力 | urllib，短超时 |
| 核心 | Tailscale 是否运行（`pgrep` 进程） | 不调用会挂死的 tailscale CLI |
| 增强 | 物理网络服务明细、当前系统代理、Tailscale 服务残留 | `networksetup`、`tailscale status` |

**增强部分有硬时间预算（默认 8 秒）**：系统网络框架异常时 `networksetup` 会挂死，
预检在预算内快速降级、跳过明细，核心结论照常输出并给出告警。

## 4. 决策规则（配置 `decision.prefer_foreign_proxy=true`）

| 探测结果 | 推荐 upstream | 含义 / 动作 |
|---|---|---|
| 存在 `foreign_ok` 的代理 | 该代理 URL（如 `http://127.0.0.1:7890`） | 微信/腾讯域名由探针直连，外网走它，**采集期间外网不断** |
| 端口在监听但 `foreign_ok=false` | 空（直连）+ 告警 | 节点失效 / 订阅过期：先在代理客户端切节点或更新订阅 |
| 无任何代理端口 | 空（直连）+ 告警 | 仅可国内采集，采集期间其他程序外网不可用 |
| Tailscale `running` | 不影响 + 提示 | 其流量走 utun 点对点、不经系统代理，探针不碰 |
| Tailscale 服务残留代理 | 告警 | Tailscale 运行时执行 `scripts/fix_tailscale_proxy.sh` 清理 |
| `networksetup` 无响应 | 增强降级 + 告警 | 系统网络层可能异常；核心结论基于端口直连探测，仍有效 |

输出关键字段：`recommendation.upstream`（空串=直连）、`recommendation.vpn_ok`、
`recommendation.warnings`、`proxy_candidates[].{domestic_ok,foreign_ok}`、
`tailscale.state`。

## 5. 跨机器配置（不硬编码环境）

配置查找顺序，后者覆盖前者：

1. 环境变量 `MCP_NET_CONFIG` 指定的文件（一次性）；
2. `~/.config/multiplatform-content-pipeline/network.json`（机器级覆盖）；
3. 仓库 `config/network.json`（随仓默认）；
4. 脚本内置默认值（兜底，无配置也能跑）。

常按机器调整的字段：

```json
{
  "proxy_port_candidates": [7890, 7897, 1087],
  "bind_host": "127.0.0.1",
  "direct_domains": ["qq.com", "qpic.cn", "weixin.com"],
  "test": { "foreign_url": "https://www.gstatic.com/generate_204", "foreign_expect": 204 },
  "enhance_budget": 8.0
}
```

- 不同代理客户端（ClashX / Clash Verge / mihomo / v2ray）端口不同 → 改
  `proxy_port_candidates`。
- 探针的"微信域名直连、其余走上游"分流规则在探针侧（`captor.go`），由
  `direct_domains` 体现；新增国内直连域名改这里。

## 6. 平台支持

- **macOS**：完整（默认路由、物理服务明细、代理能力、Tailscale）。
- **Linux**：默认路由、代理能力、Tailscale 进程；无 `networksetup`，服务明细 N/A。
- **Windows**：仅代理端口探测，其余标注未实现，不假装可用。

## 7. 相关指针

- 探针系统代理的设置 / 快照恢复（只作用物理网卡、排除 Tailscale）：
  `platforms/wechat_channels/video-capture/proxy_darwin.go`
- 上游按域名分流：`platforms/wechat_channels/video-capture/captor.go`
- 采集编排：`platforms/wechat_channels/collect_channels.py`、
  `docs/guides/wechat-channels-collect-sop.md`
- Tailscale 代理残留清理：`scripts/fix_tailscale_proxy.sh`
- 双机网络档案与故障排查：技能 `dual-machine-manager`（`references/machines.md`、
  `references/sop.md`）
