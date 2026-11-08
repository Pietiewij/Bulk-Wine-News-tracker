import os
import urllib.request
import json
import xml.etree.ElementTree as ET

# 1. High-Value Bulk Wine Data Sources (RSS Feeds)
FEEDS = {
    "OIV Wine News": "https://oiv.int",
    "Meininger International": "https://meininger.de",
    "Wine News Italy": "https://winenews.it"
}

def fetch_news():
    collected_articles = []
    
    for source, url in FEEDS.items():
        try:
            # Download the RSS XML feed safely
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()
                
            root = ET.fromstring(xml_data)
            # Find all news items in the RSS feed
            for item in root.findall('.//item')[:5]: # Get the top 5 articles per site
                title = item.find('title').text if item.find('title') is not None else ""
                desc = item.find('description').text if item.find('description') is not None else ""
                collected_articles.append(f"Source: {source}\nTitle: {title}\nSummary: {desc}\n---")
        except Exception as e:
            print(f"Could not fetch {source}: {e}")
            
    return "\n".join(collected_articles)

def ask_gemini(news_text):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "Error: No API key found."
        
    # Endpoint for the free Gemini 2.5 Flash model
    url = f"https://googleapis.com{api_key}"
    
    prompt = (
        "You are an expert bulk wine market analyst. Below is raw news data from the industry. "
        "Filter out consumer noise (like wine reviews or restaurant openings). "
        "Extract only hard production data, harvest volume estimates, climate impacts, shipping costs, and global market price trends. "
        "Create an executive market report in beautiful, clear Markdown. Group insights under 'Production Trends', 'Market Drivers', and 'Price Indicators'.\n\n"
        f"Raw Data:\n{news_text}"
    )
    
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    req = urllib.request.Request(url, method="POST")
    req.add_header("Content-Type", "application/json")
    
    try:
        with urllib.request.urlopen(req, data=json.dumps(data).encode("utf-8")) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return res_data['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"AI Generation failed: {e}"

if __name__ == "__main__":
    print("Fetching wine market feeds...")
    raw_news = fetch_news()
    
    if not raw_news:
        print("No news gathered today.")
    else:
        print("Asking Gemini to generate the report...")
        report = ask_gemini(raw_news)
        
        # Save the report as an index.md file for our website
        with open("index.md", "w", encoding="utf-8") as f:
            f.write("# 🍇 Bulk Wine Market Tracker\n")
            f.write("*Automatically updated daily using free AI agent technology.*\n\n")
            f.write(report)
        print("Report updated successfully!")
