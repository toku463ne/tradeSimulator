import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Do NOT import env
import datetime, calendar, time, pytz, tzlocal
import os
import shutil
import math
import numpy as np
unix_epoch = np.datetime64(0, 's')
one_second = np.timedelta64(1, 's')

from consts import *    

def epoch2dt(epoch):
    d = datetime.datetime.utcfromtimestamp(epoch)
    return d

# Thu=0, Fri=1, Sat=2, Sun=3, Mon=4, Tue=5, Wed=6
def dt2epoch(gmdt):
    return math.floor(calendar.timegm(gmdt.timetuple()))

def str2dt(strgmdt, format=DEFAULT_DATETIME_FORMAT):
    d = datetime.datetime.strptime(strgmdt, format)
    if format[-2:] != "%z":
        d = d.replace(tzinfo=tzlocal.get_localzone())
    return d
    
def str2epoch(strgmdt, format=DEFAULT_DATETIME_FORMAT):
    return dt2epoch(str2dt(strgmdt, format))
    
def dt2str(gmdt, format=DEFAULT_DATETIME_FORMAT):
    return gmdt.strftime(format)

def epoch2str(epoch, format=DEFAULT_DATETIME_FORMAT):
    return dt2str(epoch2dt(epoch), format)

def nowepoch():
    return time.time()

def epoch2weeknum(epoch):
    return int(epoch % (86400*7) / 86400)

def npdt2dt(dt64):
    seconds_since_epoch = (dt64 - unix_epoch) / one_second
    return datetime.datetime.utcfromtimestamp(seconds_since_epoch)


def list2str(list1, sep=",", enquote=False):
    s = ""
    for v in list1:
        if enquote:
            v = "'%s'" % str(v)
        if s == "":
            s = v
        else:
            s = "%s%s %s" % (s, sep, str(v))
    return s


def mergeJson(j1, j2):
    if not isinstance(j1, dict) or not isinstance(j2, dict):
        return j2

    if len(j1) == 0 or len(j2) == 0:
        return j2
    for k1 in j1.keys():
        for k2 in j2.keys():
            if k1 == k2:
                j1[k1] = mergeJson(j1[k1], j2[k2])
                break
    
    return j1

def ensureDir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def removeDir(path):
    if os.path.exists(path):
        shutil.rmtree(path)

def ensureDataDir(data_dir="", subdir=""):
    home = os.environ["HOME"]
    if data_dir == "":
        data_dir = "%s/%s" % (home, DEFAULT_DATA_DIR)
    if data_dir[0] != "/":
        data_dir = "%s/%s" % (home, data_dir)
    if subdir != "":
        data_dir += "/" + subdir
    ensureDir(data_dir)
    return data_dir


def adjust_data(data):
    start = data["start_date"]
    end = data["end_date"]
    if len(start) == 10:
        start = start + "T00:00:00"
        end = end + "T00:00:00"
    data["start_date"] = start
    data["end_date"] = end
    return data