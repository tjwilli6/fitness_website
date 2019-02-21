import datetime
#import tzlocal
import pytz
import numpy as np
import config as cfg

class DateUtil:

    @staticmethod
    def utcnow():
        return datetime.datetime.utcnow()
    @staticmethod
    def get_utc_offset(tz=cfg.TIMEZONE):
        dt = datetime.datetime.now()
        try:
            timezone = pytz.timezone(tz)
        except:
            return
        utcoff = timezone.utcoffset(dt).total_seconds() / 3600.
        return datetime.timedelta(hours=utcoff)

    @staticmethod
    def now(tz=cfg.TIMEZONE):
        dt = datetime.datetime.utcnow()
        utcoff = DateUtil.get_utc_offset(tz)
        return dt + utcoff

    @staticmethod
    def today(tz=cfg.TIMEZONE):
        return DateUtil.now(tz).date()

    @staticmethod
    def convert_datetimes(dt,tz=cfg.TIMEZONE,convert_to_date=False):
        dt = np.array(dt,ndmin=1)
        utcoff = DateUtil.get_utc_offset(tz)

        if convert_to_date:
            dates = [(idt + utcoff).date() for idt in dt]
        else:
            dates = [(idt + utcoff) for idt in dt]

        return np.array(dates)
