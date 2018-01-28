from datetime import datetime, timedelta
from threading import Timer
from mincult.min_cult import process_all as mincult_process

x = datetime.today()
y = x + timedelta(days=1)
delta_t = y - x

secs = delta_t.total_seconds()


def schedule():
    print(str(datetime.today()) + "\tStart")
    print("Start getting from mincult")
    mincult_process()
    print(str(datetime.today()) + "\tDone")

    t = Timer(secs, schedule)
    t.start()


schedule()
