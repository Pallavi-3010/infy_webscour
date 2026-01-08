import requests    # brings in the requests library to make HTTP requests (download web pages)
import time   #gives access to time-related functions (we use time.sleep() to pause between requests).
import os  #making directories/files

#imports deque, a double-ended queue. We use it as a simple FIFO queue for URLs to crawl.
from collections import deque

#imports BeautifulSoup, a parser to extract links and text from HTML
from bs4 import BeautifulSoup

#Breaks a URL into parts and Convert relative links into full URLs
from urllib.parse import urljoin, urlparse


# =========================================================
# TASK 7: Fetch page with retry logic
# Objective: Retry fetching a page if it fails temporarily
# =========================================================

#Try to download the page 
#If it succeeds it return page  
#If it fails then print retry message 
#If attempts left then wait 1 sec & retry
#If no attempts left then return None

def fetch_page(url, retries=3):
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(    #Sends an HTTP GET request to the given URL.This is how the crawler downloads a web page.
                url,
                timeout=5,
                headers={"User-Agent": "WebScourCrawler/1.0"}
            )
            if response.status_code == 200:
                return response.text
        except Exception:
            print(f"[Retry {attempt}/{retries}] Failed to fetch: {url}")

        time.sleep(1)  # wait 1 sec before retry

    return None  # failed after retries


# =========================================================
#  Main Crawler Function
# =========================================================
def crawl(seed_url, max_pages):

    # -------------------------------
    # TASK 3: Create pages folder
    # Objective: Store HTML files neatly
    # -------------------------------
    pages_folder = "pages1"
    os.makedirs(pages_folder, exist_ok=True)

    # -------------------------------
    # TASK 5: Same-domain crawling
    # Objective: Crawl only seed domain
    # -------------------------------
    seed_domain = urlparse(seed_url).netloc      #Extract domain for same-domain crawling

    # Queue for crawling
    # The crawler will take URLs from this queue one by one
    queue = deque([seed_url])

    # Visited URLs
    visited = set()

    # Statistics
    duplicate_count = 0
    start_time = time.time()
    queue_expanded = False  #At the start of crawling, we don’t know yet if the queue will expand
    page_number = 1

    # =====================================================
    # Crawling Loop
    # =====================================================
    # crawler runs only while there are URLs to crawl and the page limit is not reached
    while queue and len(visited) < max_pages:
        current_url = queue.popleft()

        # TASK 2: Duplicate detection
        if current_url in visited:
            duplicate_count += 1
            continue

        page_start = time.time()

        html = fetch_page(current_url)
        if html is None:
            continue

        # -------------------------------
        # TASK 1: Save HTML pages
        # -------------------------------
        file_path = os.path.join(pages_folder, f"page_{page_number}.html") #Combines folder + filename 
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html)    #Writes the downloaded HTML content into the file

        #time.time() → current timestamp
        #page_start → timestamp recorded before fetching page
        #Difference = time taken to crawl this page

        page_time = round(time.time() - page_start, 3)
        print(f"Saved: {file_path} | Time: {page_time}s")

        visited.add(current_url)
        page_number += 1

        # -------------------------------
        # Extract links
        # -------------------------------
        soup = BeautifulSoup(html, "html.parser")  #Creates DOM as it transforms HTML document into a structured representation


        for tag in soup.find_all("a", href=True): #finds all anchor tags having href attribute
            link = tag["href"].strip()  #Extracts the value of the href attribute

            # -------------------------------------------
            # TASK 4: Filter useless links
            # -------------------------------------------
            if link.startswith(("mailto:", "javascript:", "#", "tel:")):
                continue

            # Convert relative links to absolute
            link = urljoin(current_url, link)

            # -------------------------------------------
            # TASK 5: Same-domain check
            # -------------------------------------------
            link_domain = urlparse(link).netloc        #gets only the domain part of a URL
            if link_domain != seed_domain:
                continue

            # -------------------------------------------------------------
            # TASK 2: Queue management & duplicate count, unique url count
            # -------------------------------------------------------------
            if link not in visited and link not in queue:
                queue.append(link)
                queue_expanded = True
            else:
                duplicate_count += 1

        time.sleep(0.5)  # crawling delay

    # =====================================================
    # TASK 6: Save visited URLs to file visited1.txt
    # =====================================================
    with open("visited1.txt", "w", encoding="utf-8") as f:
        for url in visited:
            f.write(url + "\n")

    total_time = round(time.time() - start_time, 2) #Measure how long it took to crawl the page

    # =====================================================
    # FINAL SUMMARY OUTPUT 
    # =====================================================
    print("\n--- Crawl Summary ---")
    print(f"Total pages crawled     : {len(visited)}")
    print(f"Total time taken (sec)  : {total_time}")
    print(f"Unique URLs found       : {len(visited)}")
    print(f"Duplicate URLs detected : {duplicate_count}")
    print(f"Final queue size        : {len(queue)}")
    print(f"Queue expanded?         : {'Yes' if queue_expanded else 'No'}")
    print("Visited URLs saved in    : visited1.txt")
    print("HTML pages saved in      : pages1/ folder")


# =========================================================
# Program Execution
# =========================================================
if __name__ == "__main__":
    seed = input("Enter seed URL: ")       #https://www.python.org/
    max_pages = int(input("Enter MAX_PAGES (e.g., 10, 20, 50): "))
    crawl(seed, max_pages)
