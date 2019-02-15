#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Feb  8 17:47:17 2019

@author: tjwilliamson
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import dates as mdates
import datetime
import os

basedir = os.path.abspath(os.path.dirname(__file__))

plt.style.use( os.path.join(basedir, "plotting.mplstyle" ) )


def round_to_nearest(num,mode='up',factor=10.):
    if mode=='up':
        func = np.ceil
    else:
        func = np.floor

    return int(func(num/float(factor))) * factor

class Plotter(object):
    colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
    offset_max = 10.
    offset_min = 30.
    offset_max_all = 10.
    offset_min_all = 10.

    def __init__(self,do_errors=True,norm=True,date_min=None,date_max=None):

        self.do_errors = do_errors
        self.norm = norm
        self.date_min = date_min
        self.date_max = date_max

        self.figure = None

        self.date_fmt =  mdates.DateFormatter('%m/%d')


    @staticmethod
    def iter_colors():
        i = -1
        while True:
            i+=1
            yield Plotter.colors [ i % len(Plotter.colors) ]

    def format_axes(self,ax):

        ax = plt.gca()
        ax.xaxis.set_major_formatter( self.date_fmt )
        self.figure.autofmt_xdate()
        ax.set_xlabel('Date')
        if self.norm:
            ax.set_ylabel('% of Starting Weight')
        else:
            ax.set_ylabel('Weight [lbs]')

        plt.minorticks_on()
        ax.grid(True)
        return ax

    def scale_axes_users(self,users,ax):

        imin = min( [user.date_min for user in users] )
        imax = max( [user.date_max for user in users] )

        dt = (imax - imin).total_seconds() / 3600. / 24.
        week = 7.
        if dt < 7.0:
            dmax = imax + datetime.timedelta(days = week - 1 )
            dmin = imin - datetime.timedelta(days = 1 )

            xmin = dmin
            xmax = dmax
            curdate = datetime.date.today()
            xmax = max(xmax,curdate)
            ax.set_xlim(xmin,xmax)

        ymin = np.inf
        ymax = -np.inf

        for user in users:
            if not user.status:
                continue
            iymin = user.get_ydata().min()
            iymax = user.get_ydata().max()

            iyminpct = iymin / user.get_ydata()[0] * 100
            iymaxpct = iymax / user.get_ydata()[0] * 100

            iymax_lim_pct = iymaxpct + self.offset_max_all
            iymin_lim_pct = iyminpct - self.offset_min_all

            iymax_lim = iymax * iymax_lim_pct/100.
            iymin_lim = iymin * iymin_lim_pct/100.

            iymax_lim = round_to_nearest(iymax_lim,'up',10)
            iymin_lim = round_to_nearest(iymin_lim,'down',10)

            ymin = min( [ymin,iymin_lim] )
            ymax = max( [ymax,iymax_lim] )

        ax.set_ylim(ymin,ymax)


    def scale_axes(self,user,ax):

        imin = user.date_min
        imax = user.date_max
        dt = (imax - imin).total_seconds() / 3600. / 24.
        week = 7.
        if dt < 7.0:
            dmax = imax + datetime.timedelta(days = week - 1 )
            dmin = imin - datetime.timedelta(days = 1 )

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

            ymax_lim_pct = ymaxpct + self.offset_max
            ymin_lim_pct = yminpct - self.offset_min

            ymax_lim = ymax * ymax_lim_pct/100.
            ymin_lim = ymin * ymin_lim_pct/100.

            ymax_lim = round_to_nearest(ymax_lim,'up',10)
            ymin_lim = round_to_nearest(ymin_lim,'down',10)

            ax.set_ylim(ymin_lim,ymax_lim)

    def plot_all_users(self,users,colors=None):
        color_gen = Plotter.iter_colors()
        for i,user in enumerate( users ):
            name = user.get_user().first_name
            if colors is None:
                color = color_gen.next()
            elif user.get_user().email not in colors.keys():
                color = color_gen.next()
            else:
                color = colors [user.get_user().email]

            self.plot_user(user,label=name,color=color,
                fmt_axes=False,plot_ci=False)
        self.scale_axes_users(users,plt.gca())
        self.format_axes(plt.gca())
        plt.legend()

    def plot_user(self,user,label='',color='blue',fmt_axes=True,
        plot_data=True,plot_fit=True,plot_ci=True):

        if self.figure is not None:
            fig = self.figure
        else:
            fig = plt.figure()
            self.figure = fig


        ax = plt.gca()

        user.set_normalized(self.norm)

        if plot_data:
            r1 = user.plot_data( ax, color=color, label=label)
        if plot_fit:
            r2 = user.plot_fit( ax, color=color )
        if plot_ci:
            r3 = user.plot_butterfly( ax, color=color )

        if fmt_axes:
            self.format_axes(ax)
            self.scale_axes(user,ax)


    def savefig(self,fname):
        if self.figure is None:
            return

        self.format_axes(plt.gca())
        plt.savefig(fname,bbox_inches='tight')
        plt.close()
