from apscheduler.schedulers.blocking import BlockingScheduler
from service.sync import crawl_nodes

if __name__ == "__main__":
    scheduler = BlockingScheduler()

    scheduler.add_job(crawl_nodes, "interval", minutes=5)

    scheduler.start()
