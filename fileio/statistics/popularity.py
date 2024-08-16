import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math

from utils import plot_frame
from utils import save_csv

#-----
"""
* x axis : ranking by references count
* y axis : reference count
"""
# ranking
def ref_cnt_rank(blkdf):
    read_rank = blkdf['count'][(blkdf['operation'] == 'read')].rank(ascending=False)
    blkdf.loc[(blkdf['operation'] == 'read'), ['op_rank']] = read_rank

    write_rank = blkdf['count'][(blkdf['operation'] == 'write')].rank(ascending=False)
    blkdf.loc[(blkdf['operation'] == 'write'), ['op_rank']] = write_rank

    rw_rank = blkdf['count'][(blkdf['operation'] == 'read&write')].rank(ascending=False)
    blkdf.loc[(blkdf['operation'] == 'read&write'), ['op_rank']] = rw_rank

    return blkdf

"""
* x axis : ranking by % of reference count (in percentile form)
* y axis : % of reference count
"""
def ref_cnt_percentile_rank(blkdf):
    total_read = blkdf['count'][(blkdf['operation'] == 'read')].sum()
    total_write = blkdf['count'][(blkdf['operation'] == 'write')].sum()
    total_rw = blkdf['count'][(blkdf['operation'] == 'read&write')].sum()

    # percentage
    blkdf['op_pcnt'] = blkdf['count'].astype('float64')
    blkdf.loc[(blkdf['operation'] == 'read'), ['op_pcnt']] /= total_read
    blkdf.loc[(blkdf['operation'] == 'write'), ['op_pcnt']] /= total_write
    blkdf.loc[(blkdf['operation'] == 'read&write'), ['op_pcnt']] /= total_rw

    # ranking in percentile form
    read_rank = blkdf['op_pcnt'][(blkdf['operation'] == 'read')].rank(ascending=False, pct=True)
    blkdf.loc[(blkdf['operation'] == 'read'), ['op_pcnt_rank']] = read_rank

    write_rank = blkdf['op_pcnt'][(blkdf['operation'] == 'write')].rank(ascending=False, pct=True)
    blkdf.loc[(blkdf['operation'] == 'write'), ['op_pcnt_rank']] = write_rank

    rw_rank = blkdf['op_pcnt'][(blkdf['operation'] == 'read&write')].rank(ascending=False, pct=True)
    blkdf.loc[(blkdf['operation'] == 'read&write'), ['op_pcnt_rank']] = rw_rank

    return blkdf

#-----
# zipf
def func_powerlaw(x, m, c):
    return c * (x ** m)

def zipf_param(freqs):
    from scipy.optimize import curve_fit

    target_func = func_powerlaw

    freqs = freqs[freqs != 0]
    y = freqs.sort_values(ascending=False).to_numpy()
    x = np.array(range(1, len(y) + 1))

    popt, pcov = curve_fit(target_func, x, y, maxfev=2000)
    #print(popt)

    return popt

#-----
def popularity_graph(blkdf, filename, fig_title, zipf=False, single_frame=True):
    # read
    x1 = blkdf['op_rank'][(blkdf['operation'] == 'read')].sort_values()
    y1 = blkdf['count'][(blkdf['operation'] == 'read')].sort_values(ascending=False)
    # write
    x2 = blkdf['op_rank'][(blkdf['operation'] == 'write')].sort_values()
    y2 = blkdf['count'][(blkdf['operation'] == 'write')].sort_values(ascending=False)
    # read&write
    x3 = blkdf['op_rank'][(blkdf['operation'] == 'read&write')].sort_values()
    y3 = blkdf['count'][(blkdf['operation'] == 'read&write')].sort_values(ascending=False)

    if single_frame:
        fig, ax = plot_frame((1, 1), title=fig_title, xlabel='Rank', ylabel='Reference counts', log_scale=True)
        ax = [ax]
    else:
        # type(ax) == numpy.ndarray
        fig, ax = plot_frame((2, 1), title=fig_title, xlabel='Rank', ylabel='Reference counts', log_scale=True)

    for a in ax:
        a.set_axisbelow(True)
        a.grid(True, which='major', color='black', alpha=0.5, linestyle='--')
        a.grid(True, which='minor', color='black', alpha=0.3, linestyle='--', lw=0.3)

    ax[0].scatter(np.arange(1,len(y1)+1), y1, color='blue', label='read', s=10)
    ax[0].scatter(np.arange(1,len(y2)+1), y2, color='red', label='write', s=10)
    if single_frame:
        #pass
        ax[0].scatter(np.arange(1,len(y3)+1), y3, color='green', label='read&write', s=10)
    else:
        ax[1].scatter(np.arange(1,len(y3)+1), y3, color='green', label='read&write', s=10)

    if zipf:
        s_best1 = zipf_param(y1)
        s_best2 = zipf_param(y2)
        s_best3 = zipf_param(y3)

        ax[0].plot(x1, func_powerlaw(x1, *s_best1), color="darkblue", lw=1)   # label="curve_fitting: read"
        ax[0].plot(x2, func_powerlaw(x2, *s_best2), color="brown", lw=1)  # label="curve_fitting: write"
        if single_frame:
            ax[0].plot(x3, func_powerlaw(x3, *s_best3), color="darkgreen", lw=1)  # label="curve_fitting: read&write"
        else:
            ax[1].plot(x3, func_powerlaw(x3, *s_best3), color="darkgreen", lw=1)  # label="curve_fitting: read&write"

        """ax[0].annotate(str(round(s_best1[0], 5)), xy=(10, func_powerlaw(10, *s_best1)), xycoords='data',
                    xytext=(40.0, 30.0), textcoords="offset points", color="steelblue", size=13,
                    arrowprops=dict(arrowstyle="->", ls="--", color="steelblue", connectionstyle="arc3,rad=-0.2"))
        ax[0].annotate(str(round(s_best2[0], 5)), xy=(5, func_powerlaw(5, *s_best2)), xycoords='data',
                    # xytext=(-30.0, -50.0)
                    xytext=(3.0, 10.0), textcoords="offset points", color="indianred", size=13,
                    arrowprops=dict(arrowstyle="->", ls="--", color="indianred", connectionstyle="arc3,rad=-0.2"))
        ax[0].annotate(str(round(s_best3[0], 5)), xy=(100, func_powerlaw(100, *s_best3)), xycoords='data',
                    # xytext=(-80.0, -50.0)
                    xytext=(20.0, 20.0), textcoords="offset points", color="olivedrab", size=13,
                    arrowprops=dict(arrowstyle="->", ls="--", color="olivedrab", connectionstyle="arc3,rad=-0.2"))"""
        print(s_best1, s_best2, s_best3)

    # legend
    for a in ax:
        a.legend(loc='upper right', ncol=1, markerscale=3)

    ax[0].axis([0.8, None, 0.8, None])
    xrange = ax[0].get_xlim()
    yrange = ax[0].get_ylim()

    if yrange[1] > xrange[1]:
        ax[0].set_xlim(yrange)
    else:
        ax[0].set_ylim(xrange)

    #plt.show()
    plt.savefig(filename+'.png', dpi=300)


def cdf_graph(blkdf, fig_title, filename):
    fig, ax = plot_frame((1, 1), title=fig_title, xlabel='Rank by reference count (%)', ylabel='Cumulative access ratio (%)')

    ax.set_axisbelow(True)
    ax.grid(True, color='black', alpha=0.5, linestyle='--')

    # calculate CDF for each operation
    x_list, y_list = [], []
    operations = ['read', 'write', 'read&write']
    for op in operations:
        cur_cdf = blkdf['op_pcnt'][(blkdf['operation'] == op)].sort_values(ascending=False).cumsum().to_numpy()
        cur_cdf_rank = blkdf['op_pcnt_rank'][(blkdf['operation'] == op)].sort_values(ascending=True).to_numpy()
        cur_x = np.concatenate(([0, cur_cdf_rank[0]], cur_cdf_rank, [1]))
        cur_y = np.concatenate(([0, 0], cur_cdf, [1]))

        x_list.append(cur_x)
        y_list.append(cur_y)

    # plot
    colors = ['blue', 'red', 'green']
    dash_colors = ['darkblue', 'brown', 'darkgreen']
    labels = ['read', 'write', 'total']
    for i in range(len(operations)-1):
        """
        '''1. same values are assigned as the same rank'''
        x_l = x_list[i];     y_l = y_list[i]
        '''2. ranks assigned in order they appear in the array'''
        # x_sl = np.arange(len(x_list[i])-3) / (len(x_list[i])-3);    y_sl = y_list[i][2:-1]
        x_sl = np.arange(len(x_list[i])) / (len(x_list[i]));          y_sl = y_list[i]
        """
        x_l = np.arange(len(x_list[i])-3) / (len(x_list[i])-3) * 100
        y_l = y_list[i][2:-1] * 100

        '''top_20_idx = np.where(x_l == 20)[0]'''
        idx = np.searchsorted(x_l, 20, side="left")
        if idx > 0 and (idx == len(x_l) or math.fabs(20 - x_l[idx-1]) < math.fabs(20 - x_l[idx])):
            top_20_idx = idx-1
        else:
            top_20_idx = idx

        print("[{0}]\ttop_20_idx: {1},\ttop_20_accounts_for: {2}".format(labels[i], top_20_idx, y_l[top_20_idx]))

        ax.plot(x_l, y_l, color=dash_colors[i], label=labels[i], lw=3)
        # ax.plot(x_sl, y_sl, , linestyle='dashed', color=dash_colors[i], lw=1.5)

    # legend
    ax.legend(loc='lower right', ncol=1, fontsize=20)

    #plt.show()
    plt.savefig(filename+'_cdf.png', dpi=300)