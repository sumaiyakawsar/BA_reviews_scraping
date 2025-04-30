# Web scraping and analysis
# This Jupyter notebook includes some code to get you started with web scraping. We will use a package called BeautifulSoup to collect the data from the web. Once you've collected your data and saved it into a local .csv file you should start with your analysis.
#
# Scraping data from Skytrax
# If you visit [https://www.airlinequality.com] you can see that there is a lot of data there. For this task, we are only interested in reviews related to British Airways and the Airline itself.
#
# If you navigate to this link: [https://www.airlinequality.com/airline-reviews/british-airways] you will see this data. Now, we can use Python and BeautifulSoup to collect all the links to the reviews and then to collect the text data on each of the individual review links.
#

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
# Set up headers to mimic Chrome
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
}

base_url = "https://www.airlinequality.com/airline-reviews/british-airways"
# pages = 40

def clean_text(text):
    # Remove non-ASCII characters
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    # Normalize fancy quotes
    text = text.replace('“', '"').replace('”', '"').replace("‘", "'").replace("’", "'")
    # Replace multiple spaces/tabs/newlines with a single space
    text = re.sub(r'\s+', ' ', text)
    # Strip surrounding quotes and spaces
    text = text.strip('"').strip("'").strip()
    return text

def extract_review_details(review):
    details = {}
    table = review.find("table", class_="review-ratings")
    if table:
        rows = table.find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) == 2:
                key = cols[0].get_text(strip=True)

                # Check if the second column contains star-rating spans
                star_spans = cols[1].find_all("span", class_="star")
                if star_spans:
                    # Count how many spans have class 'fill' to determine rating
                    rating = sum("fill" in star.get("class", []) for star in star_spans)
                    details[key] = rating
                else:
                    # Just use the text value if not a star rating
                    value = cols[1].get_text(strip=True)
                    details[key] = value
    return details


# --- Function to parse a single review block
def parse_single_review(review):
    try:
        title = review.find("h2", class_="text_header").text.strip()
        title = clean_text(title)
    except:
        title = ""

    try:
        rating_tag = review.find("div", class_="rating-10").text
        rating = rating_tag if rating_tag else None
    except:
        rating = None

    try:
        content = review.find("div", class_="text_content").text.strip()
        content = content.replace("✅", "").replace("❌", "")
    except:
        content = ""

    try:
        author = review.find("h3", class_="userStatusWrapper").text.strip()
        author = clean_text(author)
    except:
        author = ""

    try:
        date = review.find("time")["datetime"]
    except:
        date = ""

    try:
        trip_verified = "Yes" if "Trip Verified" in content else "No"
    except:
        trip_verified = "No"

    # Extract additional fields from details table
    additional_details = extract_review_details(review)

    # Build full review record
    review_data = {
        "Date": date,
        "Author": author,
        "Title": title,
        "Rating": rating,
        "Trip Verified": trip_verified,
        "Review": content
    }

    review_data.update(additional_details)  # Merge additional fields
    return review_data


def parse_page(page_num):
    url = f"{base_url}/page/{page_num}/?sortby=post_date%3ADesc&pagesize=100"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    reviews = soup.find_all("article", class_="comp_media-review-rated")

    page_reviews = [parse_single_review(review) for review in reviews]
    print(f"Page {page_num}: {len(page_reviews)} reviews found.")

    return page_reviews

# --- Main script to loop through pages
def scrape_all_reviews(pages=40):
    all_reviews = []
    for page in range(1, pages + 1):
        print(f"Scraping page {page}...")
        try:
            page_data = parse_page(page)
            all_reviews.extend(page_data)
        except Exception as e:
            print(f"Error on page {page}: {e}")
        time.sleep(2)  # Polite delay


    return pd.DataFrame(all_reviews)


# --- Run the scraper
if __name__ == "__main__":
    df = scrape_all_reviews(pages=40)
    filename ="british_airways_detailed_reviews.csv"
    df.to_csv(filename, index=False)
    print(f"✅ Scraping complete. Data saved to {filename}")

## Congratulations! Now you have your dataset for this task! The loops above collected 1000 reviews by iterating through the paginated pages on the website. However, if you want to collect more data, try increasing the number of pages!
# The next thing that you should do is clean this data to remove any unnecessary text from each of the rows. For example, "✅ Trip Verified" can be removed from each row if it exists, as it's not relevant to what we want to investigate.