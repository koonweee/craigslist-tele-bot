import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
from pytz import timezone
class Listing:
    @staticmethod
    def parseDatetime(datetime_str):
        dt = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
        dt = dt.astimezone(timezone('US/Pacific'))
        return int(dt.strftime('%s'))

    def __init__(self, url, img_url, title, datetime_str, price, distance):
        self.url = url
        self.img_url = img_url
        self.title = title
        self.datetime_str = datetime_str
        self.epoch = Listing.parseDatetime(datetime_str)
        self.price = price
        self.distance = distance

    def __str__(self):
        return (
            f'Title: {self.title}\n'
            f'Date time: {self.datetime_str}\n'
            f'Price: {self.price}\n'
            f'Distance: {self.distance}\n'
            f'Image URL: {self.img_url}\n'
            f'URL: {self.url}'
        )

def getTextOfChild(parent, type, search_class, default_value):
    child_ele = parent.find(type, class_=search_class)
    if child_ele:
        return child_ele.getText()
    else:
        return default_value

def getListings(base_url, start="0", latest_epoch=0):
    return_listings = []
    listings_page = requests.get(base_url + f'&s={start}')
    content = listings_page.content
    soup = BeautifulSoup(content, 'html.parser')
    n_total_listings = soup.find('span', class_='totalcount').getText()
    n_page_listings = soup.find('span', class_='rangeTo').getText()
    listings = soup.find_all('li', class_='result-row')
    for listing in listings:
        listing_url = listing.a['href']
        listing_img_ele = listing.find('a', class_='result-image gallery')
        listing_img_url = None
        if listing_img_ele:
            listing_img_data_ids = listing_img_ele["data-ids"]
            if listing_img_data_ids:
                listing_img_data_id = listing_img_data_ids.split(",")[0][2:]
                listing_img_url = f'https://images.craigslist.org/{listing_img_data_id}_300x300.jpg'
        listing_datetime_string = listing.find('time', class_='result-date')['datetime']
        # check if timezone ok
        listing_title = getTextOfChild(listing, "a", "result-title hdrlnk", "Not stated")
        listing_price = getTextOfChild(listing, "span", "result-price", "Not stated")
        listing_distance = getTextOfChild(listing, "span", "maptag", "Not stated")
        listing = Listing(
            listing_url,
            listing_img_url,
            listing_title,
            listing_datetime_string,
            listing_price,
            listing_distance
        )
        if listing.epoch <= latest_epoch: # seen before, terminate early
            return return_listings
        return_listings.append(listing)
    if n_total_listings != n_page_listings: # more pages exist
        return_listings += getListings(base_url, n_page_listings)
    return return_listings
