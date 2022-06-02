from apscheduler.schedulers.blocking import BlockingScheduler
from service.sync import assign_country

if __name__ == "__main__":
    scheduler = BlockingScheduler()

    scheduler.add_job(assign_country, "interval", seconds=10)

    scheduler.start()
