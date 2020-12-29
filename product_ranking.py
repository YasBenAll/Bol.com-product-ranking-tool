import sys
import requests
from bs4 import BeautifulSoup
import json 
import pandas as pd
import timeit

def beautifulSoup(url):
    try:
        return BeautifulSoup(requests.get(url).text, "lxml")
    except:
        return "NaN"

def getName(c):
    # Shorten the name to 100 symbols
    try:
        return c[:100]
    except:
        return "NaN"
    
# Function for finding EAN-code for a product
def getEan(soup):
    # Get all product data
    try:
        taxonomy_data = soup.findAll("div", {"data-test": "taxonomy_data"})
        ean = json.loads(taxonomy_data[0].text)['pdpTaxonomyObj']['productInfo'][0]['ean']
        return ean 
    except:
        return "NaN"

# Analyse the ranking of a product    
def analyseRankings(ean, productSoup):
    # Check the first 2 pages 
    try:
        count = 0
        categoryLink = "https://www.bol.com" + productSoup.find(id="option_block_4").select('li')[-1].findAll("a")[0]['href']
        for i in range(1,3):
            categorySoup = BeautifulSoup(requests.get(categoryLink+f'?page={i}').text, "lxml")
            
            # get element that contains products
            categoryProducts = categorySoup.find(id="js_items_content")
            categoryChildren = categoryProducts.findChildren("li", recursive=False)
            
            # check if product is found
            for cc in categoryChildren:
                count += 1
                categoryProductLink = "https://www.bol.com" + cc.find('a')['href']
                categoryProductSoup = BeautifulSoup(requests.get(categoryProductLink).text, "lxml")
                productEan = getEan(categoryProductSoup)
                if productEan == ean :
                    return str(count)
                elif count > 50:
                    return "50+"
        return str(count)
    except:
        return "NaN"

# Generate html of every product page
def generate_urls(start_url):
    # Download the HTML from start_url
    downloaded_html = requests.get(start_url)

    # Download the HTML with BeatifulSoup and create a soup object
    soup = BeautifulSoup(downloaded_html.text, 'lxml')

    # select element next to next button on the page, which is the one second to last element, which specifies the total
    # number of pages
    try:
        pages = int(soup.find(id="js_pagination_control").select('li')[-2].text)
    except:
        pages = 1
    # Generate the html of every product page 
    soups = [beautifulSoup(f'{start_url}?page={element}') for element in range(1,pages+1)]

    return soups

def main(start_url):
    soups = generate_urls(start_url)

    # Generate list of lists with the product name, EAN-codes and page rank for all products
    data = []

    # Loop over all pages
    n=1
    for i in soups:
        start = timeit.default_timer()
        print("Analysing products listed on page ", n, "...")
        n+=1

        li = i.find(id="js_items_content")

        # get all the products of the page
        children = li.findChildren("li", recursive=False)
        for c in children:
            productList = []

            # Get name of the product 
            productPage = c.findAll("a", {"class":"product-title px_list_page_product_click"})[0]
            name = getName(productPage.text)
            productList.append(name)

            # Go to page of productS
            productSoup = beautifulSoup(f'https://www.bol.com{productPage["href"]}')

            # Find EAN-code for product
            ean = getEan(productSoup)
            productList.append(ean)

            # Find product rank for product
            productList.append(analyseRankings(ean, productSoup))

            # Add all features of product to data in
            data.append(productList)

        stop = timeit.default_timer()
        print('Time: ', stop - start, "s")  

    # Export data to a pandas dataframe and export this to an excel file
    df = pd.DataFrame(data,columns=['Product name', 'Ean', 'Rank'])
    df.to_excel("output.xlsx")  

    print("Done!")

if __name__ == "__main__":
    print("Enter start url:")
    start_url = str(input())
    if "https://www.bol.com/nl/w/" in start_url:
        main(start_url)
    else:
        print("Please enter a valid url")