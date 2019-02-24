#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Feb  8 16:43:22 2019

@author: tjwilliamson
"""


import numpy as np
from scipy.optimize import curve_fit
from models import Measurement, User
import config
import matplotlib.pyplot as plt
import datetime
from app.utils import DateUtil

class UserDataBase(object):

    def __init__(self,user,norm=True):

        self.__user = user
        self.__x_dates = None
        self.__x_days = None
        self.__y_data = None
        self.__y_err = None
        self.do_errors = True
        self.norm = norm
        self.__load_data__()

    def get_user(self):
        return self.__user

    def __load_data__(self):
        """Query the user data"""
        email = self.__user.email
        measurements = Measurement.query.filter_by(email=email).all()

        weights = np.array( [] )
        dates = np.array( [] )
        if len( measurements ):
            dates = np.array( [m.timestamp for m in measurements] )
            weights = np.array( [m.weight for m in measurements] )

            weights = np.array( [x for _,x in sorted( zip(dates,weights) ) ] )
            dates = DateUtil.convert_datetimes( np.array ( sorted(dates) ),convert_to_date=True)

            days = np.array( [td.total_seconds() / 3600. / 24. for td in dates - dates[0]] )


            self.__x_dates = dates
            self.__x_days = days
            self.__y_data = weights

            yerr = getattr(config,'WT_ERROR',None)

            if yerr is not None:
                self.__y_err = np.ones_like(self.__y_data) * yerr
            else:
                self.do_errors = False



    def get_y0(self):
        
        if self.status is None:
            return
        d0 = config.DT_STRT
        y0 = self.get_y_by_date(d0)
        if y0 is None:
            return self.get_ydata()[0]
        return y0

    def get_y_by_date(self,date):
        """Get a measurement for a given date"""
        if not self.status:
            return
        
        if not isinstance(date,datetime.date):
            raise TypeError("Date argument must be 'datetime.date' instance")
        xdates = self.get_xdata(dates=True)
        
        dates_below = xdates [ xdates <= date ]
        dates_above = xdates [ xdates >= date ]
        
        #Get the index of the nearest dates above and below
        ilow = ihi = None
    
        if len(dates_below):
            ilow = np.argmax(dates_below)
        if len(dates_above):
            ihi = np.argmin(dates_above)
        
        index = None
        
        if ilow is None and ihi is None:
            return
        
        if ilow==ihi:
            index = ilow   
            
        else:
            if ilow is not None:
                diff_lo = np.abs ( (date - xdates[ilow]).total_seconds() )
            else:
                diff_lo = np.inf
            if ihi is not None:
                diff_hi = np.abs ( (date - xdates[ihi]).total_seconds() )
            else:
                diff_hi = np.inf
            
            if diff_lo < diff_hi:
                index = ilow
            else:
                index = ihi
        
        return self.__y_data [index]
            

    def get_xdata(self,dates=False):

        if dates:
            return self.__x_dates
        return self.__x_days


    def get_norm_factor(self):
        norm = 1
        if self.norm:
            norm = self.get_y0() * 0.01
        return norm

    def set_normalized(self,bnorm=True):
        self.norm = bnorm

    def get_ydata(self):

        return self.__y_data / self.get_norm_factor()

    def get_yerror(self):

        return self.__y_err / self.get_norm_factor()


    def get_analyis(self):
        return AnaData(self.__x_days,self.__y_data,self.__y_err)

    def toggle_errors(self,do_errors=True):
        self.__do_errors = do_errors


    @property
    def status(self):
        return ( self.__y_data is not None and self.__x_dates is not None
                and self.__y_data.size > 0 and self.__y_data.size == self.__x_dates.size )


def is_valid(number):
    if number is None or np.isnan(number) or np.isinf(number):
        return False
    return True







class AnaData(UserDataBase):

    def __init__(self,user,norm=True):

        super(AnaData,self).__init__(user,norm=norm)

        self.date_min = None
        self.date_max = None

        self.set_plotting_range()
        self.fit_status = False
        self.fit_result = ()

    def days_to_date(self,xdays):

        t0 = datetime.datetime.combine ( self.date_min, datetime.time(hour=0) )
        days = np.array( [datetime.timedelta(days=d) for d in xdays] )

        return t0 + days

    def set_plotting_range(self,date_min=None,date_max=None):

        bstatus = self.status

        if date_min is None:
            if bstatus:
                self.date_min = self.get_xdata(dates=True)[0]
            else:
                self.date_min = datetime.date.today()

        if date_max is None:
            if bstatus:
                self.date_max = self.get_xdata(dates=True)[-1]
            else:
                self.date_max = datetime.date.today()

    def get_xfit(self):

        if not self.status:
            return
        xmin = (self.date_min - self.get_xdata(True)[0]).total_seconds() / 3600./24.
        xmax = (self.date_max - self.get_xdata(True)[0]).total_seconds() / 3600./24.

        return np.linspace(xmin,xmax,1000)

    def get_xplot(self):

        if not self.status:
            return
        return self.days_to_date(self.get_xfit())

    def fit(self):

        if not self.status:
            return

        popt,pcov = curve_fit( self.__linear_func__, self.get_xdata(), self.get_ydata(),
                              sigma=self.get_yerror(),absolute_sigma=True )

        if len(popt):
            popt = popt[0]
        perr = None
        if len(pcov) and self.do_errors:
            perr = np.sqrt ( np.diag( pcov ) )

        self.fit_result = popt,perr

        if not is_valid(popt) or not is_valid(perr):
            self.fit_status = False
        else:
            self.fit_status = True

    def plot_data(self,ax=None,color='blue',label=''):
        
        if ax is None:
            ax = plt.gca()

        if not self.status:
            return
        yerr = None

        if self.do_errors:
            yerr = self.get_yerror()

        return ax.errorbar( self.get_xdata(dates=True),
                    self.get_ydata(),
                    yerr=yerr,
                    fmt='o',
                    color=color,
                    capsize=2,
                    label=label )



    def plot_butterfly(self,ax=None,ndraws=100,color='blue',alpha=.25):
        if ax is None:
            ax = plt.gca()

        if not self.status:
            return

        if not self.fit_result:
            self.fit()
            if not self.fit_result:
                return

        m,merr = self.fit_result

        if not is_valid(m) or not is_valid(merr):
            return

        xdata = self.get_xfit()

        xfit = np.zeros ( (ndraws, xdata.size ) )
        xfit[:,:] = xdata
        m = np.random.normal(loc=m,scale=merr,size=xfit.shape)

        yfit = self.get_ydata()[0] + xfit * m
        ymean = yfit.mean(0)
        ystd = yfit.std(0)

        return ax.fill_between(self.get_xplot(),ymean-ystd,ymean+ystd,color=color,alpha=alpha)



    def plot_fit(self,ax=None,color='blue'):

        ax = plt.gca()
        if not self.status:
            return

        if not self.fit_result:
            self.fit()
            if not self.fit_result:
                return

        m,merr = self.fit_result

        if not is_valid(m) or not is_valid(merr):
            return

        xfit = self.get_xfit()
        yfit = self.get_ydata()[0] + m * xfit

        return ax.plot(self.get_xplot(),yfit,color=color)


    def get_projected_weight(self,date_obj):

        if self.status and self.fit_status:
            if isinstance(date_obj,datetime.datetime):
                date_obj = date_obj.date()

            xdata = self.get_xdata(True)
            date_last_meas = xdata[-1]

            days_to_date = date_obj - date_last_meas

            days = days_to_date.days

            # m = np.random.normal(*self.fit_result,size=1000)
            # proj_weight = self.get_ydata()[-1] + days * m
            #
            # return proj_weight.mean(),proj_weight.std()
            m,merr = self.fit_result
            proj_weight = self.get_ydata()[-1] + days * m
            proj_weight_err = days * merr

            print merr,days
            return proj_weight,proj_weight_err
        return None,None


    def __linear_func__(self,xdata,m):
        if not self.status:
            return
        return self.get_ydata()[0] + m * xdata
