import requests, random, emoji, argparse, os
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta

# ====== Parse arguments ======
parser = argparse.ArgumentParser()
parser.add_argument("--keyword", required=True)
parser.add_argument("--board", required=True)
parser.add_argument("--domain", required=True)
parser.add_argument("--start_date", required=True)
args = parser.parse_args()

keyword = args.keyword
board = args.board
domain = args.domain
start_date = datetime.strptime(args.start_date, "%Y-%m-%d")

rows_per_file = 200
num_pages = 3   # عدد الصفحات المراد scrape

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# ====== Step 1: Scraping Pinterest ======
results = []
for page in range(1, num_pages+1):
    url = f"https://www.pinterest.com/search/pins/?q={keyword}&page={page}"
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    pins = soup.find_all("img", {"src": True})
    for i, pin in enumerate(pins):
        title = pin.get("alt", f"{keyword} idea {i}")
        img = pin["src"]
        results.append({"title": title, "img": img})

print(f"Scraped {len(results)} results.")

# ====== Step 2: Clean & Generate ======
data = []
for i, item in enumerate(results):
    em = random.choice([emoji.emojize(":sparkles:"), emoji.emojize(":fire:"), emoji.emojize(":bulb:"), ""])
    rand_num = random.randint(1, 999)
    final_title = f"{item['title']} {em} {rand_num}"
    scheduled_date = start_date + timedelta(days=i)

    data.append({
        "title": final_title,
        "description": f"{keyword} inspiration {i}",
        "image_url": item["img"],
        "scheduled_date": scheduled_date.strftime("%Y-%m-%d"),
        "keyword": keyword,
        "board": board,
        "domain_link": f"https://{domain}/{keyword.replace(' ','-')}-{i}"
    })

df = pd.DataFrame(data)

# ====== Step 3: Split into CSV chunks ======
os.makedirs("output", exist_ok=True)
chunks = [df[i:i+rows_per_file] for i in range(0, df.shape[0], rows_per_file)]

for idx, chunk in enumerate(chunks):
    filename = f"output/{keyword}_part{idx+1}.csv"
    chunk.to_csv(filename, index=False)
    print(f"💾 Saved {filename}")
