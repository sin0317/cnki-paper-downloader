---
name: cnki-paper-downloader
description: 当用户需要批量下载 CNKI（知网）论文 PDF 全文，特别是通过"已登录浏览器 + 校园网机构访问"自动化获取文献原文时使用。覆盖「cnki CLI 检索 → 抽取下载目标 → bsk 控制浏览器导航/过验证码/真实点击下载 → 校验 PDF → 扫描件 OCR 补表」完整流程。agent_created: true
---

# CNKI 论文自动化下载（含浏览器控制）

## 适用场景
- 用户有一批知网文献（标题/URL 列表），需要批量下载 PDF 全文。
- 用户已用校园网 / 机构访问登录知网，浏览器能免费下全文。
- 需要把"检索 → 下载 → 校验 → OCR 补表"串成可复用流水线。
- 典型触发语："把这批文献下下来""自动下载知网论文""用浏览器批量下 PDF"。

## 前置依赖（均为已安装 skill / 工具）
- **browser-skill (bsk)**：驱动用户真实已登录浏览器（带知网 cookie + 校园网机构访问）。这是下载的关键——CLI 与裸脚本拉不到全文（反爬 + 无浏览器 session）。
- **cnki-search skill** 的 `cnki.exe`：检索元数据、产出文献列表 JSON（可选，若用户已有文献列表则跳过）。
- **pdf-scan-ocr skill**：扫描件 PDF 用多模态读图补表（见步骤 6）。

## 硬约束（红线）
- **不得**读取、转发、存储用户的浏览器 cookie / 知网 token。
- **每开一篇新文献，CNKI 必弹一次点选验证码**（clickWord：请依次点击【x,y,z】）。需通过 `bsk request-help` 交用户点，不可尝试自动识别图片字（不可靠且违规）。
- 下载全文依赖用户已登录 + 校园网机构访问；skill 只负责编排，不绕过鉴权。

## 工作流

### 步骤 1：获取文献列表
- 若用户已有文献列表 JSON（如 `cnki_survey_result.json`），直接进入步骤 2。
- 否则用 `cnki.exe search "<关键词>" --field=title --size=N --format=json` 检索（注意 title 检索易失配，偏好短查询）。

### 步骤 2：抽取下载目标（TopN）
- 运行 `scripts/extract_targets.py`：从文献列表按"例数 / 被引 / 年份"排序，选出 TopN，生成带安全文件名的 targets JSON。
- 例数从标题正则 `\d+例` 提取；支持 `--by cases|cited|year`、`--min-cases`、`--type-filter`。
- 例：`python extract_targets.py cnki_survey_result.json --top 20 --by cases --out targets.json`

### 步骤 3：启动浏览器会话（bsk 控制浏览器）
```bash
SID=$(timeout 40 bsk session start --no-focus)
echo "$SID" > _bsk_sid.txt
bsk status   # 确认 1 个浏览器已连接
```
- 浏览器需已登录知网 + 机构访问。页面顶部显示"XX 大学图书馆 机构登录"即生效。

### 步骤 4：批量下载（bsk 控制浏览器）
- 运行 `scripts/batch_download.sh --sid "$SID" --targets targets.json --out D:/download`
- 脚本对每篇：navigate → 若 observe 出现"请完成安全验证"则 `request-help` 交用户点字 → 取 `@eXX link "PDF下载"` 真实 `bsk click`（evaluate.click 无效）→ sleep 等落地 → 下一篇。
- **用户侧**：验证码弹窗依次点那 3 个字 + Done，自动下一篇，中间不卡。

### 步骤 5：校验 PDF
- 运行 `scripts/verify_pdfs.py --src D:/download --move-to <项目/下载原文> --keep-src`：
  - 校验每个 .pdf 头部为 `%PDF`；非 PDF（验证码残留页等）隔离不删。
  - 合法 PDF 搬进项目目录；保留下载目录原件作备份。

### 步骤 6：扫描件 OCR 补表
- 对 pypdf 抽不出文字的扫描件，调用 **pdf-scan-ocr skill**：PyMuPDF 渲染 PNG → 多模态 Read 识别关键句 → 补回判定表。
- 见该 skill 的 `scripts/render_pages.py`。

## scripts 说明
- `extract_targets.py`：文献列表 → TopN 下载目标 JSON（带安全文件名）。
- `batch_download.sh`：bsk 批量下载（含验证码 request-help 循环 + 真实点击）。
- `verify_pdfs.py`：PDF 合法性校验 + 搬运。

## references
- `cnki_antibot.md`：知网反爬 / 验证码 / 机构登录 / bsk 命令速查与坑位。

## 关键坑位（经验）
1. CNKI 文章页是 JS 反爬桩页，裸 `urllib`/requests 抓不到下载端点；必须走浏览器。
2. `evaluate("a.click()")` 无法触发 CNKI 下载处理器，**必须真实 `bsk click @eXX`**。
3. 每篇新文献弹一次点选验证码；首访有短暂信任期（第 1 篇可能不弹）。
4. 下载目录是浏览器默认目录（用户机多为 `D:/download` 或 `~/Downloads`），先确认再搬。
5. 题名"N 例"可能是【用药例数】也可能是【ADR 例数】，需读原文区分，勿直接相加（详见项目判定表流程）。
