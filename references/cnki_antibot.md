# 知网反爬 / 验证码 / 机构登录 速查

## 浏览器控制（browser-skill / bsk）
- 启动会话：`bsk session start --no-focus` → 返回 SID，存 `_bsk_sid.txt`
- 检查连接：`bsk status`（需至少 1 个浏览器已连接；若阻塞说明扩展未连上）
- 导航：`bsk navigate <url> --session <SID> --wait-until domcontentloaded|networkidle`
- 观察元素：`bsk observe --session <SID>`（输出 `@eXX` 编号、按钮/链接文本）
- 真实点击：`bsk click @eXX --session <SID>`（能触发下载；`evaluate` 的 `.click()` 不行）
- 交用户过点选验证码：`bsk request-help --session <SID> --title "..." --prompt "请依次点击【x,y,z】这3个字…" --timeout 3m`

## 关键经验
- 文章摘要页是 JS 反爬桩页（~2KB，无 filename/tablename/下载端点），裸 `urllib`/`requests` 抓不到全文 → 必须浏览器。
- 首访有短暂信任期（第 1 篇可能不弹验证码），之后每开一篇新文献必弹一次点选验证码。
- 验证码为 clickWord 类型："请依次点击【叔,头,但】"，需人工点，不可自动识别图片。
- 过一次验证码通常解锁后续若干篇，但仍会再次触发。
- 机构访问：页面顶部显示"XX 大学图书馆 机构登录"说明校园网机构通道生效，可免费下 PDF。
- "PDF下载"(`@eXX`) 和 "CAJ下载" 是两个不同按钮；优先选 PDF（便于文本抽取与 OCR）。
- 下载目录为浏览器默认目录（Win 多为 `D:/download` 或 `C:/Users/xxx/Downloads`），先确认再批量搬运。

## 检索注意事项（cnki-search / cnki.exe）
- `cnki.exe search "<关键词>" --field=title --size=N --format=json`：title 字段检索易失配，优先用短查询。
- JSON 顶层是 dict，`results` 才是数组（`d["results"]`）。
- CLI 只能检索元数据，**不提供下载**。
