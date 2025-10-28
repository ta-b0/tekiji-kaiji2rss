import requests
from datetime import datetime, timedelta
import csv
import os
from feedgen.feed import FeedGenerator  # RSS生成用

def fetch_data(url):
    response = requests.get(url)
    data = response.json()
    return data['items']

def filter_data(items, keywords):
    return [item['Tdnet'] for item in items if any(keyword in item['Tdnet']['title'] for keyword in keywords)]

def get_market_classification(company_code):
    csv_filename = "data_j.csv"
    if os.path.exists(csv_filename):
        with open(csv_filename, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['コード'] == company_code:
                    return row['市場・商品区分']
                elif row['コード'].startswith(company_code[:4]):  # 上位4桁でマッチング
                    return row['市場・商品区分']
    return None

def format_output(items):
    prime_count = 0
    standard_count = 0
    growth_count = 0
    formatted_output = ""
    rss_items = []

    for count, item in enumerate(items, start=1):
        company_code = item['company_code']
        market_classification = get_market_classification(company_code)
        if not market_classification:
            continue

        formatted_output += f"[{count}]\n"
        formatted_output += f"社名:\t{item['company_name']}\n"
        formatted_output += f"表題:\t{item['title']}\n"
        formatted_output += f"日付:\t{item['pubdate']}\n"

        url = item['document_url'].removeprefix("https://webapi.yanoshin.jp/rd.php?")
        formatted_output += f"URL:\t{url}\n"

        formatted_company_code = company_code[:4]
        if not company_code.endswith("0"):
            formatted_company_code += f"（{company_code[4:]}）"

        formatted_output += f"コード:\t{formatted_company_code}（{market_classification}）"

        yahoo_finance_url = f"https://finance.yahoo.co.jp/quote/{formatted_company_code[:4]}"
        formatted_output += f" {yahoo_finance_url}\n\n"

        # RSSに追加する要素
        rss_items.append({
            "title": f"{item['company_name']} - {item['title']}",
            "link": url,
            "description": f"{item['company_name']}（{market_classification}）が{item['title']}を発表しました。",
            "pubdate": item['pubdate']
        })

        # 内訳集計
        if "プライム" in market_classification:
            prime_count += 1
        elif "スタンダード" in market_classification:
            standard_count += 1
        elif "グロース" in market_classification:
            growth_count += 1

    breakdown_message = f"内訳：プライムが{prime_count}件、スタンダードが{standard_count}件、グロースが{growth_count}件\n"
    return formatted_output.strip(), breakdown_message, rss_items

def generate_rss(rss_items, target_day, breakdown_message):
    fg = FeedGenerator()
    fg.title(f"{target_day.strftime('%m月%d日')}のサイバー攻撃関連適時開示")
    fg.link(href="https://example.com/rss.xml", rel="self")
    fg.description(f"{breakdown_message.strip()}")

    for item in rss_items:
        fe = fg.add_entry()
        fe.title(item["title"])
        fe.link(href=item["link"])
        fe.description(item["description"])
        fe.pubDate(item["pubdate"])

    fg.rss_file("rss.xml")  # RSSファイルを出力

def main():
    today = datetime.now().date()
    target_day = today
    url = "https://webapi.yanoshin.jp/webapi/tdnet/list/" + target_day.strftime("%Y%m%d") + ".json"

    items = fetch_data(url)
    keywords = ["サイバー攻撃", "漏えい", "漏洩", "ランサムウェア", "攻撃", "不正アクセス"]

    filtered_items = filter_data(items, keywords)
    if filtered_items:
        output, breakdown_message, rss_items = format_output(filtered_items)
        print(f"{target_day.strftime('%m月%d日')}は {len(filtered_items)} 件のサイバー攻撃に関する適時開示がありました")
        print(breakdown_message)
        print(output)
        generate_rss(rss_items, target_day, breakdown_message)
        print("✅ RSSフィードを rss.xml に出力しました。")
    else:
        print(f"{target_day.strftime('%m月%d日')}はサイバー攻撃に関する適時開示がありませんでした")

if __name__ == "__main__":
    main()
