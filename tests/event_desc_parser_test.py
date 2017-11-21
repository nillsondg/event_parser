import unittest
from event_desc_parser import *
import datetime


class TestEventDescParser(unittest.TestCase):
    @staticmethod
    def prepare_two_dates():
        # "11 – 12 ноября 2017, 10:00"
        date1 = datetime.datetime(year=2017, month=11, day=11, hour=10)
        end_date1 = datetime.datetime(year=2017, month=11, day=11, hour=22)
        date2 = datetime.datetime(year=2017, month=11, day=12, hour=10)
        end_date2 = datetime.datetime(year=2017, month=11, day=12, hour=22)
        return [(date1, end_date1), (date2, end_date2)]

    def test_parse_date(self):
        # 28 ноября 2017, 10:00
        # 11 – 12 НОЯБРЯ 2017, 10:45
        # 10 – 12 НОЯБРЯ 2017, 10:00
        date_str = "28 ноября 2017, 10:00"
        date = datetime.datetime(year=2017, month=11, day=28, hour=10)
        end_date = datetime.datetime(year=2017, month=11, day=28, hour=22)
        self.assertEqual([(date, end_date)], parse_digital_october_date(date_str))

        date_str = "11 – 12 ноября 2017, 10:00"
        self.assertEqual(self.prepare_two_dates(), parse_digital_october_date(date_str))

    def test_prepare_dates(self):
        res = [{"event_date": "2017-11-11", "start_time": "10:00", "end_time": "22:00"},
               {"event_date": "2017-11-12", "start_time": "10:00", "end_time": "22:00"}]
        self.assertEqual(res, prepare_date(self.prepare_two_dates()))
