#!/usr/bin/env python3
"""
加拿大旅行 Line Bot — 使用 Flask 架設的 Webhook 伺服器

部署方式：
  方案一：Render / Railway / Fly.io 免費部署（推）
  方案二：你的 Windows 本機 + ngrok（臨時測試）
  方案三：OpenClaw 轉接（免伺服器）

流程：
  Line User → Line Messaging API → Webhook → 本程式 → Line User
  
前置需求：
  1. Line Developers 建立 Messaging API Channel
  2. 取得 Channel Access Token + Channel Secret
  3. 部署到雲端或本機 ngrok
"""

import os, sys, json, re, logging
from pathlib import Path

# ── 設定 ──────────────────────────────────────────────────────
BOT_DIR = Path(__file__).parent
DATA_PATH = BOT_DIR / 'data.json'
CONFIG_PATH = BOT_DIR / 'line_config.json'

# Line 金鑰（從 line_config.json 讀取，或從環境變數）
CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')
CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', '')

# 嘗試從設定檔載入
if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET:
    try:
        with open(CONFIG_PATH, encoding='utf-8') as f:
            cfg = json.load(f)
        CHANNEL_ACCESS_TOKEN = CHANNEL_ACCESS_TOKEN or cfg.get('channel_access_token', '')
        CHANNEL_SECRET = CHANNEL_SECRET or cfg.get('channel_secret', '')
    except (FileNotFoundError, json.JSONDecodeError):
        pass

with open(DATA_PATH, encoding='utf-8') as f:
    DATA = json.load(f)

# ── Handler functions ────────────────────────────────────────

def show_day(n):
    plan = DATA['daily_plan'][n-1]
    lines = [
        f"📅 Day {n} — {plan['date']} ({plan['dow']})",
        f"📍 {plan['title']}",
        f"📝 {plan['detail']}",
    ]
    if n == 2:
        lines.append('\n🚗 到卡加利後取車（Alamo RAV4），開1.5h到班夫鎮')
    elif n == 7:
        lines.append('\n🚗 冰原大道(93號) 230km，約4-5hrs，小心野生動物與結冰')
        lines.append('🎫 哥倫比亞冰原雪車現場購票')
    elif n == 9:
        lines.append('\n🚗 最長車程290km/4h，建議一早出發')
    return '\n'.join(lines)


def show_preparations():
    lines = ['📋 行前準備：']
    for cat in DATA['preparations']:
        lines.append(f"\n【{cat['category']}】")
        for item in cat['items']:
            lines.append(f"✅ {item}")
    return '\n'.join(lines)


def show_car():
    r = DATA['rental_car']
    lines = [
        '🚗 租車資訊',
        f'車行：{r["provider"]}',
        f'車型：{r["model"]}（4人+4行李）',
        f'價格：{r["price"]}',
        f'取車：{r["pickup"]}（10/3）',
        f'還車：{r["return"]}（10/12）',
        '',
        '📌 取車要帶：台灣駕照正本 / 國際駕照 / 護照 / 信用卡（額度5萬↑，預扣400加幣押金）',
        '',
        '📌 自駕重點：',
    ]
    for tip in DATA['driving_tips']:
        lines.append(f'⚠️ {tip}')
    return '\n'.join(lines)


def show_gas():
    return (
        '⛽ 加油須知\n\n'
        '1. 加拿大加油站多為自助加油\n'
        '2. 信用卡須開通「預借現金」+4位數PIN碼\n'
        '3. 建議VISA和MasterCard各一張\n'
        '4. 冰原大道油站間距長，看到就加滿\n'
        '5. 一般加 regular (87) 即可'
    )


def show_hotels():
    lines = ['🏨 住宿\n']
    for h in DATA['hotels']:
        price = f' ({h.get("price", "")})' if 'price' in h else ''
        room = f' — {h["room"]}' if 'room' in h else ''
        note = f'（{h["note"]}）' if 'note' in h else ''
        lines.append(f'📅 {h["day"]}：{h["location"]}（{h["nights"]}晚）{price}{room}{note}')
    return '\n'.join(lines)


def show_weather():
    return (
        '🌤 10月初天氣\n\n'
        '班夫白天5~12°C，晚上-2~5°C\n'
        '冰原大道可能-5~5°C，風大\n'
        '卡加利8~15°C\n\n'
        '🧥 洋蔥式穿法：底層發熱衣 → 刷毛/輕羽絨 → 防風防水外套\n'
        '🧤 必備：帽子、手套、防水登山鞋\n'
        '⚠️ 10月初可能下雪'
    )


def show_emergency():
    e = DATA['emergency']
    return (
        '🆘 緊急\n\n'
        f'🚔 報警/消防/救護：{e["canada_police"]}\n'
        f'🚗 租車 Alamo：{e["rental_company"]}\n'
        f'🏛 駐溫哥華辦事處：{e["taiwan_embassy"]}\n\n'
        '先存手機+寫紙條放錢包'
    )


def show_members():
    return (
        f'👥 {DATA["trip"]["members"]}\n'
        f'🎯 你負責開車和租車\n'
        f'RAV4後車廂可放4個29吋行李箱'
    )


def show_all_days():
    lines = ['📅 完整行程\n']
    for p in DATA['daily_plan']:
        lines.append(f"Day{p['day']}（{p['date']} {p['dow']}）：{p['title']}")
    return '\n'.join(lines)


def show_budget():
    r = DATA['rental_car']
    return (
        '💰 已知花費\n\n'
        f'✈️ 機票：NT$32,178/人\n'
        f'✈️ 國內段：NT$3,750~9,574/人\n'
        f'🚗 租車：{r["price"]}\n'
        f'🏰 費爾蒙10/7：NT$59,191（4人分）\n'
        f'⛽ 油費估：NT$5,000~8,000\n\n'
        '建議收公基金 cover 共同開銷'
    )


def show_help():
    return (
        '🇨🇦 加拿大旅行小幫手\n\n'
        '你可以問我：\n'
        '「第X天」→ 每日行程\n'
        '「要帶什麼」→ 準備清單\n'
        '「租車」→ 租車細節\n'
        '「加油」→ 加油須知\n'
        '「飯店」→ 住宿安排\n'
        '「天氣」→ 穿衣建議\n'
        '「緊急電話」→ 聯絡方式\n'
        '「全部行程」→ 11天總覽\n'
        '「花費」→ 預算參考'
    )


# ── Keyword mapping ──────────────────────────────────────────

KW_MAP = [
    (['第1天', '第一天', '10/2', '10月2'], lambda: show_day(1)),
    (['第2天', '第二天', '10/3', '10月3'], lambda: show_day(2)),
    (['第3天', '第三天', '10/4', '10月4'], lambda: show_day(3)),
    (['第4天', '第四天', '10/5', '10月5'], lambda: show_day(4)),
    (['第5天', '第五天', '10/6', '10月6'], lambda: show_day(5)),
    (['第6天', '第六天', '10/7', '10月7'], lambda: show_day(6)),
    (['第7天', '第七天', '10/8', '10月8', '冰原大道'], lambda: show_day(7)),
    (['第8天', '第八天', '10/9', '10月9', '瑪琳湖', '精靈島'], lambda: show_day(8)),
    (['第9天', '第九天', '10/10', '10月10'], lambda: show_day(9)),
    (['第10天', '第十天', '10/11', '10月11'], lambda: show_day(10)),
    (['第11天', '第十一天', '10/12', '10月12'], lambda: show_day(11)),
    (['文件', '證件', '準備', '要帶', '帶什麼', '行李', '清單'], show_preparations),
    (['汽車', '車子', '自駕', '開車', '駕駛', '租車', '還車', '取車', 'alamo', 'rav4'], show_car),
    (['加油', '油站', '汽油', 'gas', '加油站'], show_gas),
    (['飯店', '旅館', '住宿', '酒店', '過夜', '住哪', '費爾蒙', '路易斯', '費爾蒙'], show_hotels),
    (['天氣', '穿', '衣服', '衣物', '保暖', '幾度', '溫度', '氣溫'], show_weather),
    (['緊急', '電話', '警察', 'embassy', '醫院', '急', '出事', '意外'], show_emergency),
    (['預算', '費用', '多少錢', '花費', '價錢', '價格', 'total', '總共'], show_budget),
    (['行程', '總覽', '全部', '每天', '所有', '整個', '計畫', '計劃'], show_all_days),
    (['人', '團員', '成員', '誰去', '3女', '幾個人', '總共幾'], show_members),
    (['保險', '醫療', '旅平', '平安'],
     lambda: "建議投保旅平險+海外醫療險。加拿大醫療費昂貴，沒有保險掛號可能數百加幣。建議旅平險保500萬以上。"),
    (['esim', 'sim', '上網', '網路', '網卡', '漫遊', 'wifi'],
     lambda: "建議買有加拿大電話號碼的eSIM/SIM卡。好處：導航較穩、租車公司可聯絡你、緊急可撥打當地電話。推薦：Airalo / 淘寶加拿大eSIM / 中華電信輕量漫遊"),
    (['幫助', 'help', '可以問', '功能', '指令', '怎麼用', 'hi', '嗨', '哈囉', '你好', 'hello'], show_help),
]


def answer(question):
    q = question.strip()
    if not q:
        return show_help()
    q_lower = q.lower()

    for keywords, handler in KW_MAP:
        for kw in keywords:
            if kw.lower() in q_lower:
                return handler()

    if '天' in q and re.search(r'\d+', q):
        nums = re.findall(r'\d+', q)
        if nums:
            d = int(nums[0])
            if 1 <= d <= 11:
                return show_day(d)

    return (
        '不太確定你問什麼 🤔\n\n'
        '試試：\n'
        '「第3天」/「要帶什麼」/「租車」/「加油」/「全部行程」'
    )


# ── Webhook Server（Flask） ──────────────────────────────────

def create_app():
    """建立 Flask 應用（供部署使用）"""
    from flask import Flask, request, abort

    app = Flask(__name__)

    @app.route('/')
    def index():
        return '🇨🇦 Canada Travel Bot is running!'

    @app.route('/webhook', methods=['POST'])
    def webhook():
        # Verify signature
        if CHANNEL_SECRET:
            from hashlib import sha256
            import hmac
            signature = request.headers.get('X-Line-Signature', '')
            body = request.get_data(as_text=True)
            hash = hmac.new(CHANNEL_SECRET.encode('utf-8'), body.encode('utf-8'), sha256).digest()
            expected = base64.b64encode(hash).decode()
            if signature != expected:
                abort(401)

        data = request.json
        events = data.get('events', [])

        for event in events:
            if event['type'] == 'message' and event['message']['type'] == 'text':
                user_msg = event['message']['text']
                reply_token = event['replyToken']
                reply = answer(user_msg)
                reply_line(reply_token, reply)

        return 'OK'

    return app


def reply_line(reply_token, text):
    """回覆 Line 訊息"""
    if not CHANNEL_ACCESS_TOKEN:
        logging.warning("CHANNEL_ACCESS_TOKEN 未設定，跳過回覆")
        return

    import requests
    url = 'https://api.line.me/v2/bot/message/reply'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {CHANNEL_ACCESS_TOKEN}',
    }
    data = {
        'replyToken': reply_token,
        'messages': [{'type': 'text', 'text': text}],
    }
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=10)
        if resp.status_code != 200:
            logging.error(f"Line API error: {resp.status_code} {resp.text}")
    except Exception as e:
        logging.error(f"Line API request failed: {e}")


# ── 設定產生器 ────────────────────────────────────────────────

def setup():
    """互動式設定精靈——引導建立 Line Bot"""
    print("=" * 60)
    print("🇨🇦  加拿大旅行 Line Bot — 設定精靈")
    print("=" * 60)
    print()
    print("你需要先到 Line Developers Console 建立一個 Messaging API Channel：")
    print("  1. 打開 https://developers.line.biz/console/")
    print("  2. 登入（用你的 Line 帳號）")
    print("  3. 按「Create Provider」取名「Canada Travel」")
    print("  4. 按「Create Channel」→「Messaging API」")
    print("  5. 填寫基本資料（Channel name: 加拿大旅行小幫手）")
    print("  6. 建立後在 Basic Settings 頁面：")
    print("     - Channel Secret（複製）")
    print("     - 往下到 Messaging API → Channel Access Token（按 Issue）")
    print()
    
    token = input("貼上 Channel Access Token > ").strip()
    secret = input("貼上 Channel Secret > ").strip()
    
    config = {
        'channel_access_token': token,
        'channel_secret': secret,
    }
    
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print()
    print(f"✅ 已儲存到 {CONFIG_PATH}")
    print()
    print("下一步：部署到雲端")
    print()
    print("選項一：Render（推薦，免費）")
    print("  1. 把 canada/ 整個資料夾推到 GitHub")
    print("  2. 在 Render 選 Web Service，連 GitHub repo")
    print("  3. Start Command: gunicorn canada_bot_line:app")
    print("  4. 環境變數填入 LINE_CHANNEL_ACCESS_TOKEN 和 LINE_CHANNEL_SECRET")
    print("  5. 拿到 URL 後回 Line Console 設定 Webhook URL")
    print()
    print("選項二：本機測試（ngrok）")
    print("  1. python canada_bot_line.py  run")
    print("  2. ngrok http 5000")
    print("  3. 把 ngrok URL+ /webhook 貼到 Line Console")
    print()
    print("選項三：用 OpenClaw 轉接（最簡單，不用架）")
    print("  只要設好 config，我就可以幫你轉發")


# ── Main ──────────────────────────────────────────────────────

def main():
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'setup':
        setup()
        return
    
    if len(sys.argv) > 1 and sys.argv[1] == 'run':
        # 啟動 Flask 伺服器
        app = create_app()
        port = int(os.environ.get('PORT', 5000))
        print(f"🇨🇦 Canada Travel Bot 啟動於 :{port}")
        print(f"   Webhook URL: http://你的IP:{port}/webhook")
        app.run(host='0.0.0.0', port=port, debug=True)
        return

    # 互動模式
    print("=" * 60)
    print("🇨🇦  加拿大旅行問答小幫手")
    print(f"📅  {DATA['trip']['name']}")
    print("=" * 60)
    print("輸入「幫助」看功能 | exit 離開")
    print()

    while True:
        try:
            q = input("🧑 > ").strip()
            if not q:
                continue
            if q.lower() in ('exit', 'quit', 'q', '離開'):
                print("👋 一路平安 🍁")
                break
            print()
            print(answer(q))
            print()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 一路平安 🍁")
            break


# ── WSGI entry point ────────────────────────────────────────────────
app = create_app()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # 如果有 Flask 才載入，否則只跑互動模式
    try:
        import flask
    except ImportError:
        pass

    main()
