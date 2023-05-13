
import requests
import math
from bs4 import BeautifulSoup
import pandas as pd


# In[2]:


### URLS
BASE_URL = "https://www.willhaben.at"
BASE_FILTER = "/iad/immobilien/haus-kaufen/oberoesterreich/"
START_PAGE = 1
ROWS = 5
DESTRICTS = ["braunau-am-inn", "eferding", "freistadt", "gmunden", "grieskirchen",
            "kirchdorf-an-der-krems", "linz", "linz-land", "perg", "ried-im-innkreis",
            "rohrbach", "schaerding", "steyr", "steyr-land", "urfahr-umgebung", "voecklabruck",
            "wels", "wels-land"]


# In[3]:


def GetPages(soup):
    pageCount = soup.find("h1", id="result-list-title").text.split(" ")[0]
    pages = math.ceil(int(pageCount)/ROWS)
    return pages


# In[4]:


def GetLinksFromPage(soup):
    items = []
    #search-result-entry-header
    allElements = soup.find_all("a", id=lambda x: x and x.startswith('search-result-entry-header'), href=True)
    for element in allElements:
        items.append(element.get("href"))
        
    return items


# In[5]:


def GetElementDescriptionFromLink(soup):
    row = {}
    priceElement = soup.select('span[data-testid="contact-box-price-box-price-value-0"]')
    price = int(priceElement[0].text.replace("€ ", "").replace(".", "")) if priceElement != [] else "N/A"
    addressElement = soup.select("div[data-testid='object-location-address']")
    adress = addressElement[0].text
    row.update([("Preis", price), ("Adresse", adress)])
    
    ###Read the property lists
    propLists = soup.find_all("ul", class_="PropertyList-sc-e2zq14-0 cLGcEd")
    for pl in propLists:
        ###Get each element
        propElem = pl.select("li")
        for pe in propElem:
            attribute = pe.select("div[data-testid='attribute-title'] span")[0].text
            value = pe.select("div[data-testid='attribute-value']")[0].text
            #print(attribute + " - " + (value if (value != "") else "vorhanden"))
            row.update({attribute : (value if (value != "") else "vorhanden")})
    for extraInformation in soup.select("div[data-testid^=ad-description]"):
        for li in extraInformation.find_all("li"):
            e = li.text.split(":")
            if len(e) > 1:
                attribute = e[0]
                value = e[1]
                #print(attribute + " - " + (value if (value != "") else "vorhanden"))
                row.update({attribute : (value if (value != "") else "vorhanden")})
                
    
    #print("Preis:" + str(price))
    #print("Adresse: " + adress)
    ### Get object description seperate
    objDescription = soup.select("div[data-testid='ad-description-Objektbeschreibung']")[0].text
    row.update({"Beschreibung" : objDescription})
    return row
    #print("\n"+objDescription)


# In[6]:


def GenerateLinksForDestricts():
    destrictURLS = []
    baseURL = f"{BASE_URL}{BASE_FILTER}"
    for d in DESTRICTS:
        url = f"{baseURL}{d}"
        ### Get max amount of pages for each district
        response = requests.get(url, stream=True)
        html = response.content.decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        pages = GetPages(soup)
        ### Setup all urls with pages parameter
        for i in range(1, pages+1):
            finalURL = f"{url}?page={i}&rows={ROWS}"
            destrictURLS.append(finalURL)
            
    return destrictURLS


# In[7]:


def GetAllPagesLinks(pagesURLS):
    allItems = []
    for link in pagesURLS:
        print(link)
        ### load soup 
        response = requests.get(link, stream=True)
        html = response.content.decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        items = GetLinksFromPage(soup)
        allItems = allItems + items
    
    return allItems


# In[8]:


urls = GenerateLinksForDestricts()
allItems = GetAllPagesLinks(urls)


# In[9]:


def GetSoupElement(url):
    response = requests.get(url, stream=True)
    html = response.content.decode("utf-8")
    return BeautifulSoup(html, "html.parser")


# In[10]:


def GetDetailsFromItems(itemList):
    df = pd.DataFrame()
    
    for item in itemList:
        url = f"{BASE_URL}{item}"
        soup = GetSoupElement(url)
        row = GetElementDescriptionFromLink(soup)
        
        for key in row:
            if key not in df:
                df[key] = ""
        
        df = df.append(row, ignore_index=True)
        
    return df


# In[11]:


dframe = GetDetailsFromItems(allItems)

