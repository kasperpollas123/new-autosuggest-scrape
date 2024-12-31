import requests
import streamlit as st
import time
import json

# Zyte API Credentials
ZYTE_API_URL = "https://api.zyte.com/v1/extract"
ZYTE_API_KEY = "a5615680ab7647bbb06769b5568dc218"  # Your Zyte API key

# Function to get Google autosuggestions using Zyte API
def get_google_autosuggestions(query):
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Basic {ZYTE_API_KEY}"  # Add API key to headers
    }
    payload = {
        "url": f"https://www.google.com/complete/search?q={query}&client=chrome&hl=en",
        "browserHtml": True  # Request the rendered HTML of the page
    }
    try:
        response = requests.post(ZYTE_API_URL, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Parse the HTML to extract autosuggestions
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(data["browserHtml"], "html.parser")
            suggestions = [suggestion.text for suggestion in soup.select("div.sbqs_c")]
            return suggestions
        elif response.status_code == 403:
            st.warning(f"Rate limit hit for '{query}'. Retrying...")
            time.sleep(5)  # Pause before retrying
            return get_google_autosuggestions(query)  # Retry the request
        else:
            st.error(f"Failed to fetch suggestions for '{query}'. Status code: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"Request failed for '{query}': {e}")
        return []

# Function to fetch suggestions for a seed keyword
def fetch_suggestions_for_seed(seed_keyword, append_letters=True):
    if append_letters:
        alphabet = 'abcdefghijklmnopqrstuvwxyz'
        queries = [f"{seed_keyword} {letter}" for letter in alphabet] + [f"{letter} {seed_keyword}" for letter in alphabet]
    else:
        queries = [seed_keyword]
    
    suggestions = set()
    for query in queries:
        results = get_google_autosuggestions(query)
        suggestions.update(results)
        time.sleep(2)  # Add a delay between requests to avoid rate limiting
    return sorted(suggestions)

# Recursive function to generate keywords
def generate_keywords(seed_keyword, depth=1, max_depth=2):
    if depth > max_depth:
        return set()
    
    st.write(f"Generating keywords for seed: '{seed_keyword}' (Depth {depth})")
    append_letters = (depth == 1)  # Only append letters at depth 1
    suggestions = fetch_suggestions_for_seed(seed_keyword, append_letters)
    all_suggestions = set(suggestions)
    
    for suggestion in suggestions:
        all_suggestions.update(generate_keywords(suggestion, depth + 1, max_depth))
    
    return all_suggestions

# Streamlit UI
st.title("Google Autosuggest Keyword Expander")
seed_keyword = st.text_input("Enter a seed keyword:", "dog training")
max_depth = st.number_input("Enter the maximum recursion depth:", min_value=1, max_value=5, value=2)

if st.button("Generate Keywords"):
    if seed_keyword:
        # Generate keywords recursively
        with st.spinner("Fetching suggestions..."):
            all_suggestions = generate_keywords(seed_keyword, max_depth=max_depth)
        
        # Display the suggestions
        if all_suggestions:
            st.write(f"Found {len(all_suggestions)} unique keywords:")
            st.write(sorted(all_suggestions))
            
            # Output the keywords to a text file
            keywords_file = "keywords.txt"
            with open(keywords_file, "w") as f:
                f.write("\n".join(sorted(all_suggestions)))
            
            # Download the keywords file
            with open(keywords_file, "rb") as f:
                st.download_button(
                    label="Download Keywords as Text",
                    data=f,
                    file_name=keywords_file,
                    mime="text/plain"
                )
        else:
            st.write("No suggestions found.")
    else:
        st.warning("Please enter a seed keyword.")
