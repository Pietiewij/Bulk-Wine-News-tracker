import os
import urllib.request
import json
import xml.etree.ElementTree as ET

# Targeted institutional data feeds for raw harvest data
HARVEST_FEEDS = {
    "OIV Press & Statistics": "https://oiv.int",
    "EU Agriculture Wine Portal": "https://europa.eu", 
    "USDA Crop Production Alerts": "https://usda.gov"
}

def fetch_harvest_news():
    collected_data = []
    for source, url in HARVEST_FEEDS.items():
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=15) as response:
                html_or_xml = response.read()
            
            # Simple fallback text aggregation if it's an HTML dashboard or RSS
            if b"<item>" in html_or_xml:
                root = ET.fromstring(html_or_xml)
                for item in root.findall('.//item')[:8]:
                    title = item.find('title').text if item.find('title') is not None else ""
                    desc = item.find('description').text if item.find('description') is not None else ""
                    collected_data.append(f"[{source}] {title}: {desc}")
            else:
                # If it's a web portal page, grab snippets of text safely
                text_content = html_or_xml.decode('utf-8', errors='ignore')[:3000]
                collected_data.append(f"[{source} Raw Dashboard Snippet]:\n{text_content}")
        except Exception as e:
            print(f"Could not read from {source}: {e}")
            
    return "\n\n".join(collected_data)

def analyze_harvest_gaps(raw_text):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY missing from repository secrets."
        
    url = f"https://googleapis.com{api_key}"
    
    prompt = (
        "You are a B2B bulk wine trade strategist helping a broker find arbitrage opportunities. "
        "Analyze the raw agricultural harvest data provided below.\n\n"
        "Your task:\n"
        "1. Identify specific countries or major wine regions where the forecasted or actual harvest volume is significantly LOWER than previous years (indicating a shortage).\n"
        "2. Identify regions with bumper crops/surpluses.\n"
        "3. Explicitly highlight 'SALES OPPORTUNITIES': Match surplus regions with shortage regions where a broker could step in and sell bulk wine.\n\n"
        "Format the output as a clean, highly scannable Markdown report with tables summarizing: "
        "Country | Forecasted Amount | Actual Amount | Status (Shortage/Surplus) | Trade Recommendation.\n\n"
        f"Raw Data:\n{raw_text}"
    )
    
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    req = urllib.request.Request(url, method="POST")
    req.add_header("Content-Type", "application/json")
    
    try:
        with urllib.request.urlopen(req, data=json.dumps(data).encode("utf-8")) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return res_data['candidates']['content']['parts']['text']
    except Exception as e:
        return f"Arbitrage analysis failed: {e}"

if __name__ == "__main__":
    print("Collecting global harvest yield reports...")
    raw_harvest_text = fetch_harvest_news()
    
    print("Analyzing regional supply shortages with AI...")
    harvest_report = analyze_harvest_gaps(raw_harvest_text)
    
    with open("harvest_report.md", "w", encoding="utf-8") as f:
        f.write("# 📊 Global Wine Harvest & Shortage Radar\n")
        f.write("*B2B Trading Agent: Spotting regional supply gaps for sales opportunities.*\n\n")
        f.write(harvest_report)
    print("Harvest shortage report saved successfully!")
