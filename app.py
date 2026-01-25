import streamlit as st
import requests

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Ads.txt Availability Checker",
    layout="centered"
)

def format_url(input_domain):
    """
    Cleans the input to extract just the domain (e.g., 'https://cnn.com/page' -> 'cnn.com').
    """
    # Remove protocol
    clean = input_domain.replace("https://", "").replace("http://", "")
    # Remove path
    clean = clean.split("/")[0]
    return clean

def check_file_status(domain, filename):
    """
    Checks if the file exists and returns status code and line count.
    """
    target_url = f"https://{domain}/{filename}"
    
    try:
        # User-Agent is important because some firewalls block python-requests
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(target_url, headers=headers, timeout=5)
        
        # Check for successful response
        if response.status_code == 200:
            # Check if content is actually text (sometimes 200 returns HTML 404 page)
            if "<html" in response.text.lower() or "<body" in response.text.lower():
                 return {
                    "exists": False,
                    "code": 200,
                    "message": "Soft 404 (HTML content detected instead of text)",
                    "lines": 0
                }

            line_count = len(response.text.strip().split('\n'))
            return {
                "exists": True,
                "code": 200,
                "message": "File found",
                "lines": line_count
            }
        else:
            return {
                "exists": False,
                "code": response.status_code,
                "message": "HTTP Error",
                "lines": 0
            }
            
    except requests.exceptions.Timeout:
        return {"exists": False, "code": 408, "message": "Connection Timed Out", "lines": 0}
    except requests.exceptions.ConnectionError:
        return {"exists": False, "code": 0, "message": "DNS/Connection Error", "lines": 0}
    except Exception as e:
        return {"exists": False, "code": 500, "message": str(e), "lines": 0}

# --- UI LAYOUT ---

st.title("Ads.txt Availability Checker")
st.markdown("Check if a domain hosts valid `ads.txt` or `app-ads.txt` files and retrieve file statistics.")

# Input Section
domain_input = st.text_input("Enter Domain", placeholder="example.com")

# The Switch
file_type = st.radio(
    "Select File to Check:",
    ("ads.txt", "app-ads.txt"),
    horizontal=True
)

# Action
if st.button("Check Availability"):
    if not domain_input:
        st.warning("Please enter a domain.")
    else:
        domain = format_url(domain_input)
        
        with st.spinner(f"Pinging {domain}/{file_type}..."):
            result = check_file_status(domain, file_type)
        
        # Output Section
        st.divider()
        st.subheader("Result")

        col1, col2, col3 = st.columns(3)
        
        # Display Status Code
        with col1:
            st.metric("HTTP Status", result["code"])
        
        # Display Status Message
        with col2:
            st.metric("Status", "Available" if result["exists"] else "Missing")

        # Display Line Count (only if found)
        with col3:
            if result["exists"]:
                st.metric("Line Count", result["lines"])
            else:
                st.metric("Line Count", "-")

        # Detailed Message
        if result["exists"]:
            st.success(f"Success: {file_type} is present on {domain}. Found {result['lines']} records.")
        else:
            st.error(f"Failed: {result['message']}. Server returned code {result['code']}.")
