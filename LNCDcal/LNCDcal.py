#from apiclient.discovery import build
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

import httplib2
#from oauth2client import client, file, tools

import datetime
import pytz
import re
import configparser
# """
# timezone/DST correction:
# """
# def getTimeFromUTC() ):
# #get the difference between localtime and now. round to half hours
# #N.B. bad b/c daylight saving!
# secdiff=(datetime.datetime.utcnow() - datetime.datetime.now()).total_seconds()
# hourdiff=round(secdiff/60,2)
# return( datetime.timedelta(seconds=hourdiff*60) )
#DELTAFROMUTC = getTimeFromUTC()


def to_utc(dt, tzstr="America/New_York"):
    tz = pytz.timezone(tzstr)
    return(dt - tz.utcoffset(dt))
    # later when printing, will get the same time as we put in
    # utc=pytz.timezone('UTC')
    # return( tz.localize(dt).astimezone( utc ) )

# def to_tz(dt,tzstr="America/New_York"):
#  tz=pytz.timezone(tzstr)
#  utc=pytz.timezone('UTC')
#  return( utc.localize(dt).astimezone( tz ) )


def get_service(api_name, api_version, scope, key_file_location,
                service_account_email):

    credentials = ServiceAccountCredentials.from_p12_keyfile(
        service_account_email, key_file_location, scopes=scope)

    # UPMC MItM's our SSL connection: disable_ssl_certificate_validation=True
    # todo: add as config switch
    http = credentials.authorize(httplib2.Http(
        disable_ssl_certificate_validation=True))

    # Build the service object.
    service = build(api_name, api_version, http=http)

    return service


def g2time(dtstr):
    """
    google time string to datetime
    -> google gives back time in localtime
    """
    return(datetime.datetime.strptime(dtstr[0:18], '%Y-%m-%dT%H:%M:%S'))


def calInfo(e):
    """
    get calendar info from google api returned dict
    split summary into expected parts: study age sex subj_initials ra score
    """
    d = {
        'start': e['start']['dateTime'],
        'starttime': g2time(e['start']['dateTime']),
        'dur_hr': (g2time(e['end']['dateTime']) - g2time(e['start']['dateTime'])).seconds / 60 / 60,
        'creator': e['creator'].get('displayName'),
        'note': e.get('description'),
        'calid': e.get('id'),
        'summary': e.get('summary'),
        'htmlLink': e.get('htmlLink')
    }

    c = re.compile(
        r'(?P<study>[a-z/]+)[ -]*(?P<age>[0-9.]+) *yo(?P<sex>m|f) *\(?(?P<subjinit>[A-Z]{2,3})\)? *(?P<ra>[A-Z]{2,3})[ -]*(?P<score>[0-9.]+)',
        re.I)
    m = re.search(c, e['summary'])
    if m:
        md = m.groupdict()
        d = {**d, **md}

    return(d)


def time2g(dt, tzstr="America/New_York"):
    dtutc = to_utc(dt)
    return(dtutc.isoformat() + 'Z')


def time2gdict(dt,
               tzstr="America/New_York"): return({'dateTime': time2g(dt),
                                                  'timeZone': tzstr})

"""
a class containing a connection to our google calendar
"""


class LNCDcal():
    # authetenticate
    # ini: cal.ini
    # [Calendar]
    #  email = 'yyy@xxx.iam.gserviceaccount.com'
    #  p12   = '/path/to/creds.p12'
    #  calID = 'email@gmail.com'
    #  tz    = 'America/New_York'
    def __init__(self, ini):

        # Define the auth scopes to request.
        # -- read in from ini
        config = configparser.RawConfigParser()
        config.read(ini)

        service_account_email = config.get('Calendar', 'email')
        key_file_location = config.get('Calendar', 'p12')
        self.calendarId = config.get('Calendar', 'calID')
        self.backCalID = config.get('Calendar', 'backCalID', fallback=None)
        self.tzstr = config.get('Calendar', 'tz')

        scope = ['https://www.googleapis.com/auth/calendar']
        self.cal = get_service('calendar', 'v3', scope, key_file_location,
                               service_account_email)
        # might need to be updated after events are add
        self.events = self.cal.events()

    def find_in_range(self, dtmin, dtmax):
        if(isinstance(dtmin, datetime.datetime)):
            dtmin = time2g(dtmin)
        if(isinstance(dtmax, datetime.datetime)):
            dtmax = time2g(dtmax)

        events = self.events.list(
            calendarId=self.calendarId,
            singleEvents=True,
            timeMin=dtmin,
            timeMax=dtmax).execute()
        # use only events with datetime starts (remove full day events)
        items = [calInfo(i) for i in events['items']
                 if i['start'].get('dateTime')]
        # check time
        #dt.isoformat()[0:16] ==  items[0]['start']['dateTime'][0:16]
        return(items)

    def find(self, dt):
        delta = 10
        dtmin = dt - datetime.timedelta(minutes=delta)
        dtmax = dt + datetime.timedelta(minutes=delta)
        items = self.find_in_range(dtmin, dtmax)
        return(items)

    def upcoming(self, daydelta=5):
        dt = datetime.datetime.now()
        dtmin = time2g(dt, self.tzstr)
        dtmax = time2g(dt + datetime.timedelta(days=daydelta), self.tzstr)
        items = self.find_in_range(dtmin, dtmax)
        return(items)

    def insert_event(self, startdt, dur_h, summary, desc):
        endtime = startdt + datetime.timedelta(hours=dur_h)
        event = {
            'summary': summary,
            'description': desc,
            'start': time2gdict(startdt, self.tzstr),
            'end': time2gdict(endtime, self.tzstr)
        }
        eventres = self.cal.events().insert(
            calendarId=self.calendarId, body=event).execute()
        return(eventres)

    def delete_event(self, eventId):
        res = self.cal.events().delete(
            calendarId=self.calendarId,
            eventId=eventId).execute()
        return(res)

    def get_event(self, eventId):
        """ get an event: useful for testing successful delete"""
        res = self.cal.events().get(
            calendarId=self.calendarId,
            eventId=eventId).execute()
        return(res)

    def move_event(self, eventId):
        """move event to different calendar we have a 'backCalID' in config"""
        if self.backCalID is None:
            raise Exception("No backCalID in config, but trying to move")
        print("moving %s to %s" % (eventId, self.backCalID))
        res = self.cal.events().move(
                calendarId=self.calendarId,
                eventId=eventId,
                destination=self.backCalID).execute()
        return(res)

