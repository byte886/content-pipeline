# 微信基本操作SOP

> **文档类型**：SOP（标准操作流程）
> **更新时间**：2026-09-18
> **微信版本**：4.1.8（锁定，不升级）
> **前置依赖**：无（所有微信采集的基础）

---

## 快速参考（Cheat Sheet）

| 任务 | 操作 | 可靠性 |
|------|------|--------|
| 打开微信 | `osascript -e 'tell application "WeChat" to reopen'` | ✅ |
| 激活主窗口 | `osascript -e 'tell application "System Events" to tell process "WeChat" to set frontmost to true'` | ✅ |
| 验证窗口激活 | 菜单栏显示"微信"，红黄绿按钮彩色 | 必须做 |
| 切到聊天列表 | `Cmd+1` | ✅ |
| 退出聊天输入状态 | 点聊天列表 → 按↓键切换到空白会话 | ✅ |
| 激活搜索框 | `Cmd+F` | ✅ 最可靠 |
| 输入中文 | `echo -n "词" \| pbcopy` + `Cmd+V` | 必须用剪贴板 |
| 触发搜索 | 按↓键选建议 → 回车 | ✅ |
| 打开朋友圈 | `Cmd+4`（新窗口） | ✅ |
| 关闭当前标签页 | `Cmd+W` | ✅ |
| 前置被盖住的窗口 | `osascript -e 'tell application "System Events" to tell process "WeChat" to perform action "AXRaise" of window N'` | ✅ |

**工具优先级**：Computer use（主）> cliclick（备）> AppleScript（窗口管理）

---

> **Windows版快捷键**：将本文档中所有`Cmd`替换为`Ctrl`即可（如`Cmd+F`→`Ctrl+F`）。

---

## 1. 窗口管理

### 1.1 打开与激活

```bash
# 打开/恢复微信
osascript -e 'tell application "WeChat" to reopen'
sleep 0.3
osascript -e 'tell application "WeChat" to activate'
sleep 0.2
```

**激活验证（必须）**：菜单栏左上角显示"微信"，窗口红黄绿按钮是彩色。否则键盘和点击都不生效。

### 1.2 窗口位置与大小

```bash
# 获取位置
osascript -e 'tell application "System Events" to tell process "WeChat" to get position of window 1'
# 获取大小
osascript -e 'tell application "System Events" to tell process "WeChat" to get size of window 1'
```

**调整大小/位置**：
```bash
osascript <<'OSA'
tell application "System Events"
  tell process "WeChat"
    set size of window 1 to {900, 600}
    set position of window 1 to {0, 0}
  end tell
end tell
OSA
```

> 如果osascript不生效（通讯录页面等），用鼠标拖动窗口右下角。

### 1.3 标准布局（任务开始时统一调整）

**布局原则**：按优先级从左到右排布，横向不够再往下排，窗口不重叠。

| 优先级 | 窗口 | 1920x1200参考位置 | 大小 |
|--------|------|-------------------|------|
| 1级 | 主窗口（聊天列表） | 左上角 (0,0) | 900x600 |
| 2级 | 微信浏览器/搜索结果 | 主窗口右侧 (900,0) | 1010x600 |
| 3级 | 其它（朋友圈等） | 主窗口下方 (0,600) | 900x590 |

**窗口识别**：用标题判断，不用索引（索引随窗口开关变化）：
- 主窗口：标题"微信"
- 搜索/浏览器：标题"微信 (窗口)"或含"搜一搜"
- 朋友圈：标题"朋友圈"

**触发布局调整**：任务开始时、打开新窗口后、窗口重叠遮挡时。

### 1.4 前置被盖住的窗口

```bash
osascript -e 'tell application "System Events" to tell process "WeChat" to perform action "AXRaise" of window N'
```

> N用窗口索引，但调整前先确认窗口标题。

---

## 2. 导航操作

### 2.1 左侧导航快捷键

| 快捷键 | 功能 |
|--------|------|
| `Cmd+1` | 聊天 |
| `Cmd+2` | 通讯录 |
| `Cmd+3` | 收藏 |
| `Cmd+4` | 朋友圈（新窗口） |
| `Cmd+5~9` | 无对应功能 |

### 2.2 退出聊天输入状态

在跟某人聊天时，Tab键作用于聊天输入框，不能切到搜索框。需要先退出。

**方法（推荐）**：点击聊天列表获取焦点 → 按↓键切换会话 → 右侧显示空白微信图标即退出。

> End键只滚动列表，不切换会话，不可靠。不要点左侧导航栏空白区域，不能退出输入状态。

### 2.3 打开朋友圈

按 `Cmd+4`，新窗口打开，放在主窗口下方。

---

## 3. 搜索操作

### 3.1 完整搜索流程

1. 激活主窗口（§1.1），验证菜单栏显示"微信"
2. 按 `Cmd+F` 激活搜索框（绿色边框+下拉框）
3. 输入关键词：`echo -n "词" | pbcopy` + `Cmd+V`
4. 按↓键选择搜索建议（灰色高亮），按回车确认
5. 搜索结果窗口打开后可能被盖住，用AXRaise前置（§1.4）

> 直接在搜索框按回车无效，必须先↓键选建议。单击建议也可触发，但坐标需精确计算。

### 3.2 搜索框替换内容

按 `Cmd+F` 直接激活搜索框，直接输入新内容自动覆盖。不要用Cmd+A（会全选聊天列表）。

### 3.3 微信浏览器操作

#### 在浏览器中搜索新内容
1. 激活浏览器窗口，点击顶部搜索框
2. 直接输入新内容（自动覆盖）
3. 回车或点绿色"搜索"按钮

> ❌ 不要在浏览器中用Cmd+A，会全选整个网页。必须先点搜索框确保焦点。

#### 识别并打开视频号/公众号
1. 鼠标悬停条目上，确认变浅灰色高亮
2. 视频号有"视频号"字样，公众号有"公众号"字样
3. 确认灰色后再点击

#### 关闭多余标签页
- 点标签页右侧×按钮，或按 `Cmd+W`
- 只有一个标签页时，关闭后会显示新空白页

---

## 4. 鼠标与坐标

### 4.1 工具选择

| 操作 | 推荐工具 |
|------|---------|
| 截图/状态观察 | Computer use |
| 键盘操作 | Computer use 或 AppleScript |
| 鼠标点击/悬停 | **Computer use优先** |
| 窗口管理 | AppleScript（AXRaise/reopen） |
| 备选（报错时） | cliclick |

### 4.2 坐标原则

- **不写死坐标**，所有坐标基于当前窗口位置动态计算
- 获取窗口位置/大小后，加上相对偏移量
- 当前屏幕1920x1200，非Retina，缩放因子1
- 鼠标点击瞄准中心，不要刚好到边界

### 4.3 点击验证

- 点击前截图，点击后截图
- 一个动作后验证，不要连续点5次不检查

### 4.4 cliclick命令（备选）

```bash
cliclick c:x,y          # 单击
cliclick m:x,y          # 移动鼠标（不点击，用于悬停）
cliclick dd:x1,y1 dm:x2,y2 du:x2,y2  # 拖拽
```

### 4.5 优先用不依赖坐标的操作

| 操作 | 方法 |
|------|------|
| 退出聊天输入状态 | ↓键切换会话 |
| 触发搜索 | ↓键+回车 |
| 激活搜索框 | Cmd+F |
| 关闭标签页 | Cmd+W |
| 中文输入 | 剪贴板 pbcopy+Cmd+V |

---

## 5. 常见问题

| 问题 | 解决方案 |
|------|---------|
| Tab键没反应 | 在聊天输入状态，用↓键切换会话退出（§2.2） |
| 键盘/点击没反应 | 检查窗口是否激活：菜单栏显示"微信"，按钮彩色（§1.1） |
| 点搜索建议没触发 | 单击即可，瞄准中心，不要拖拽 |
| 窗口被盖住 | AXRaise前置（§1.4） |
| Cmd+W关了整个微信 | 只有主窗口时Cmd+W关窗口，用reopen重开 |
| 中文输入失败 | 用剪贴板，osascript keystroke不支持中文 |
| Computer use截图过期 | 重试，频繁出现则换cliclick |
| 误发消息 | 确认搜索框有绿色边框再输入 |

---

## 6. 参考文档

- 视频号采集：[SOP-wechat-channels-capture.md](SOP-wechat-channels-capture.md)
- 公众号采集：[SOP-wechat-official-article.md](SOP-wechat-official-article.md)
