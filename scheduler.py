from datetime import datetime, timedelta
from threading import Timer
import event_parser
import event_creator

x = datetime.today()
y = x + timedelta(days=1)
delta_t = y - x

secs = delta_t.total_seconds()


def schedule():
    print(str(datetime.today()) + "\tStart")
    print("Start checking")
    event_parser.parse_all()
    print("Start parsing")
    event_creator.process_all()
    print(str(datetime.today()) + "\tDone")

    t = Timer(secs, schedule)
    t.start()


schedule()
