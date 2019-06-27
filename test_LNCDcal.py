#!/usr/bin/env python3

#
# Usage:
#   ~/.local/bin/pytest test_LNCDcal.py
#

import pytest
from LNCDcal import *
import datetime


def test_time2g_summer():
    dt = datetime.datetime(2017, 7, 29, 1, 2, 3)
    gt = time2g(dt)
    # utc is 4 hours later
    assert(gt == "2017-07-29T05:02:03Z")


def test_time2g_winter():
    dt = datetime.datetime(2017, 1, 29, 1, 2, 3)
    gt = time2g(dt)
    # utc is 5 hours later (dst)
    assert(gt == "2017-01-29T06:02:03Z")


def test_g2time():
    gt = "2017-01-29T10:05:04Z"
    dt = g2time(gt)
    # no seconds in google time
    assert(dt == datetime.datetime(2017, 1, 29, 10, 5))


def test_time2gdict():
    pass


class TestCal():
    def setup(self):
        self.cal = LNCDcal('cal.ini')

    # insert_event(self,startdt,dur_h,summary,desc):
    def test_insert_remove(self):
        dt = datetime.datetime.now()
        dur_h = 2
        e = self.cal.insert_event(dt, dur_h, 'TEST ONLY', 'longer desc')
        assert(e is not None)
        assert(e['id'] is not None)
        assert(e['summary'] == 'TEST ONLY')
        assert(e['description'] == 'longer desc')

        # google doesn't use seconds
        dtg = dt.replace(second=0, microsecond=0)
        estarttime = g2time(e['start']['dateTime']).replace(second=0)
        eendtime = g2time(e['end']['dateTime']).replace(second=0)
        dtge = dt.replace(microsecond=0, second=0) + \
            datetime.timedelta(hours=dur_h)

        assert(dtg == estarttime)
        assert(dtge == eendtime)

        delres = self.cal.delete_event(e['id'])
        assert(delres == '')
