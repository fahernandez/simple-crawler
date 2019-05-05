# Simple crawler
Information retrival simple crawler project. This script will craw the web using an url

## Requirements
1. This project will requires install docker locally.
- [Docker](https://docs.docker.com/engine/installation/) 

# How to run the proyect
docker run -ti -v $PWD/src:/src fahernandez/simple-crawler --levels 20 --gigabytes 2

# Options
```
Usage: crawler.py [OPTIONS]

Options:
  --gigabytes INTEGER  Max number og gigabytes to be downloaded.
  --url TEXT           Page url to be crawled.
  --levels INTEGER     Maximum deeper level to be reach while crawling.
  --restart BOOLEAN    Restart the crawling process.
  --help               Show this message and exit.
 ```
 
Note: The crawling result will be save on file url.txt