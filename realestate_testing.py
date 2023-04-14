from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import time

from matplotlib.ticker import FuncFormatter


base_url = "http://house.speakingsame.com/suburbtop.php?sta=sa&cat=HomePrice&name=&page="

suburb_names = []
prices = []

# Setup Selenium with a headless browser
chrome_options = Options()
chrome_options.add_argument("--headless")

# Supress browser logs
chrome_options.add_argument("--log-level=3")

# Custom user agent to bypass restrictions
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3") 

driver = webdriver.Chrome(options=chrome_options)

for i in range(15):
    url = base_url + str(i)
    driver.get(url)
    
    time.sleep(1) # Wait 1sec in case content has not loaded

    # Use Beautiful Soup to parse the HTML
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Find the tbody element containing data items and populate rows with row elements
    tbody_list = soup.find_all("tbody")
    rows = tbody_list[7].find_all("tr")

    # Loop through the elements in 'rows' excluding the first item
    for row in rows[1:]:
        # Get suburb name from the anchor tag inside the second td element
        suburb_name = row.find_all("td")[1].find("a").text
        suburb_names.append(suburb_name)

        # Get price from the third td element
        price = row.find_all("td")[2].text
        prices.append(price)

# Clean up
driver.quit()


# Create a DataFrame from the suburb_names and prices lists
data = {
    'suburb_name': suburb_names,
    'price': prices
}
df = pd.DataFrame(data)

# Remove dollar sign and commas, and convert to a numeric type
df['price'] = df['price'].str.replace(',', '', regex=False).str.replace('$', '', regex=False).astype(float)

# Print the DataFrame
print(df)

mapcol = 'coolwarm'

# Function to format colorbar tick labels as dollar values
def currency_fmt(x, pos):
    return f"${x:,.0f}"

# Locate the suburb shape file and read it
shapefile_path = 'D:\Local Disk Documents\Suburbs_GDA2020.shp'
gdf = gpd.read_file(shapefile_path)

# Convert suburb names to lowercase in both DataFrames
gdf['suburb'] = gdf['suburb'].str.lower()
df['suburb_name'] = df['suburb_name'].str.lower()

# Merge the data with the GeoDataFrame on the suburb_name column
gdf_merged = gdf.merge(df, left_on='suburb', right_on='suburb_name')

# Read the road shapefile
road_shapefile_path = 'D:\Local Disk Documents\ZIP\MajorRoads.shp'
roads_gdf = gpd.read_file(road_shapefile_path)

# Set up plot
fig, ax = plt.subplots(1, figsize=(12, 12))
ax.set_title('Adelaide Suburb Housing Prices')

# Plot the heatmap using the price column as the value
gdf_merged.plot(column='price', cmap=mapcol, linewidth=0.8, edgecolor='0.8', ax=ax, legend=False)

# Plot the road shapefile on the same axis
roads_gdf.plot(ax=ax, linewidth=0.5, edgecolor='black')

# Add colorbar with dollar values
sm = plt.cm.ScalarMappable(cmap=mapcol, norm=plt.Normalize(vmin=gdf_merged['price'].min(), vmax=gdf_merged['price'].max()))
sm._A = []
cbar = fig.colorbar(sm, format=FuncFormatter(currency_fmt))

plt.show()