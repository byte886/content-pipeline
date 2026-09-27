# Codex 开发环境与模型选型方案（GPT-5.6 Sol）

> 更新：2026-09-27 ｜ 适用：本仓 `multiplatform-content-pipeline`（Go/Python，多平台采集）
> 交接对象：**整个仓库目录**（不是单文档）

---

## 1. 结论速览

| 项 | 选择 |
|---|---|
| 编程 agent | **OpenAI Codex CLI**（终端为主） |
| 主力模型 | **GPT-5.6 Sol**（旗舰，agentic/terminal 最强） |
| 辅助 IDE | **VS Code**（Go/Python 调试、git、人工把关），可装 Codex 扩展 |
| 日常省钱模型 | 国产 **DeepSeek / 通义 Qwen / GLM**（非敏感、大批量任务） |
| 算力购买 | 攻关期 **ChatGPT Plus $20/月（含 Sol）**；国内备选**口碑中转站按量** |
| **不使用 Xcode** | 本项目是 Go/Python，Xcode 是苹果生态 IDE，无对应工具链 |

**为什么是 Sol**：公众号这关是开放式终端攻关（CDP 调试、网络逆向、路径未定、反复迭代），
GPT-5.6 Sol 的最强项正是自主终端 agent（Coding Agent Index 80，第一）；Claude 的最强项
（命题式修代码正确率）在"路径未定"阶段发挥不出来，等进入确定性工程阶段再切 Claude Sonnet。

## 2. 工具形态：为什么不用 Xcode，用 Codex CLI + VS Code

- **Codex CLI**：终端原生，能自主读文件、跑命令、抓包、CDP 调试、迭代后汇报；本项目大量工作是
  "跑脚本→看输出→改代码→再跑"，CLI agent 效率最高。开源（openai/codex）。
- **VS Code**：对 Go/Python 工具链（补全、断点、测试、lint）支持最好，用于人工把关与可视化；
  装官方 Codex 扩展可在 IDE 内调用同一 agent。
- **Xcode 不适用**：Xcode 面向 Swift/Objective-C/macOS·iOS，对 Go/Python 没有调试与构建支持，
  强行使用等同于纯文本编辑器。

## 3. 算力购买：三条路径（按推荐顺序）

### 路径 A：ChatGPT 订阅（攻关期最省心，推荐）
- **ChatGPT Plus $20/月**：已包含旗舰 **GPT-5.6 Sol** 及 Codex 用量（2026-07 起 ChatGPT 与 Codex
  合并，Sol 对会员开放）。在 Codex CLI 里用 ChatGPT 账号登录即可，不必按 API 高价烧 token。
- 更高额度：Pro $100 / $200（Plus 的 5 倍 / 20 倍），单人攻关 Plus 通常够用。
- 门槛：需 **VPN（ClashX）+ 海外支付方式**。

### 路径 B：API 按量 + 中转站（国内人民币，适合不想订阅/海外支付）
- 中转站提供 OpenAI 兼容端点，支付宝/微信充值、国内直连，按量调 GPT-5.6 Sol/Terra/Luna。
- **省钱要点**：日常杂活选 **Terra（均衡，约 $2.5/$15）** 或 **Luna（最省，约 $1/$6）**，
  只有硬攻关才上 **Sol（约 $5/$30，每 1M in/out）**。
- 门槛与风险见第 4 节——务必**小额充值、只跑非敏感任务**。

### 路径 C：国产官方 API（非敏感日常，最便宜、零中转风险）
- 官方渠道、国内直连、人民币、价格极低，适合写样板代码、批量处理、可公开的任务：
  - **DeepSeek**：V4-Flash 约 ¥1/M 输入、¥2/M 输出，缓存命中低至 ¥0.02/M。
  - **通义 Qwen（阿里云百炼）**：已原生支持 Codex 所需 `responses` 协议（见 6.3）。
  - **GLM Coding Plan / Kimi Code**：约 ¥49/月套餐，编程口碑好。
- **敏感数据（量化策略、持仓、凭证、账号信息）一律不走中转站，优先本机/官方可信通道。**

## 4. 中转站选择方法与安全风险（必读）

**官方风险提示**：国家安全部 2026 年专门科普"AI 中转站"风险——中转层可看到**全部 prompt 与数据**，
存在数据/情报泄露、API key 被盗、低价积分陷阱、内容不可控、商家跑路等问题；已有"一折中转→商业
情报全泄露"的安全演示。

**不硬性背书单一商家**（推荐帖普遍含返佣、且有跑路记录）。请用第三方测评工具自查后再决定：

| 自查工具 | 用途 |
|---|---|
| 中转查 `zhongzhuancha.com` | 看掺水率、在线率、延迟、公开检测报告 |
| API搜 `apisou.com` | 中转站导航、价格分组、在线状态 |
| EggStriker `eggstriker.com/ai-api` | 全景对比（直连/价格/适用场景） |
| 社区 | Linux.do / nodeseek / V2EX 的**长期真实回复**（非商家首帖） |

**选择原则**：① 运营 ≥1 年；② 按量计费、token 明细透明；③ **先小额充值**用真实任务测几天；
④ 明确支持 **Codex / `responses`**；⑤ 高频提及可作候选（**自行验证**）：AnyRouter（Linux.do
公益、注册送额度，适合先试）、302.AI、API易、LetAiCode、NoneLinear。

## 5. 安装 Codex CLI

> 本机 node 为沙箱内置（普通终端不可用），优先用 Homebrew（`/usr/local/bin/brew`）。

```bash
# 方式一：Homebrew（推荐）
brew install codex

# 方式二：官方 npm（需系统 node，而非沙箱内置 node）
npm i -g @openai/codex

# 验证
codex --version
```

## 6. 配置 Codex（`~/.codex/config.toml`）

### 6.1 用 ChatGPT 账号（路径 A，最简单）
```bash
codex login        # 浏览器走 ChatGPT 账号登录，订阅额度直接可用
```

### 6.2 接中转站（路径 B，OpenAI 兼容 / responses）
```toml
# ~/.codex/config.toml
model = "gpt-5.6-sol"            # 日常可换 gpt-5.6-terra / gpt-5.6-luna
model_provider = "relay"
model_reasoning_effort = "high"
approval_policy = "on-request"
sandbox_mode = "workspace-write"

[model_providers.relay]
name = "中转站"
base_url = "https://你的中转站地址/v1"
env_key = "RELAY_API_KEY"
wire_api = "responses"
```
设置 key：`export RELAY_API_KEY="sk-xxx"`（建议写进 `~/.zshrc`，勿提交到仓库）。

### 6.3 接国产模型（路径 C）
- **通义 Qwen（原生 responses，无需本地转换）**：
  ```toml
  model = "qwen3.7-max"
  model_provider = "dashscope"
  [model_providers.dashscope]
  name = "阿里云百炼"
  base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
  env_key = "DASHSCOPE_API_KEY"
  wire_api = "responses"
  ```
- **DeepSeek 等仅 Chat Completions 的厂商**：Codex 讲私有 Responses 协议，需本地转换代理
  （开源 `codex-relay` / `cc-switch`，把 Responses ↔ Chat Completions 实时翻译）：
  ```bash
  pip install codex-relay        # Rust 实现的轻量转换，PyPI 可装
  # 按其向导填入 DeepSeek base_url 与 key，再让 Codex 指向本地 relay
  ```
  > DeepSeek 另有 `/anthropic` 端点是给 Claude Code 用的；Codex 需 `responses`，故用 relay。

**多供应商一键切换**：可用开源 **CC Switch**（GUI 管理 Codex/Claude Code 的多套配置），
避免手改配置文件。

## 7. 完整操作步骤（从零到攻关）

1. 开 VPN（ClashX），终端确认 `brew` 可用。
2. `brew install codex`，`codex --version` 验证。
3. 二选一：
   - **订阅**：`codex login` 走 ChatGPT Plus（含 Sol）；
   - **中转/国产**：按 6.2 / 6.3 编辑 `~/.codex/config.toml` 并 `export` 对应 key。
4. `cd ~/Desktop/multiplatform-content-pipeline`。
5. 启动并先让它熟悉仓库与任务：
   ```bash
   codex
   # 进入后给目标：阅读 project-management/active/wechat-article-full-export-task.md，
   # 按第 6 节 CDP 方案攻关，先做最小验证，保留证据，按里程碑 commit。
   ```
6. 安装 VS Code（如需）与 Go/Python 扩展、官方 Codex 扩展，用于人工把关。
7. 攻关需取 token / 开微信窗口时，按任务书提示由你做轻量配合。

## 8. 成本测算（单人，参考）

| 方案 | 月成本（约） | 说明 |
|---|---|---|
| Codex + 国产 API 按量 | ¥10–50 | 非敏感日常，DeepSeek/Qwen，极省 |
| 国产 Coding Plan 套餐 | ¥49 | GLM / Kimi，重度可预测 |
| ChatGPT Plus（含 Sol） | $20 ≈ ¥145 | 攻关期主力，最省心 |
| 中转站 + Sol 按量 | 视用量，¥几十–几百 | 只在攻关时上 Sol，杂活降档 |
| ChatGPT Pro | $100 / $200 | 单人一般用不到 |

## 9. 安全红线

1. API key / 密码 / token **不写进仓库、日志、文档**；用环境变量。
2. 量化策略、持仓、凭证、隐私与商业敏感内容**绝不经过中转站**。
3. 中转站先小额、跑非敏感任务，确认明细透明再续充。
4. 对微信客户端只做只读观察 + 标准调试接口，不反编译、不重签、不持续注入。
5. ClashX / Tailscale 不为采集关闭；网络变更走 `scripts/net_preflight.py` 预检。

## 10. 参考链接

- Codex 费率（官方）：https://help.openai.com/zh-hans-cn/articles/20001415
- Codex CLI × OpenRouter（config.toml 范例）：https://openrouter.ai/blog/tutorials/codex-cli-openrouter/
- Codex × 通义千问（responses）：https://www.cnblogs.com/youring2/p/20143850
- codex-relay（Responses→Chat Completions）：https://pypi.org/project/codex-relay/
- 中转站自查：https://zhongzhuancha.com/ ｜ https://apisou.com/ ｜ https://www.eggstriker.com/ai-api
- 公众号攻关任务书：`project-management/active/wechat-article-full-export-task.md`
