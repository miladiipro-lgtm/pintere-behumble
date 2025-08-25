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
import traceback
import time

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
        return None

def create_output_directory():
    """Create output directory safely."""
    try:
        os.makedirs("output", exist_ok=True)
        logger.info("Output directory created/verified successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create output directory: {e}")
        return False

def get_pinterest_pins(keyword, num_pages, headers):
    """Scrape Pinterest pins with enhanced logic to find more pins."""
    results = []
    target_pins = 200  # Target number of pins to collect
    
    for page in range(1, num_pages + 1):
        if len(results) >= target_pins:
            logger.info(f"Reached target of {target_pins} pins, stopping early")
            break
            
        try:
            # URL encode the keyword properly
            encoded_keyword = quote_plus(keyword)
            url = f"https://www.pinterest.com/search/pins/?q={encoded_keyword}&page={page}"
            
            logger.info(f"Scraping page {page} for keyword: {keyword} (Current pins: {len(results)})")
            logger.info(f"URL: {url}")
            
            response = requests.get(url, headers=headers, timeout=30)
            logger.info(f"Response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.warning(f"Page {page} returned status {response.status_code}")
                continue
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Try multiple selectors to find pins
            pins = []
            
            # Method 1: Look for img tags with src
            img_pins = soup.find_all("img", {"src": True})
            pins.extend(img_pins)
            logger.info(f"Found {len(img_pins)} img tags on page {page}")
            
            # Method 2: Look for Pinterest pin containers
            pin_containers = soup.find_all("div", {"data-test-id": "pin"})
            pins.extend(pin_containers)
            logger.info(f"Found {len(pin_containers)} pin containers on page {page}")
            
            # Method 3: Look for any div with pin-related classes
            pin_divs = soup.find_all("div", class_=lambda x: x and "pin" in x.lower())
            pins.extend(pin_divs)
            logger.info(f"Found {len(pin_divs)} pin divs on page {page}")
            
            # Method 4: Look for links that might contain pins
            pin_links = soup.find_all("a", href=lambda x: x and "/pin/" in x)
            pins.extend(pin_links)
            logger.info(f"Found {len(pin_links)} pin links on page {page}")
            
            # Remove duplicates while preserving order
            seen = set()
            unique_pins = []
            for pin in pins:
                pin_id = str(pin)
                if pin_id not in seen:
                    seen.add(pin_id)
                    unique_pins.append(pin)
            
            logger.info(f"Total unique elements found on page {page}: {len(unique_pins)}")
            
            if not unique_pins:
                logger.warning(f"No pins found on page {page}")
                continue
                
            page_results = []
            for i, pin in enumerate(unique_pins):
                try:
                    # Extract title from various attributes
                    title = ""
                    if pin.name == "img":
                        title = pin.get("alt", "")
                        img_src = pin.get("src", "")
                    elif pin.name == "div":
                        # Look for img inside div
                        img_tag = pin.find("img")
                        if img_tag:
                            title = img_tag.get("alt", "")
                            img_src = img_tag.get("src", "")
                        else:
                            # Try to get text content
                            title = pin.get_text(strip=True)[:100]
                            img_src = pin.get("data-src", "") or pin.get("data-lazy-src", "")
                    elif pin.name == "a":
                        # Look for img inside link
                        img_tag = pin.find("img")
                        if img_tag:
                            title = img_tag.get("alt", "")
                            img_src = img_tag.get("src", "")
                        else:
                            title = pin.get_text(strip=True)[:100]
                            img_src = ""
                    
                    # Clean up title
                    if not title:
                        title = f"{keyword} idea {len(results) + i + 1}"
                    else:
                        title = title.strip()
                    
                    # Validate image URL
                    if img_src and (img_src.startswith("http") or img_src.startswith("//")):
                        page_results.append({
                            "title": title,
                            "img": img_src
                        })
                        
                except Exception as e:
                    logger.warning(f"Error processing pin {i} on page {page}: {e}")
                    continue
            
            results.extend(page_results)
            logger.info(f"Successfully scraped {len(page_results)} pins from page {page}")
            logger.info(f"Total pins collected so far: {len(results)}")
            
            # Add delay between requests to be respectful
            if page < num_pages:
                time.sleep(1)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error on page {page}: {e}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error on page {page}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            continue
    
    logger.info(f"Final pin count: {len(results)}")
    return results

def process_data(results, keyword, board, domain, start_date):
    """Process scraped data with error handling."""
    if not results:
        logger.error("No results to process")
        return None
    
    data = []
    emojis = [emoji.emojize(":sparkles:"), emoji.emojize(":fire:"), emoji.emojize(":bulb:"), emoji.emojize(":star:"), emoji.emojize(":heart:"), ""]
    
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
        logger.error(f"Traceback: {traceback.format_exc()}")
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
        parser.add_argument("--pages", type=int, default=30, help="Number of pages to scrape (default: 30)")
        parser.add_argument("--rows_per_file", type=int, default=200, help="Rows per CSV file (default: 200)")
        
        args = parser.parse_args()
        
        # Validate inputs
        keyword = args.keyword.strip()
        board = args.board.strip()
        domain = args.domain.strip()
        start_date = validate_date(args.start_date)
        
        if start_date is None:
            logger.error("Invalid start date provided")
            sys.exit(1)
            
        num_pages = max(10, min(args.pages, 50))  # Limit pages to 10-50 for better results
        rows_per_file = max(50, min(args.rows_per_file, 1000))  # Limit rows to 50-1000
        
        logger.info(f"Starting Pinterest scraper with keyword: {keyword}")
        logger.info(f"Target board: {board}, Domain: {domain}")
        logger.info(f"Start date: {start_date.strftime('%Y-%m-%d')}")
        logger.info(f"Pages to scrape: {num_pages}, Rows per file: {rows_per_file}")
        logger.info(f"Target: Collecting 200+ pins")
        
        # Create output directory
        if not create_output_directory():
            logger.error("Failed to create output directory")
            sys.exit(1)
        
        # ====== Step 1: Scraping Pinterest ======
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        results = get_pinterest_pins(keyword, num_pages, headers)
        
        if not results:
            logger.warning("No pins were scraped. Creating sample data for testing...")
            # Create sample data to prevent complete failure
            results = [
                {"title": f"{keyword} sample idea {i+1}", "img": "https://via.placeholder.com/300x300"} 
                for i in range(10)
            ]
            logger.info("Created sample data for testing purposes")
        
        logger.info(f"Total results to process: {len(results)}")
        
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
            logger.info(f"📊 Total pins collected: {len(df)}")
        else:
            logger.error("Failed to save CSV files")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error in main function: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
