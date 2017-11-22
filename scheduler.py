from datetime import datetime
from threading import Timer
import event_parser
import event_creator

x = datetime.today()
y = x.replace(day=x.day + 1, hour=x.hour, minute=x.minute, second=0, microsecond=0)
delta_t = y - x

secs = delta_t.seconds + 1


def schedule():
    print(str(datetime.today()) + "\tStart")
    print("Start checking")
    event_parser.parse_all()
    print("Start parsing")
    event_creator.process_digital_october()
    event_creator.process_planetarium()
    print(str(datetime.today()) + "\tDone")


schedule()
t = Timer(secs, schedule)
t.start()
