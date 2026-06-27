#!/usr/bin/env python3
"""
加拿大旅行問答機器人（Line/Telegram 用）
用法：
  1. 直接執行：python canada_bot.py，然後輸入問題
  2. 透過 OpenClaw 回答：用 /ask_canada <問題> 把我當成 bot

支援的提問範例：
  - 「第3天去哪裡？」
  - 「要帶什麼文件？」
  - 「加油要注意什麼？」
  - 「冰原大道要注意什麼」
  - 「飯店訂了哪些？」
  - 「10/7住哪裡？」
  - 「租車多少錢？」
  - 「總共幾個人去？」
  - 「緊急電話是多少？」
  - 「天氣如何要穿什麼？」
"""

import json, os, sys, re

DATA_PATH = os.path.join(os.path.dirname(__file__), 'data.json')

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
        lines.append('\n🚗 到卡加利後取車（Alamo RAV4），開1.5小時到班夫鎮')
    elif n == 7:
        lines.append('\n🚗 重點：冰原大道(93號公路)全程230km，約4-5小時車程，沿途超美！小心野生動物和結冰路面')
        lines.append('🎫 哥倫比亞冰原巨型雪車可現場購票')
    elif n == 9:
        lines.append('\n🚗 最長車程290km/4h，建議一早出發，中途停阿塔巴斯卡瀑布')
    return '\n'.join(lines)


def show_preparations():
    lines = ['📋 行前準備清單：']
    for cat in DATA['preparations']:
        lines.append(f"\n【{cat['category']}】")
        for item in cat['items']:
            lines.append(f"  ✅ {item}")
    return '\n'.join(lines)


def show_car():
    r = DATA['rental_car']
    lines = [
        '🚗 租車資訊',
        f'  車行：{r["provider"]}',
        f'  車型：{r["model"]}（載4人+4行李）',
        f'  價格：{r["price"]}',
        f'  取車：{r["pickup"]}（10/3）',
        f'  還車：{r["return"]}（10/12）',
        '',
        '📌 取車要帶：',
        '  • 台灣駕照正本',
        '  • 國際駕照',
        '  • 護照',
        '  • 駕駛本人信用卡（額度5萬↑，預扣約400加幣押金）',
        '',
        '📌 自駕注意：',
    ]
    for tip in DATA['driving_tips']:
        lines.append(f'  ⚠️  {tip}')
    return '\n'.join(lines)


def show_gas():
    return (
        '⛽ 加油須知\n\n'
        '1. 加拿大加油站多為自助加油\n'
        '2. 信用卡須開通「預借現金功能」+設定4位數PIN碼\n'
        '3. 建議VISA和MasterCard各準備一張\n'
        '4. 冰原大道(93號)油站間距長，看到加油站就加滿\n'
        '5. 偏遠山區油價較貴，建議在大城鎮加滿再進山\n'
        '6. 10月初可能部分加油站已休息，注意營業時間\n'
        '7. 一般加 regular (87) 即可，租車時可確認'
    )


def show_hotels():
    lines = ['🏨 住宿安排\n']
    for h in DATA['hotels']:
        price = f' ({h.get("price", "")})' if 'price' in h else ''
        room = f' — {h["room"]}' if 'room' in h else ''
        note = f'（{h["note"]}）' if 'note' in h else ''
        lines.append(f'📅 {h["day"]}：{h["location"]}（{h["nights"]}晚）{price}{room}{note}')
    return '\n'.join(lines)


def show_weather():
    return (
        '🌤 10月初加拿大洛磯山脈天氣\n\n'
        '• 班夫/路易斯湖 白天：5~12°C\n'
        '• 班夫/路易斯湖 晚上：-2~5°C\n'
        '• 冰原大道山頂：可能 -5~5°C，風大\n'
        '• 賈斯珀：白天 3~10°C\n'
        '• 卡加利：白天 8~15°C（較暖）\n'
        '• 溫哥華：白天 10~16°C（沿海較暖）\n\n'
        '🧥 穿衣建議（洋蔥式穿法）：\n'
        '  底層：發熱衣/排汗衣\n'
        '  中層：刷毛/輕羽絨\n'
        '  外層：防風防水外套（必備！）\n'
        '  配件：帽子、手套、圍巾\n'
        '  鞋子：防水登山鞋/靴（走峽谷步道）\n\n'
        '⚠️ 10月初洛磯山可能下雪，冰原大道可能路面結冰'
    )


def show_emergency():
    e = DATA['emergency']
    return (
        '🆘 緊急聯絡\n\n'
        f'🚔 加拿大報警/消防/救護：{e["canada_police"]}\n'
        f'🚗 租車公司客服：{e["rental_company"]}\n'
        f'🏛 駐溫哥華辦事處：{e["taiwan_embassy"]}\n\n'
        f'🏥 醫療：{e["medical"]}\n\n'
        '💡 建議把這些號碼存入手機+寫在紙條上放錢包'
    )


def show_members():
    return (
        f'👥 團員：{DATA["trip"]["members"]}\n'
        f'🎯 你的角色：{DATA["trip"]["your_role"]}\n\n'
        '3女1男，你負責開車和租車\n'
        '行李空間：RAV4後車廂可放4個29吋行李箱左右'
    )


def show_all_days():
    lines = ['📅 完整行程一覽\n']
    for p in DATA['daily_plan']:
        lines.append(f"Day {p['day']}（{p['date']} {p['dow']}）：{p['title']}")
        lines.append(f"   {p['detail']}")
    return '\n'.join(lines)


def show_budget():
    r = DATA['rental_car']
    return (
        '💰 已知花費\n\n'
        f'✈️ 機票（台北-溫哥華來回）：約 NT$32,178/人\n'
        f'✈️ 國內段（溫哥華-卡加利來回）：約 NT$3,750~9,574/人\n'
        f'🚗 租車：{r["price"]}（NT$13,440/週，你負擔？平分？）\n'
        f'🏰 路易斯湖費爾蒙（10/7一晚）：NT$59,191（四人分）\n'
        f'⛽ 油費：預估 NT$5,000~8,000（來回約 1,000km）\n'
        f'🅿️ 停車費/國家公園門票：另外\n\n'
        '建議每人先收一筆公基金 cover 共同開銷'
    )


def show_help():
    return (
        '🤖 加拿大旅行小幫手\n\n'
        '你可以問我：\n'
        '  • 「第X天去哪裡？」→ 每日行程\n'
        '  • 「要帶什麼文件？」→ 準備清單\n'
        '  • 「租車多少錢？」→ 租車細節\n'
        '  • 「加油要注意什麼？」→ 加油須知\n'
        '  • 「飯店住哪裡？」→ 住宿安排\n'
        '  • 「天氣如何？」→ 天氣+穿衣建議\n'
        '  • 「緊急電話」→ 緊急聯絡方式\n'
        '  • 「全部行程」→ 11天總覽\n'
        '  • 「總花費」→ 預算參考\n\n'
        '直接輸入問題，我從資料庫回答！'
    )


# ── Keyword mapping (must come after all handler defs) ───────

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
    (['飯店', '旅館', '住宿', '酒店', '過夜', '住哪', '費爾蒙', '路易斯'], show_hotels),
    (['天氣', '穿', '衣服', '衣物', '保暖', '幾度', '溫度', '氣溫'], show_weather),
    (['緊急', '電話', '警察', 'embassy', '醫院', '急', '出事', '意外'], show_emergency),
    (['預算', '費用', '多少錢', '花費', '價錢', '價格', 'total', '總共'], show_budget),
    (['行程', '總覽', '全部', '每天', '所有', '整個', '計畫', '計劃'], show_all_days),
    (['人', '團員', '成員', '誰去', '3女', '幾個人', '總共幾'], show_members),
    (['保險', '醫療', '旅平', '平安'],
     lambda: "建議出發前投保：台灣旅平險 + 加拿大當地醫療險。加拿大醫療費用昂貴，沒有保險一次掛號可能數百加幣。台灣的旅平險建議保至少500萬以上，附加海外醫療險。"),
    (['esim', 'sim', '上網', '網路', '網卡', '漫遊', 'wifi'],
     lambda: "建議購買有加拿大電話號碼的 eSIM 或有當地門號的 SIM 卡。有當地號碼的好處：\n1. 導航可以用（山區訊號較穩）\n2. 萬一租車公司聯絡你\n3. 緊急時可撥打當地電話\n推薦：Airalo / 淘寶加拿大eSIM / 中華電信輕量漫遊"),
    (['幫助', 'help', '可以問', '功能', '指令', '怎麼用', 'hi', '嗨', '哈囉', '你好', 'hello'], show_help),
]


def answer(question):
    q = question.strip()
    if not q:
        return show_help()
    q_lower = q.lower()

    # Exact keyword match
    for keywords, handler in KW_MAP:
        for kw in keywords:
            if kw.lower() in q_lower:
                return handler()

    # Fuzzy: "第X天" pattern
    if '天' in q and re.search(r'\d+', q):
        nums = re.findall(r'\d+', q)
        if nums:
            d = int(nums[0])
            if 1 <= d <= 11:
                return show_day(d)

    return (
        f'抱歉，我不太確定你在問什麼 🤔\n\n'
        f'試試看：\n'
        f'  • 「第3天去哪裡？」\n'
        f'  • 「要帶什麼？」\n'
        f'  • 「租車」\n'
        f'  • 「全部行程」\n'
        f'  • 「幫助」看所有功能'
    )


def main():
    print("=" * 60)
    print("🇨🇦  加拿大旅行問答小幫手")
    print(f"📅  {DATA['trip']['name']}  ({DATA['trip']['dates']})")
    print("=" * 60)
    print("輸入問題，或輸入「幫助」看所有功能")
    print("輸入 exit / quit 離開")
    print()

    while True:
        try:
            q = input("🧑 你的問題 > ").strip()
            if not q:
                continue
            if q.lower() in ('exit', 'quit', 'q', '離開'):
                print("👋 旅途愉快！一路平安 🍁")
                break
            print()
            print(answer(q))
            print()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 旅途愉快！")
            break
        except Exception as e:
            print(f"❌ 錯誤：{e}")


if __name__ == '__main__':
    main()
