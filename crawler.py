from service.crawler import Crawler

if __name__ == "__main__":
    # Run the crawler
    Crawler(num_workers=25, timeout=3).crawl()
