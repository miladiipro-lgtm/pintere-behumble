import requests
import random
import emoji
import argparse
import os
import sys
import logging
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
from urllib.parse import quote_plus

# ====== Setup logging ======
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pinterest_scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def validate_date(date_string):
    """Validate and parse date string."""
    try:
        return datetime.strptime(date_string, "%Y-%m-%d")
    except ValueError:
        logger.error(f"Invalid date format: {date_string}. Please use YYYY-MM-DD format.")
        sys.exit(1)

def create_output_directory():
    """Create output directory safely."""
    try:
        os.makedirs("output", exist_ok=True)
        logger.info("Output directory created/verified successfully")
    except Exception as e:
        logger.error(f"Failed to create output directory: {e}")
        sys.exit(1)

def get_pinterest_pins(keyword, num_pages, headers):
    """Scrape Pinterest pins with error handling."""
    results = []
    
    for page in range(1, num_pages + 1):
        try:
            # URL encode the keyword properly
            encoded_keyword = quote_plus(keyword)
            url = f"https://www.pinterest.com/search/pins/?q={encoded_keyword}&page={page}"
            
            logger.info(f"Scraping page {page} for keyword: {keyword}")
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()  # Raise exception for bad status codes
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Look for pins in multiple possible selectors
            pins = soup.find_all("img", {"src": True})
            
            if not pins:
                logger.warning(f"No pins found on page {page}")
                continue
                
            page_results = []
            for i, pin in enumerate(pins):
                try:
                    title = pin.get("alt", f"{keyword} idea {i}")
                    img_src = pin.get("src", "")
                    
                    # Filter out non-image URLs and validate image URLs
                    if img_src and (img_src.startswith("http") or img_src.startswith("//")):
                        page_results.append({
                            "title": title.strip() if title else f"{keyword} idea {i}",
                            "img": img_src
                        })
                except Exception as e:
                    logger.warning(f"Error processing pin {i} on page {page}: {e}")
                    continue
            
            results.extend(page_results)
            logger.info(f"Successfully scraped {len(page_results)} pins from page {page}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error on page {page}: {e}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error on page {page}: {e}")
            continue
    
    return results

def process_data(results, keyword, board, domain, start_date):
    """Process scraped data with error handling."""
    if not results:
        logger.error("No results to process")
        return None
    
    data = []
    emojis = [emoji.emojize(":sparkles:"), emoji.emojize(":fire:"), emoji.emojize(":bulb:"), ""]
    
    for i, item in enumerate(results):
        try:
            em = random.choice(emojis)
            rand_num = random.randint(1, 999)
            final_title = f"{item['title']} {em} {rand_num}"
            scheduled_date = start_date + timedelta(days=i)
            
            # Clean and validate the keyword for URL
            clean_keyword = keyword.replace(' ', '-').replace('&', 'and').replace('+', 'plus')
            
            data.append({
                "title": final_title,
                "description": f"{keyword} inspiration {i+1}",
                "image_url": item["img"],
                "scheduled_date": scheduled_date.strftime("%Y-%m-%d"),
                "keyword": keyword,
                "board": board,
                "domain_link": f"https://{domain}/{clean_keyword}-{i+1}"
            })
        except Exception as e:
            logger.warning(f"Error processing item {i}: {e}")
            continue
    
    return data

def save_csv_chunks(df, keyword, rows_per_file):
    """Save data to CSV chunks with error handling."""
    try:
        chunks = [df[i:i+rows_per_file] for i in range(0, df.shape[0], rows_per_file)]
        
        for idx, chunk in enumerate(chunks):
            filename = f"output/{keyword.replace(' ', '_')}_part{idx+1}.csv"
            chunk.to_csv(filename, index=False, encoding='utf-8')
            logger.info(f"💾 Saved {filename} with {len(chunk)} rows")
            
        return len(chunks)
    except Exception as e:
        logger.error(f"Error saving CSV files: {e}")
        return 0

def main():
    """Main function with comprehensive error handling."""
    try:
        # ====== Parse arguments ======
        parser = argparse.ArgumentParser(description="Pinterest Scraper with enhanced error handling")
        parser.add_argument("--keyword", required=True, help="Search keyword for Pinterest")
        parser.add_argument("--board", required=True, help="Board name for categorization")
        parser.add_argument("--domain", required=True, help="Domain for generated links")
        parser.add_argument("--start_date", required=True, help="Start date in YYYY-MM-DD format")
        parser.add_argument("--pages", type=int, default=3, help="Number of pages to scrape (default: 3)")
        parser.add_argument("--rows_per_file", type=int, default=200, help="Rows per CSV file (default: 200)")
        
        args = parser.parse_args()
        
        # Validate inputs
        keyword = args.keyword.strip()
        board = args.board.strip()
        domain = args.domain.strip()
        start_date = validate_date(args.start_date)
        num_pages = max(1, min(args.pages, 10))  # Limit pages to 1-10
        rows_per_file = max(50, min(args.rows_per_file, 1000))  # Limit rows to 50-1000
        
        logger.info(f"Starting Pinterest scraper with keyword: {keyword}")
        logger.info(f"Target board: {board}, Domain: {domain}")
        logger.info(f"Start date: {start_date.strftime('%Y-%m-%d')}")
        logger.info(f"Pages to scrape: {num_pages}, Rows per file: {rows_per_file}")
        
        # Create output directory
        create_output_directory()
        
        # ====== Step 1: Scraping Pinterest ======
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        results = get_pinterest_pins(keyword, num_pages, headers)
        
        if not results:
            logger.error("No pins were scraped. Exiting.")
            sys.exit(1)
        
        logger.info(f"Successfully scraped {len(results)} pins from Pinterest")
        
        # ====== Step 2: Clean & Generate ======
        data = process_data(results, keyword, board, domain, start_date)
        
        if not data:
            logger.error("No data to process. Exiting.")
            sys.exit(1)
        
        df = pd.DataFrame(data)
        logger.info(f"Processed {len(df)} data entries")
        
        # ====== Step 3: Split into CSV chunks ======
        num_files = save_csv_chunks(df, keyword, rows_per_file)
        
        if num_files > 0:
            logger.info(f"✅ Successfully completed! Created {num_files} CSV files in output/ directory")
        else:
            logger.error("Failed to save CSV files")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error in main function: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

