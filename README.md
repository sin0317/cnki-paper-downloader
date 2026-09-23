# cnki-paper-downloader

WorkBuddy skill — 自动化批量下载 CNKI（知网）论文 PDF 全文。

## 它能做什么

把「检索 → 下载 → 校验 → OCR 补表」串成一条可复用流水线：

1. **cnki CLI 检索**：用 `cnki-search` skill 的 `cnki.exe` 拉取文献元数据（可选，若已有文献列表则跳过）。
2. **抽取下载目标**：按例数 / 被引 / 年份排序，选出 TopN，生成带安全文件名的下载清单。
3. **bsk 控制浏览器下载**：用 `browser-skill` 驱动你**已登录**的真实浏览器，自动导航、弹验证码交你点、真实点击 PDF 下载。
4. **校验 PDF**：过滤非 PDF（验证码残留页），搬运进项目目录。
5. **扫描件 OCR 补表**：配合 `pdf-scan-ocr` skill 处理抽不出文字的扫描件。

## 前置依赖

| 依赖 | 说明 |
|------|------|
| `browser-skill` (bsk) | 驱动真实浏览器。**下载全文的关键**——CLI 与裸脚本拉不到（反爬 + 无浏览器 session）。 |
| `cnki-search` skill 的 `cnki.exe` | 检索元数据、产出文献列表（可选）。 |
| `pdf-scan-ocr` skill | 扫描件 PDF 多模态 OCR 补表（可选）。 |

> 浏览器需已登录知网 + 校园网 / 机构访问，页面顶部显示「XX 大学图书馆 机构登录」即生效。

## 红线

- **不**读取 / 转发 / 存储你的浏览器 cookie 与知网 token。
- 每开一篇新文献，CNKI 必弹一次点选验证码，需你人工点（不可自动识别图片）。
- 下载全文依赖你已经登录 + 机构访问；skill 只负责编排。

## 快速开始

```bash
# 1. 抽取 Top20 下载目标
python scripts/extract_targets.py cnki_survey_result.json --top 20 --by cases --out targets.json

# 2. 启动浏览器会话（需已登录知网）
SID=$(bsk session start --no-focus)
echo "$SID" > _bsk_sid.txt

# 3. 批量下载（遇到验证码会弹出交你点）
bash scripts/batch_download.sh --sid "$SID" --targets targets.json --out D:/download

# 4. 校验 + 搬运
python scripts/verify_pdfs.py --src D:/download --move-to "项目/下载原文" --keep-src
```

## 关键坑位

1. 知网文章页是 JS 反爬桩页，裸 `urllib` 抓不到下载端点 → 必须走浏览器。
2. `evaluate("a.click()")` 触发不了 CNKI 下载 → 必须真实 `bsk click @eXX`。
3. 每篇新文献弹一次点选验证码；首篇有短暂信任期可能不弹。
4. 题名「N 例」可能是【用药例数】也可能是【ADR 例数】，需读原文区分，勿直接相加。

## 文件结构

```
cnki-paper-downloader/
├── SKILL.md
├── scripts/
│   ├── extract_targets.py   # 文献列表 → TopN 下载目标
│   ├── batch_download.sh    # bsk 批量下载（含验证码循环）
│   └── verify_pdfs.py       # PDF 合法性校验 + 搬运
└── references/
    └── cnki_antibot.md      # 知网反爬 / 验证码 / 机构登录速查
```
