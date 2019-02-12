#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Feb  8 17:47:17 2019

@author: tjwilliamson
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import dates as mdates
import datetime
import os

basedir = os.path.abspath(os.path.dirname(__file__))

plt.style.use( os.path.join(basedir, "plotting.mplstyle" ) )
sns.set_style('whitegrid')


def round_to_nearest(num,mode='up',factor=10.):
    if mode=='up':
        func = np.ceil
    else:
        func = np.floor

    return int(func(num/float(factor))) * factor

class Plotter(object):

    def __init__(self,do_errors=True,norm=True,date_min=None,date_max=None):

        self.do_errors = do_errors
        self.norm = norm
        self.date_min = date_min
        self.date_max = date_max

        self.figure = None

        self.date_fmt =  mdates.DateFormatter('%m/%d')



    def format_axes(self,ax):

        ax.xaxis.set_major_formatter( self.date_fmt )
        self.figure.autofmt_xdate()
        ax.set_xlabel('Date')
        if self.norm:
            ax.set_ylabel('% of Starting Weight')
        else:
            ax.set_ylabel('Weight [lbs]')

        plt.minorticks_on()
        return ax

    def scale_axes(self,user,ax):

        imin = user.date_min
        imax = user.date_max
        dt = (imax - imin).total_seconds() / 3600. / 24.
        week = 7.
        if dt < 7.0:
            dmax = imax + datetime.timedelta(days = week - 1 )
            dmin = imin - datetime.timedelta(days = 1 )

            # try:
            #     imincur,imaxcur = map(mdates.num2date,ax.get_xlim())
            # except ValueError:
            #
            #xmin = min(dmin,imincur.date())
            #xmax = max(dmax,imaxcur.date())
            xmin = dmin
            xmax = dmax
            curdate = datetime.date.today()
            xmax = max(xmax,curdate)
            ax.set_xlim(xmin,xmax)

        if user.status:
            ydata = user.get_ydata()
            ymin = ydata.min()
            ymax = ydata.max()

            ymaxpct = ymax / ydata[0] * 100
            yminpct = ymin / ydata[0] * 100

            ymax_lim_pct = ymaxpct + 10
            ymin_lim_pct = yminpct - 30

            ymax_lim = ymax * ymax_lim_pct/100.
            ymin_lim = ymin * ymin_lim_pct/100.

            ymax_lim = round_to_nearest(ymax_lim,'up',10)
            ymin_lim = round_to_nearest(ymin_lim,'down',10)

            ax.set_ylim(ymin_lim,ymax_lim)


    def plot_user(self,user,color='blue'):

        if self.figure is not None:
            fig = self.figure
        else:
            fig = plt.figure()
            self.figure = fig


        ax = plt.gca()

        user.set_normalized(self.norm)

        r1 = user.plot_data( ax, color=color)
        r2 = user.plot_fit( ax, color=color )
        r3 = user.plot_butterfly( ax, color=color )

        self.format_axes(ax)
        self.scale_axes(user,ax)


    def savefig(self,fname):
        if self.figure is None:
            return

        self.format_axes(plt.gca())
        plt.savefig(fname,bbox_inches='tight')
        plt.close()
