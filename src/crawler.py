import os
import click
from tinydb import TinyDB, Query
from pathlib import Path
import requests
from parsel import Selector
import operator
import validators
import csv

DATA_DB_LOCATION = "/src/data.json"
ADMIN_DB_LOCATION = "/src/admin.json"
URL_LOCATION = "/src/url.txt"
FILE_LOCATION = '/src/data/'

# Local variables
max_bytes_to_download = 0
max_levels = 0

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
    global max_bytes_to_download
    global max_levels
    max_bytes_to_download = gigabytes * 1000000000
    max_levels = levels

    # prune db to improve query time
    """Simple program that craws web pagessss."""

    db = TinyDB(DATA_DB_LOCATION)

    if restart:
        print("Starting a new site crawling...")
        os.remove(DATA_DB_LOCATION)
        Path(DATA_DB_LOCATION).touch()
        os.remove(URL_LOCATION)
        Path(URL_LOCATION).touch()
        os.remove(ADMIN_DB_LOCATION)
        Path(ADMIN_DB_LOCATION).touch()

        db = TinyDB(DATA_DB_LOCATION)
        db.insert({'sequence':0, 'url': url, 'downloaded': False, 'omit':False, 'deep':1, 'order':1, 'size':0, 'mime':''})
    else:
        print("Continuing site crawling...")

    prunedb(db)
    update_admin_fields()
    verify_preconditions(db)

def update_admin_fields():
    db = TinyDB(ADMIN_DB_LOCATION)
    admin = db.search(Query()['admin'] == True)
    if len(admin) == 0:
        db.insert({'admin': True, 'sequence': 0, 'bytes_downloaded': 0, 'order':0})

    admin = db.search(Query()['admin'] == True)[0]
    print("Last downloaded document {}".format(admin['sequence']))
    print("New document order {}".format(admin['order']))
    print("Bytes downloaded {}".format(admin['bytes_downloaded']))

def verify_preconditions(db):
    doc = Query()
    pending = db.search((doc.downloaded == False) & (doc.omit == False))
    if len(pending) != 0:
        next = sorted(pending, key = lambda i: (i['deep'], i['order']))[0]

        doc = Query()
        next_level_docs = db.search((doc.downloaded == False) & (doc.omit == False) & (doc.deep == (next['deep'] + 1)))
        if len(next_level_docs) == 0:
            TinyDB(ADMIN_DB_LOCATION).update({'order': 0}, Query()['admin'] == True)

        admin = TinyDB(ADMIN_DB_LOCATION).search(Query()['admin'] == True)[0]
        if admin['bytes_downloaded'] > max_bytes_to_download or next['deep'] > max_levels:
            prunedb(db)
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
    selector = Selector(response.text)
    href_links = selector.xpath('//a/@href').getall()

    order = TinyDB(ADMIN_DB_LOCATION).search(Query()['admin'] == True)[0]['order']
    for l in href_links:
        if not validators.url(l):
          continue

        doc = Query()
        process = db.search(doc.url == l)
        if len(process) != 0:
            continue
        else:
            order += 1
            db.insert({'sequence':0, 'url': str(l), 'downloaded': False, 'omit': False, 'deep': next['deep'] + 1, 'order': order, 'size': 0,'mime': ''})

    TinyDB(ADMIN_DB_LOCATION).update({'order': order}, Query()['admin'] == True)

def save(db, next, response, mime):
    admin = TinyDB(ADMIN_DB_LOCATION).search(Query()['admin'] == True)[0]
    sequence = admin['sequence']
    bytes_downloaded = admin['bytes_downloaded']

    sequence += 1

    file_name = "{}{}{}".format(FILE_LOCATION,sequence, allowed_mime_types[mime])
    print("Saving to {}".format(file_name))

    file = open(file_name, 'wb')
    file.write(response.content)
    file.close()

    stats = os.stat(file_name)
    bytes_downloaded += stats.st_size

    print("Downloaded {} new bytes, total {} of {}".format(stats.st_size, bytes_downloaded, max_bytes_to_download))

    doc = Query()
    db.update({'sequence':sequence, 'omit': False, 'downloaded': True, 'mime': mime, 'size':stats.st_size}, doc_ids = [next.doc_id])
    TinyDB(ADMIN_DB_LOCATION).update({'sequence': sequence, 'bytes_downloaded':bytes_downloaded}, Query()['admin'] == True)
    return

def omit(db, next):
    print("Omitting url {}".format(next['url']))
    db.update({'omit': True}, doc_ids = [next.doc_id])
    verify_preconditions(db)
    return

def prunedb(db):
    print("Pruning db to reduce size")
    doc = Query()
    # save and delete downloaded documents
    downloaded = db.search(doc.downloaded == True)
    if len(downloaded) != 0:
        writer = csv.writer(open(URL_LOCATION, "a"))
        ids = []
        for d in downloaded:
            writer.writerow([d['url'], d['mime'], "{}{}".format(d['sequence'], allowed_mime_types[d['mime']])])
            ids.append(d.doc_id)
        print("Inserting {} new documents".format(len(ids)))
        db.remove(doc_ids=ids)

    # remove omitted documents
    omitted = db.search(doc.omit == True)
    if len(omitted) != 0:
        ids = []
        for d in omitted:
            ids.append(d.doc_id)
        print("Removing {} omitted documents".format(len(ids)))
        db.remove(doc_ids=ids)

    return

if __name__ == "__main__":
    main()

