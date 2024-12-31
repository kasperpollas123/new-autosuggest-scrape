import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from concurrent.futures import ThreadPoolExecutor
import streamlit as st

# Function to get Google autosuggestions
def get_google_autosuggestions(query):
    url = "https://www.google.com/complete/search"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    params = {
        'q': query,
        'client': 'chrome',
        'hl': 'en'
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()[1]
        else:
            st.error(f"Failed to fetch suggestions for '{query}'. Status code: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"Request failed for '{query}': {e}")
        return []

# Function to fetch all suggestions
def fetch_all_suggestions(seed_keyword):
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    queries = [f"{seed_keyword} {letter}" for letter in alphabet] + [f"{letter} {seed_keyword}" for letter in alphabet]
    all_suggestions = set()
    for query in queries:
        suggestions = get_google_autosuggestions(query)
        all_suggestions.update(suggestions)
    return sorted(all_suggestions)

# Function to scrape SERP for a keyword
def scrape_serp(keyword):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    url = f"https://www.google.com/search?q={keyword}"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            st.error(f"Failed to fetch SERP for '{keyword}'. Status code: {response.status_code}")
            return []
        
        # Debugging: Log the HTML content
        with open("debug.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        
        # Updated CSS selectors for Google search results
        for result in soup.select("div.g")[:10]:  # Limit to first 10 results
            try:
                title = result.select_one("h3").text
                snippet = result.select_one("div.IsZvec").text
                results.append({"Keyword": keyword, "Title": title, "Snippet": snippet})
            except AttributeError:
                continue
        
        return results
    except requests.exceptions.RequestException as e:
        st.error(f"Request failed for '{keyword}': {e}")
        return []

# Streamlit UI
st.title("Google Autosuggest Keyword Expander with SERP Results")
seed_keyword = st.text_input("Enter a seed keyword:", "dog training")

if st.button("Generate Keywords and Scrape SERP"):
    if seed_keyword:
        # Fetch all suggestions
        with st.spinner("Fetching suggestions..."):
            suggestions = fetch_all_suggestions(seed_keyword)
        
        # Output the keywords to a text file
        keywords_file = "keywords.txt"
        with open(keywords_file, "w") as f:
            f.write("\n".join(suggestions))
        
        # Download the keywords file
        with open(keywords_file, "rb") as f:
            st.download_button(
                label="Download Keywords as Text",
                data=f,
                file_name=keywords_file,
                mime="text/plain"
            )
        
        # Proceed to scrape SERP for the first 5 keywords
        st.write("Proceeding to scrape SERP results for the first 5 keywords...")
        suggestions = suggestions[:5]  # Limit to the first 5 keywords
        
        # Scrape SERP for each suggestion using parallel requests
        with st.spinner("Scraping SERP results..."):
            serp_data = []
            with ThreadPoolExecutor(max_workers=5) as executor:  # Process 5 keywords simultaneously
                results = list(executor.map(scrape_serp, suggestions))
                for result in results:
                    serp_data.extend(result)
                    if result:  # Check if result is not empty
                        st.write(f"Scraped {len(result)} results for '{result[0]['Keyword']}'")  # Debugging
                    else:
                        st.write(f"No results found for this keyword.")
                    time.sleep(2)  # Add a delay to avoid detection
        
        # Display the SERP results
        if serp_data:
            st.write(f"Found {len(suggestions)} unique keywords with SERP results:")
            df = pd.DataFrame(serp_data)
            st.write(df)
            
            # Option to download the SERP results as an Excel file
            excel_file = "keywords_with_serp.xlsx"
            df.to_excel(excel_file, index=False)
            with open(excel_file, "rb") as f:
                st.download_button(
                    label="Download SERP Results as Excel",
                    data=f,
                    file_name=excel_file,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.write("No SERP results found.")
    else:
        st.warning("Please enter a seed keyword.")
