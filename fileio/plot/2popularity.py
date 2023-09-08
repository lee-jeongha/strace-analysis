import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

def save_csv(df, filename, index=0):
    try:
        if index == 0:
            df.to_csv(filename, index=True, header=True, mode='w')  # encoding='utf-8-sig'
        else:  # append mode
            df.to_csv(filename, index=True, header=False, mode='a')  # encoding='utf-8-sig'
    except OSError:  # OSError: Cannot save file into a non-existent directory: '~'
        #if not os.path.exists(path):
        target_dir = filename.rfind('/')
        path = filename[:target_dir]
        os.makedirs(path)
        #---
        if index == 0:
            df.to_csv(filename, index=True, header=True, mode='w')  # encoding='utf-8-sig'
        else:  # append mode
            df.to_csv(filename, index=True, header=False, mode='a')  # encoding='utf-8-sig'


"""blkdf2.1
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

"""blkdf2.2
* x axis : ranking by % of reference count (in percentile form)
* y axis : % of reference count
"""
def ref_cnt_percentile_rank(blkdf):
    total_read = blkdf['count'][(blkdf['operation'] == 'read')].sum()
    total_write = blkdf['count'][(blkdf['operation'] == 'write')].sum()
    total_rw = blkdf['count'][(blkdf['operation'] == 'read&write')].sum()

    # percentage
    blkdf['op_pcnt'] = blkdf['count']
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

"""zipf"""
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

"""blkdf2.1 graph"""
def popularity_graph(blkdf, filename, fig_title, zipf=False):
    # read
    x1 = blkdf['op_rank'][(blkdf['operation'] == 'read')].sort_values()
    y1 = blkdf['count'][(blkdf['operation'] == 'read')].sort_values(ascending=False)
    # write
    x2 = blkdf['op_rank'][(blkdf['operation'] == 'write')].sort_values()
    y2 = blkdf['count'][(blkdf['operation'] == 'write')].sort_values(ascending=False)
    # read&write
    x3 = blkdf['op_rank'][(blkdf['operation'] == 'read&write')].sort_values()
    y3 = blkdf['count'][(blkdf['operation'] == 'read&write')].sort_values(ascending=False)

    if fig_title != '':
        plt.suptitle(fig_title, fontsize=30)
    plt.rcParams['font.size'] = 20

    if zipf:
        fig, ax = plt.subplots(figsize=(7, 7), constrained_layout=True)
        ax.set_axisbelow(True)
        ax.grid(True, color='black', alpha=0.5, linestyle='--')
        
        plt.scatter(np.arange(len(y1)), y1, color='blue', label='read', s=3)
        plt.scatter(np.arange(len(y2)), y2, color='red', label='write', s=3)
        plt.scatter(np.arange(len(y3)), y3, color='green', label='read&write', s=3)

        s_best1 = zipf_param(y1)
        s_best2 = zipf_param(y2)
        s_best3 = zipf_param(y3)

        plt.plot(x1, func_powerlaw(x1, *s_best1), color="darkblue", lw=1)   # label="curve_fitting: read"
        plt.plot(x2, func_powerlaw(x2, *s_best2), color="brown", lw=1)  # label="curve_fitting: write"
        plt.plot(x3, func_powerlaw(x3, *s_best3), color="darkgreen", lw=1)  # label="curve_fitting: read&write"

        ax.axis([0.8, None, 0.8, None])
        xrange = ax.get_xlim()
        yrange = ax.get_ylim()

        if yrange[1] > xrange[1]:
            ax.set_xlim(yrange)
        else:
            ax.set_ylim(xrange)

        """plt.annotate(str(round(s_best1[0], 5)), xy=(10, func_powerlaw(10, *s_best1)), xycoords='data',
                    xytext=(40.0, 30.0), textcoords="offset points", color="steelblue", size=13,
                    arrowprops=dict(arrowstyle="->", ls="--", color="steelblue", connectionstyle="arc3,rad=-0.2"))
        plt.annotate(str(round(s_best2[0], 5)), xy=(5, func_powerlaw(5, *s_best2)), xycoords='data',
                    # xytext=(-30.0, -50.0)
                    xytext=(3.0, 10.0), textcoords="offset points", color="indianred", size=13,
                    arrowprops=dict(arrowstyle="->", ls="--", color="indianred", connectionstyle="arc3,rad=-0.2"))
        plt.annotate(str(round(s_best3[0], 5)), xy=(100, func_powerlaw(100, *s_best3)), xycoords='data',
                    # xytext=(-80.0, -50.0)
                    xytext=(20.0, 20.0), textcoords="offset points", color="olivedrab", size=13,
                    arrowprops=dict(arrowstyle="->", ls="--", color="olivedrab", connectionstyle="arc3,rad=-0.2"))"""
        print(s_best1, s_best2, s_best3)

        plt.legend(loc='upper right', markerscale=3)

    else:
        fig, ax = plt.subplots(2, figsize=(7, 7*2), constrained_layout=True, sharex=True, sharey=True)  # sharex=True: share x axis
        ax[0].grid(True, color='black', alpha=0.5, linestyle='--')
        ax[1].grid(True, color='black', alpha=0.5, linestyle='--')

        ax[0].scatter(np.arange(len(y1)), y1, color='blue', label='read', s=3)
        ax[0].scatter(np.arange(len(y2)), y2, color='red', label='write', s=3)
        ax[1].scatter(np.arange(len(y3)), y3, color='green', label='read&write', s=3)

        # legend
        ax[0].legend(loc='upper right', ncol=1, markerscale=3)
        ax[1].legend(loc='upper right', ncol=1, markerscale=3)

        ax[0].axis([0.8, None, 0.8, None])
        xrange = ax[0].get_xlim()
        yrange = ax[0].get_ylim()

        if yrange[1] > xrange[1]:
            ax[0].set_xlim(yrange)
        else:
            ax[0].set_ylim(xrange)

    plt.xscale('log')
    plt.yscale('log')

    fig.supxlabel('rank', fontsize=25)
    fig.supylabel('block reference count', fontsize=25)

    #plt.show()
    plt.savefig(filename+'.png', dpi=300)


"""blkdf2.2 graph"""
def cdf_graph(blkdf, fig_title, filename):
    plt.rc('font', size=20)
    fig, ax = plt.subplots(figsize=(7, 7), constrained_layout=True)
    if fig_title != '':
        plt.title(fig_title, fontsize=30)
    ax.set_axisbelow(True)
    ax.grid(True, color='black', alpha=0.5, linestyle='--')

    # calculate CDF for each operation
    x_list, y_list = [], []
    operations = ['read', 'write', 'read&write']
    for op in operations:
        cur_cdf = blkdf['op_pcnt'][(blkdf['operation'] == op)].sort_values(ascending=False).cumsum().to_list()
        cur_cdf_rank = blkdf['op_pcnt_rank'][(blkdf['operation'] == op)].sort_values(ascending=True).to_list()
        cur_x = [0, cur_cdf_rank[0]] + cur_cdf_rank + [1]
        cur_y = [0, 0] + cur_cdf + [1]

        x_list.append(cur_x)
        y_list.append(cur_y)

    # plot
    colors = ['blue', 'red', 'green']
    dash_colors = ['darkblue', 'brown', 'darkgreen']
    labels = ['read', 'write', 'total']
    for i in range(len(operations)):
        '''1. same values are assigned as the same rank'''
        plt.plot(x_list[i], y_list[i], color=colors[i], label=labels[i], lw=3)

        '''2. ranks assigned in order they appear in the array'''
        #plt.plot(np.arange(len(x_list[i])-3) / (len(x_list[i])-3), y_list[i][2:-1], linestyle='dashed', marker='.', color=dash_colors[i], lw=1.5, ms=0.5)
        plt.plot(np.arange(len(x_list[i])-3) / (len(x_list[i])-3), y_list[i][2:-1], linestyle='dashed', color=dash_colors[i], lw=1.5)
        #plt.scatter(np.arange(len(x_list[i])-3) / (len(x_list[i])-3), y_list[i][2:-1], color=dash_colors[i], s=1)

    # legend
    fig.supxlabel('rank (in % form)', fontsize=25)
    fig.supylabel('CDF', fontsize=25)   # Cumulative Distribution Function
    ax.legend(loc='lower right', ncol=1, fontsize=20)

    #plt.show()
    plt.savefig(filename+'_cdf.png', dpi=300)

if __name__=="__main__":
    # add parser
    parser = argparse.ArgumentParser(description="plot popularity graph")

    parser.add_argument("--input", "-i", metavar='I', type=str,
                        nargs='?', default='input.txt', help='input file')
    parser.add_argument("--output", "-o", metavar='O', type=str,
                        nargs='?', default='output.txt', help='output file')
    parser.add_argument("--zipf", "-z", action='store_true',
                        help='calculate zipf parameter')
    parser.add_argument("--title", "-t", metavar='T', type=str,
                        nargs='?', default='', help='title of a graph')
    args = parser.parse_args()

    """##**blkdf2 = tendency of memory block access**"""
    blkdf2 = pd.read_csv(args.input, sep=',', header=0, index_col=0, on_bad_lines='skip')

    blkdf2 = ref_cnt_rank(blkdf2)
    blkdf2 = ref_cnt_percentile_rank(blkdf2)
    save_csv(blkdf2, args.output, 0)

    popularity_graph(blkdf=blkdf2, filename=args.output[:-4], fig_title=args.title, zipf=args.zipf)
    plt.cla()
    cdf_graph(blkdf=blkdf2, fig_title=args.title, filename=args.output[:-4])