# Simple crawler
Information retrieval simple crawler project. This script will craw the web using an url

## Requirements
1. Install docker.
- [Docker](https://docs.docker.com/engine/installation/) 
2. Install git.
- [Git](https://gist.github.com/derhuerst/1b15ff4652a867391f03)

# How to run the proyect
1. Clone this project.
```
git clone https://github.com/fahernandez/simple-crawler
```
2. Execute 
```
cd simple-crawler
docker run -ti -v $PWD/src:/src fahernandez/simple-crawler:latest --levels=20 --gigabytes=2 --restart=true
```

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