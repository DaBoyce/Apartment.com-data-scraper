import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import os

priceMaximum = 1900
squareFootageMinimum = 400

def extract_unit_data(unit_container):
    # Extract apartment price
    apartment_price = unit_container.find('div', class_='pricingColumn').find('span', class_="").text.strip()

    try:
        apartment_price = int(apartment_price.replace('$', '').replace(',', ''))
    except ValueError:
        apartment_price = "Call for Rent"

    # Extract square footage
    square_footage = unit_container.find('div', class_='sqftColumn').find('span', class_=None).text.strip()
    square_footage = int(square_footage.replace('$', '').replace(',', ''))

    # Extract availability
    date_available_element = unit_container.find('span', class_='dateAvailable')
    if date_available_element:
        available_from = ''.join([x for x in date_available_element.contents if not hasattr(x, 'attrs') or 'screenReaderOnly' not in x.attrs.get('class', [])]).strip()
        if not available_from:
            available_from = "Not found"
    else:
        available_from = "Not found"

    # Replace "Now" with today's date
    if available_from.lower() == "now":
        available_from = datetime.datetime.now().strftime("%B %d")

    return apartment_price, square_footage, available_from



def extract_property_name(soup):
    property_name_element = soup.find('div', class_='propertyName')
    if property_name_element:
        property_name = property_name_element.text.replace("media gallery", "").replace("\n Unit", "").strip().replace('\n', ' ')
        return property_name
    else:
        return "Not found"


def scrape_url(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive"
    }


    try:
        response = requests.get(url, headers=headers, timeout=60)
    except requests.exceptions.RequestException as e:
        print(f"RequestException occurred for {url}. Skipping...\nError: {e}")
        return
    
    unit_data = []    

    soup = BeautifulSoup(response.text, 'html.parser')

    property_name = extract_property_name(soup)
    
    unit_containers = soup.find_all('div', class_='grid-container js-unitExtension')

    for unit_container in unit_containers:
        apartment_price, square_footage, available_from = extract_unit_data(unit_container)
        unit_data.append({
            'Property Name': property_name,
            'Link': url,
            'Apartment Price': apartment_price,
            'Square Footage': square_footage,
            'Available From': available_from
        })

    return unit_data

def extract_apartment_urls(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive"
    }

    try:
        response = requests.get(url, headers=headers, timeout=60)
    except requests.exceptions.RequestException as e:
                print(f"RequestException occurred for {url}. Skipping...\nError: {e}")
                return

    soup = BeautifulSoup(response.text, "html.parser")
    url_array = []

    for mortar_wrapper in soup.find_all("li", class_="mortar-wrapper"):
        property_link = mortar_wrapper.find("a", class_="property-link")
        if property_link:
            url = property_link["href"]
            url_array.append(url)

    return url_array

############################ MAIN #################################

url = "https://www.apartments.com/apartments/under-1900-pet-friendly-cat/air-conditioning-washer-dryer/?sk=81cd9227fa151a155ac5e6500d2a0eda&bb=l0ught9p4H_0vvq8P&so=2&mid=20230701"
url_array = extract_apartment_urls(url)

all_unit_data = []

for apartment in url_array:
    unit_data = scrape_url(apartment)

    for data in unit_data:
        if data['Apartment Price'] != "Call for Rent":
            if data['Apartment Price'] <= priceMaximum and data['Square Footage'] >= squareFootageMinimum:
                all_unit_data.append(data)

new_df = pd.DataFrame(all_unit_data)
output_filename = "apartment_data.xlsx"

# Check if the file exists
if os.path.isfile(output_filename):
    # Read the existing file
    existing_df = pd.read_excel(output_filename)

    # Append new data to the existing DataFrame only if there is no duplicate
    for _, row in new_df.iterrows():
        duplicate_entry = existing_df[
            (existing_df['Property Name'] == row['Property Name']) &
            (existing_df['Apartment Price'] == row['Apartment Price']) &
            (existing_df['Square Footage'] == row['Square Footage'])
        ]

        if duplicate_entry.empty:
            existing_df = existing_df.append(row, ignore_index=True)

    combined_df = existing_df
else:
    # If the file doesn't exist, create a new DataFrame
    combined_df = new_df

# Save the combined data to the Excel file
combined_df.to_excel(output_filename, index=False)

