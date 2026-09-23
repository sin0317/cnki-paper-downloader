#!/bin/bash
# 用 bsk 驱动真实浏览器批量下载 CNKI PDF（含验证码 request-help 循环）
# 用法: bash batch_download.sh --sid SID --targets targets.json --out D:/download
#
# 依赖：browser-skill (bsk) 已安装且浏览器已登录知网 + 校园网机构访问。
# PY 可由环境变量覆盖，默认指向 WorkBuddy 管理的 Python venv。
set -u

SID=""
TARGETS="_download_targets.json"
OUT="D:/download"
PY="${PY:-C:/Users/10276/.workbuddy/binaries/python/envs/default/Scripts/python.exe}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --sid)     SID="$2"; shift 2;;
    --targets) TARGETS="$2"; shift 2;;
    --out)     OUT="$2"; shift 2;;
    *) echo "unknown arg $1"; exit 1;;
  esac
done

[ -z "$SID" ] && { echo "need --sid (run: bsk session start --no-focus)"; exit 1; }

# 从 targets JSON 抽出 URL 列表
"$PY" -c "import json;d=json.load(open('$TARGETS'));open('_urls.txt','w').write('\n'.join(i['url'] for i in d['items']))"

LOG="batch_log.txt"
: > "$LOG"
echo "START $(date)" >> "$LOG"

n=0
while IFS= read -r url; do
  n=$((n+1))
  echo "===== [$n] navigate =====" >> "$LOG"
  timeout 50 bsk navigate "$url" --session "$SID" --wait-until domcontentloaded >> "$LOG" 2>&1

  # 最多尝试 3 次验证码（极少数情况需多点一次）
  for attempt in 1 2 3; do
    obs=$(timeout 40 bsk observe --session "$SID" 2>/dev/null)
    if echo "$obs" | grep -q "请完成安全验证"; then
      words=$(echo "$obs" | grep -oE "请依次点击【[^】]*】" | head -1)
      echo "[$n] CAPTCHA $words (attempt $attempt)" >> "$LOG"
      timeout 200 bsk request-help --session "$SID" \
        --title "CNKI验证 #$n" \
        --prompt "请依次点击$words 这3个字，验证通过后点本面板下方的 Done 交还控制权。" \
        --timeout 3m >> "$LOG" 2>&1
      echo "[$n] request-help returned" >> "$LOG"
    else
      break
    fi
  done

  # 取 PDF 下载真实 @e 编号并真实点击（evaluate.click() 无效）
  obs=$(timeout 40 bsk observe --session "$SID" 2>/dev/null)
  ref=$(echo "$obs" | grep -oE '@e[0-9]+ link "PDF下载"' | grep -oE '@e[0-9]+' | head -1)
  if [ -n "$ref" ]; then
    timeout 30 bsk click "$ref" --session "$SID" >> "$LOG" 2>&1
    echo "[$n] clicked $ref" >> "$LOG"
  else
    echo "[$n] !! NO PDF REF FOUND" >> "$LOG"
  fi
  sleep 6
  echo "[$n] pdf_count=$(ls "$OUT"/*.pdf 2>/dev/null | wc -l)" >> "$LOG"
done < _urls.txt

echo "BATCH DONE $(date)" >> "$LOG"
