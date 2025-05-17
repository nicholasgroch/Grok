import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from io import BytesIO

def scrape_property_capsule(company):
    base_url = f"https://properties.propertycapsule.com/{company.lower()}/"
    response = requests.get(base_url)
    if response.status_code != 200:
        return f"Could not access the Property Capsule page for {company}.", None

    soup = BeautifulSoup(response.text, 'html.parser')
    property_links = [a['href'] for a in soup.find_all('a', href=True) if '/p/' in a['href']]
    property_links = list(set(property_links))

    data = []
    for link in property_links:
        full_url = link if link.startswith("http") else f"https:{link}"
        prop_resp = requests.get(full_url)
        if prop_resp.status_code != 200:
            continue

        prop_soup = BeautifulSoup(prop_resp.text, 'html.parser')
        property_name = prop_soup.find('h1')
        property_name = property_name.text.strip() if property_name else "Unnamed Property"

        suite_info = prop_soup.find_all('div', class_='suite')
        for suite in suite_info:
            if 'available' in suite.text.lower() or 'coming' in suite.text.lower():
                size_match = re.search(r'\d{3,5}\s?sq\s?ft', suite.text, re.IGNORECASE)
                size = size_match.group(0) if size_match else "N/A"
                suite_number = suite.find('span', class_='suite-number')
                suite_number = suite_number.text.strip() if suite_number else "Unknown"

                status = "Coming Soon" if 'coming' in suite.text.lower() else "Available"

                data.append({
                    "Property": property_name,
                    "Suite": suite_number,
                    "Size": size,
                    "Status": status,
                    "URL": full_url
                })

    df = pd.DataFrame(data)
    return None, df

st.title("Property Capsule Vacancy Scraper")
st.markdown("Enter the Property Capsule company name (e.g., `kimco`, `brixmor`) to extract available and coming soon leasing data.")

company = st.text_input("Company Slug (from URL)", "")

if st.button("Scrape Leasing Data", key="scrape_button"):
    if company:
        with st.spinner("Scraping... please wait."):
            error, df = scrape_property_capsule(company)

        if error:
            st.error(error)
        elif df is not None and not df.empty:
            st.success(f"Found {len(df)} vacant or coming soon spaces.")
            st.dataframe(df)

            output = BytesIO()
            df.to_excel(output, index=False, engine='openpyxl')
            output.seek(0)
            st.download_button(
                label="Download Excel File",
                data=output,
                file_name=f"{company}_vacancies.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("No vacancy data found.")
    else:
        st.warning("Please enter a company name.")