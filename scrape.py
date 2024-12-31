import requests
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

# Streamlit UI
st.title("Google Autosuggest Keyword Expander")
seed_keyword = st.text_input("Enter a seed keyword:", "dog training")

if st.button("Generate Keywords"):
    if seed_keyword:
        # Fetch all suggestions
        with st.spinner("Fetching suggestions..."):
            suggestions = fetch_all_suggestions(seed_keyword)
        
        # Display the suggestions
        if suggestions:
            st.write(f"Found {len(suggestions)} unique keywords:")
            st.write(suggestions)
            
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
        else:
            st.write("No suggestions found.")
    else:
        st.warning("Please enter a seed keyword.")
