import os
import click
from tinydb import TinyDB, Query
from pathlib import Path
import requests
from parsel import Selector
import operator
import hashlib
import validators

DB_LOCATION = "/src/data.json"

max_downloaded_bytes = 0
downloaded_bytes = 0
max_deep_level = 0
order = 0

allowed_mime_types = {
  'text/html': '.html',
  'text/xhtml': '.html',
  'application/msword': '.doc',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
  'application/pdf': '.pdf',
  'application/vnd.oasis.opendocument.text': '.odt',
  'text/csv': '.csv',
  'text/calendar': '.ics',
  'application/json': '.json',
  'application/vnd.oasis.opendocument.spreadsheet': '.ods',
  '	application/xhtml+xml': '.xhtml',
  'application/vnd.ms-excel': '.xls',
  'application/xml': '.xml',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.template': '.xltx',
  'text/richtext': '.rtx',
  'text/plain': '.txt',
  'text/yaml': '.yaml',
}

@click.command()
@click.option('--gigabytes', default=2, help='Max number og gigabytes to be downloaded.')
@click.option('--url', default="http://www.costafresh.co.cr/", help='Page url to be crawled.')
@click.option('--levels', default=20, help='Maximum deeper level to be reach while crawling.')
@click.option('--restart', default=False, type=bool,  help='Restart the crawling process.')


def main(gigabytes, url, levels, restart):
    global max_downloaded_bytes
    global max_deep_level
    max_downloaded_bytes = gigabytes * 1000000000
    max_deep_level = levels

    """Simple program that craws web pagessss."""
    db = TinyDB(DB_LOCATION)
    if restart:
        print("Starting a new site crawling...")
        os.remove(DB_LOCATION)
        Path(DB_LOCATION).touch()
        db = TinyDB(DB_LOCATION)

        hash = hashlib.md5(url.encode())
        db.insert({'hash':hash.hexdigest(), 'url': url, 'downloaded': False, 'omit':False, 'deep':1, 'order':1, 'size':0, 'mime':''})
    else:
        print("Continuing site crawling...")

    update_downloaded(db)
    verify_preconditions(db)

def update_downloaded(db):
    global downloaded_bytes
    doc = Query()
    docs = db.search(doc.downloaded == True)
    for d in docs:
        downloaded_bytes += d['size']

def verify_preconditions(db):
    global order
    order = 0

    doc = Query()
    pending = db.search((doc.downloaded == False) & (doc.omit == False))
    if len(pending) != 0:
        pending = sorted(pending, key = lambda i: (i['deep'], i['order']))
        next = pending[0]

        doc = Query()
        next_docs = db.search((doc.downloaded == False) & (doc.omit == False) & (doc.deep == (next['deep'] + 1)))
        if len(next_docs) != 0:
            next_docs = sorted(next_docs, key=lambda k: k['order'], reverse=True)
            last = next_docs[0]
            order = last['order']

        if downloaded_bytes > max_downloaded_bytes or next['deep'] > max_deep_level:
            export(db)
        else:
            craw(db, next)
    else:
        print ('No more documents to search')

def craw(db, next):
    print("--------Getting url {}".format(next['url']))

    try:
        response = requests.get(next['url'])
        print("Response status {}".format(response.status_code))
        if response.status_code != 200:
            omit(db, next)
            return

        content = response.headers['content-type'].split(";")
        if len(content) == 0:
            omit(db, next)
            return

        mime = content[0]
        print("Mime type {}".format(mime))
        if mime not in allowed_mime_types:
            omit(db, next)
            return

        save(db, next, response, mime)
        update_urls(db, next, response)
        verify_preconditions(db)
    except ConnectionError:
        omit(db,next)

def update_urls(db, next, response):
    global order

    selector = Selector(response.text)
    href_links = selector.xpath('//a/@href').getall()

    for l in href_links:
        if not validators.url(l):
          continue
        hash = hashlib.md5(l.encode())
        digest = hash.hexdigest()

        doc = Query()
        process = db.search(doc.hash == digest)
        if len(process) != 0:
            continue
        else:
            order += 1
            db.insert({'hash': digest, 'url': str(l), 'downloaded': False, 'omit': False, 'deep': next['deep'] + 1, 'order': order, 'size': 0,'mime': ''})

def save(db, next, response, mime):
    global downloaded_bytes
    file_name = "/src/data/{}{}".format(next["hash"], allowed_mime_types[mime])
    print("Saving to {}".format(file_name))

    file = open(file_name, 'w')
    file.write(response.text)
    file.close()

    stats = os.stat(file_name)
    dowloaded = stats.st_size
    downloaded_bytes += dowloaded

    print("Downloaded {} new bytes, total {} of {}".format(dowloaded, downloaded_bytes, max_downloaded_bytes))

    doc = Query()
    db.update({'omit': False, 'downloaded': True, 'mime': mime, 'size':dowloaded}, doc.url == next['url'])

    return

def omit(db, next):
    print("Omitting url {}".format(next['url']))
    doc = Query()
    db.update({'omit': True}, doc.url == next['url'])
    verify_preconditions(db)
    return

def export(db):
    return

if __name__ == "__main__":
    main()

