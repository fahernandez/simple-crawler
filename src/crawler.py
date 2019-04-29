import os
import click
from tinydb import TinyDB, Query
from pathlib import Path
import requests
from parsel import Selector
from tinydb import where

DB_LOCATION = "/src/data.json"

document_size = 0
deep_level = 0

@click.command()
@click.option('--size', default=2, help='Max number og gigabytes to be downloaded.')
@click.option('--url', default="http://www.costafresh.co.cr/", help='Page url to be crawled.')
@click.option('--levels', default=20, help='Maximum deeper level to be reach while crawling.')
@click.option('--restart', default=True, type=bool,  help='Restart the crawling process.')


def main(size, url, levels, restart):
    global document_size
    global deep_level
    document_size = size
    deep_level = levels

    """Simple program that craws web pagessss."""
    db = TinyDB(DB_LOCATION)
    if restart:
        print("Starting a new site crawling...")
        os.remove(DB_LOCATION)
        Path(DB_LOCATION).touch()
        db = TinyDB(DB_LOCATION)
        db.insert({'url': url, 'downloaded': False, 'deep':1, 'order':1, 'size(MB)':0, 'mime':'text/html'})
    else:
        print("Continuing site crawling...")

    craw(db)

def craw(db):
    page = Query()
    size = db.search(where('size(MB)') != 0)

    # res = db.search(page.downloaded == False)
    # print(res)
    # response = requests.get(url)
    # # "response.txt" contain all web page content
    # selector = Selector(response.text)
    #
    # # Extracting href attribute from anchor tag <a href="*">
    # href_links = selector.xpath('//a/@href').getall()
    # page = Query()
    # for link in href_links:
    #     res = db.Search(page.url == link)
    #     if size(res) == 0:
    #         db.insert({'url': link, 'visited': False, 'deep':1})

if __name__ == "__main__":
    main()