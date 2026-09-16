# 电子资料采集与转码 SOP

> **适用范围**：所有行业（股票、珠宝等）的PDF/PPTX/EPUB/DOCX等电子资料
> **目标**：将外部获取的电子资料统一采集、转码、组织到知识库中

---

## 1. 目录结构（按行业隔离）

```
library/07_books/
├── raw/                           # 原始文件（不入库，gitignore）
│   ├── stock/                     # 股票行业原始资料
│   └── jewelry/                   # 珠宝行业原始资料
├── extracted/                     # 转码后的Markdown（知识来源，入库）
│   ├── stock/
│   └── jewelry/
└── 精华/                          # 结构化精华文稿（入库）
    ├── stock/
    └── jewelry/
```

**原则**：
- `raw/` 放原始文件（PDF/PPTX等），大文件不入库
- `extracted/` 放转码后的全文Markdown，作为知识来源
- `精华/` 放AI生成的结构化精华，面向快速阅读

---

## 2. 采集流程

### 2.1 获取电子资料

来源渠道：
1. 用户直接提供（上传/指定路径）
2. 公众号/视频号中推荐的书籍 → 搜索电子版
3. 行业社区（生财有术、雪球等）分享的资料
4. 公开免费电子书网站

### 2.2 命名规范

原始文件命名：`<书名>.<扩展名>`
- 示例：`股票大作手回忆录.pdf`
- 含版本信息：`趋势交易法(第2版).pdf`

转码后命名：`<书名>_extracted.md`

### 2.3 存放位置

按行业放入 `library/07_books/raw/<行业>/`

---

## 3. 转码流程

### 3.1 工具

统一使用 `scripts/books/batch_extract_books.py`

```bash
python3 scripts/books/batch_extract_books.py <输入目录> <输出目录>
```

### 3.2 自动判断提取方式

| 文件类型 | 判断条件 | 提取方式 |
|---|---|---|
| PDF有文本层 | 文本页占比>20% 或 平均>30字符/页 | PyMuPDF直接提取 |
| PDF扫描件 | 文本页占比<20% 且 平均<30字符/页 | Vision OCR（1.5秒/页） |
| PPTX | 所有 | python-pptx提取 |
| DOCX | 所有 | python-docx提取（待实现） |
| EPUB | 所有 | ebooklib提取（待实现） |

### 3.3 批量转码

```bash
# 股票行业
python3 scripts/books/batch_extract_books.py library/07_books/raw/stock library/07_books/extracted/stock

# 珠宝行业
python3 scripts/books/batch_extract_books.py library/07_books/raw/jewelry library/07_books/extracted/jewelry
```

### 3.4 校验门

转码完成后必须检查：
1. **页数对账**：输出Markdown的分页节数 ≥ 源文件页数
2. **空页检测**：连续空白页标记出来
3. **乱码检测**：统计`�`替换字符，超阈值告警
4. **首尾抽样**：抽查第1页、中间1页、最后1页

---

## 4. 知识组织

### 4.1 精华提取

对每本转码后的书籍，生成结构化精华文稿：

```
精华文稿结构：
1. 核心哲学（3-5条）
2. 交易/分析方法（可操作步骤）
3. 经典语录（10-20条）
4. 对量化系统的启示
5. 与其他书籍的对比
```

位置：`library/07_books/精华/<行业>/`

### 4.2 知识详解

将书籍内容拆解到行业知识库的对应分类：

```
domains/<行业>/knowledge_base/
├── 交易哲学/
├── 技术分析/
├── 基本面分析/
├── ...
└── 书籍详解/
    └── <书名>.md
```

### 4.3 去重

- 同一本书的精华和全文只保留一份权威版
- 不同书籍中重复的知识点，在知识详解中合并，标注来源

---

## 5. 网盘同步

```bash
# 原始文件同步
bash scripts/netdisk/sync_library.sh "<行业>知识库" "07_books/raw/<行业>" "07_books/raw/<行业>"

# 转码稿同步
bash scripts/netdisk/sync_library.sh "<行业>知识库" "07_books/extracted/<行业>" "07_books/extracted/<行业>"

# 精华同步
bash scripts/netdisk/sync_library.sh "<行业>知识库" "07_books/精华/<行业>" "07_books/精华/<行业>"
```

---

## 6. 增量更新

1. 新资料放入 `raw/<行业>/`
2. 运行批量转码（已存在的自动跳过）
3. 对新转码的书籍生成精华
4. 更新行业知识库README的书籍清单
5. 同步网盘

---

## 7. 常见问题

| 问题 | 解决方案 |
|---|---|
| PDF有文本层但提取乱码 | 检查编码，尝试pdfplumber替代 |
| OCR速度慢 | 先用文本层提取，只对确实无文本的页OCR |
| PPTX图片中的文字未提取 | 需要OCR PPTX中的图片（待实现） |
| 书籍找不到电子版 | 在知识库中标注"待获取"，告知用户 |

---

*最后更新：2026-09-16*
