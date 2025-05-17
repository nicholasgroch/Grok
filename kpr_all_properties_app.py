import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import BytesIO

def get_all_kpr_property_urls():
    base_url = "https://kprcenters.propertycapsule.com"
    response = requests.get(base_url)
    if response.status_code != 200:
        return f"Could not access {base_url}", []

    soup = BeautifulSoup(response.text, 'html.parser')
    links = [
        "https://kprcenters.propertycapsule.com" + a['href']
        for a in soup.find_all('a', href=True)
        if a['href'].startswith('/p/') and '/commercial-real-estate-listings/' in a['href']
    ]
    return None, list(set(links))

def scrape_kpr_property(url):
    try:
        res = requests.get(url)
        if res.status_code != 200:
            return []

        soup = BeautifulSoup(res.text, 'html.parser')
        name = soup.find('h1').text.strip() if soup.find('h1') else "Unknown Property"
        data = []

        # Look for div-based suite listings
        suite_divs = soup.find_all("div", class_="suite")
        for suite_div in suite_divs:
            txt = suite_div.get_text(" ", strip=True)
            if "available" in txt.lower() or "coming soon" in txt.lower():
                suite_number = suite_div.find("span", class_="suite-number")
                size_tag = suite_div.find("span", class_="suite-size")

                suite = suite_number.text.strip() if suite_number else "Unknown"
                size = size_tag.text.strip() if size_tag else "N/A"
                status = "Coming Soon" if "coming soon" in txt.lower() else "Available"

                data.append({
                    "Property": name,
                    "Suite": suite,
                    "Size": size,
                    "Status": status,
                    "URL": url
                })

        return data
    except:
        return []

st.title("KPR All Properties Scraper (Enhanced)")
st.markdown("Click the button below to scrape all property listings from KPR's Property Capsule site and download a spreadsheet of available and coming soon spaces. Now supports both table and suite-block formats.")

if st.button("Scrape All Properties"):
    with st.spinner("Collecting property URLs..."):
        error, all_urls = get_all_kpr_property_urls()
    if error:
        st.error(error)
    else:
        all_data = []
        with st.spinner("Scraping each property..."):
            for url in all_urls:
                all_data.extend(scrape_kpr_property(url))

        if all_data:
            df = pd.DataFrame(all_data)
            st.success(f"Scraped {len(df)} vacancies across {len(all_urls)} properties.")

            st.dataframe(df)

            output = BytesIO()
            df.to_excel(output, index=False, engine='openpyxl')
            output.seek(0)

            st.download_button(
                label="Download Full Excel Report",
                data=output,
                file_name="kpr_all_properties_vacancies.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("No vacancy data found across properties.")