import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

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


"""##**blkdf2 = tendency of memory block access**"""
blkdf2 = pd.read_csv(args.input, sep=',', header=0, index_col=0, on_bad_lines='skip')

"""blkdf2.1
* x axis : ranking by references count
* y axis : reference count
"""
# ranking
read_rank = blkdf2['count'][(blkdf2['operation'] == 'read')].rank(ascending=False)
blkdf2.loc[(blkdf2['operation'] == 'read'), ['op_rank']] = read_rank

write_rank = blkdf2['count'][(blkdf2['operation'] == 'write')].rank(ascending=False)
blkdf2.loc[(blkdf2['operation'] == 'write'), ['op_rank']] = write_rank

rw_rank = blkdf2['count'][(blkdf2['operation'] == 'read&write')].rank(ascending=False)
blkdf2.loc[(blkdf2['operation'] == 'read&write'), ['op_rank']] = rw_rank

"""blkdf2.2
* x axis : ranking by % of reference count (in percentile form)
* y axis : % of reference count
"""
total_read = blkdf2['count'][(blkdf2['operation'] == 'read')].sum()
total_write = blkdf2['count'][(blkdf2['operation'] == 'write')].sum()
total_rw = blkdf2['count'][(blkdf2['operation'] == 'read&write')].sum()

# percentage
blkdf2['op_pcnt'] = blkdf2['count']
blkdf2.loc[(blkdf2['operation'] == 'read'), ['op_pcnt']] /= total_read
blkdf2.loc[(blkdf2['operation'] == 'write'), ['op_pcnt']] /= total_write
blkdf2.loc[(blkdf2['operation'] == 'read&write'), ['op_pcnt']] /= total_rw

# ranking in percentile form
read_rank = blkdf2['op_pcnt'][(blkdf2['operation'] == 'read')].rank(ascending=False, pct=True)
blkdf2.loc[(blkdf2['operation'] == 'read'), ['op_pcnt_rank']] = read_rank

write_rank = blkdf2['op_pcnt'][(blkdf2['operation'] == 'write')].rank(ascending=False, pct=True)
blkdf2.loc[(blkdf2['operation'] == 'write'), ['op_pcnt_rank']] = write_rank

rw_rank = blkdf2['op_pcnt'][(blkdf2['operation'] == 'read&write')].rank(ascending=False, pct=True)
blkdf2.loc[(blkdf2['operation'] == 'read&write'), ['op_pcnt_rank']] = rw_rank

save_csv(blkdf2, args.output, 0)

"""zipf"""

if args.zipf:
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

# read
x1 = blkdf2['op_rank'][(blkdf2['operation'] == 'read')].sort_values()
y1 = blkdf2['count'][(blkdf2['operation'] == 'read')].sort_values(ascending=False)
# write
x2 = blkdf2['op_rank'][(blkdf2['operation'] == 'write')].sort_values()
y2 = blkdf2['count'][(blkdf2['operation'] == 'write')].sort_values(ascending=False)
# read&write
x3 = blkdf2['op_rank'][(blkdf2['operation'] == 'read&write')].sort_values()
y3 = blkdf2['count'][(blkdf2['operation'] == 'read&write')].sort_values(ascending=False)

if args.title != '':
    plt.suptitle(args.title, fontsize=30)
plt.rcParams['font.size'] = 20

if args.zipf:
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
plt.savefig(args.output[:-4]+'.png', dpi=300)


"""blkdf2.2 graph"""

plt.cla()

plt.rc('font', size=20)
fig, ax = plt.subplots(figsize=(7, 7), constrained_layout=True)
if args.title != '':
    plt.title(args.title, fontsize=30)
ax.set_axisbelow(True)
ax.grid(True, color='black', alpha=0.5, linestyle='--')

#read
rcdf = blkdf2['op_pcnt'][(blkdf2['operation'] == 'read')].sort_values(ascending=False).cumsum().to_list()
rcdf_rank = blkdf2['op_pcnt_rank'][(blkdf2['operation'] == 'read')].sort_values(ascending=True).to_list()
x1 = [0, rcdf_rank[0]] + rcdf_rank + [1]
y1 = [0, 0] + rcdf + [1]
#write
wcdf = blkdf2['op_pcnt'][(blkdf2['operation'] == 'write')].sort_values(ascending=False).cumsum().to_list()
wcdf_rank = blkdf2['op_pcnt_rank'][(blkdf2['operation'] == 'write')].sort_values(ascending=True).to_list()
x2 = [0, wcdf_rank[0]] + wcdf_rank + [1]
y2 = [0, 0] + wcdf + [1]
#read&write
rwcdf = blkdf2['op_pcnt'][(blkdf2['operation'] == 'read&write')].sort_values(ascending=False).cumsum().to_list()
rwcdf_rank = blkdf2['op_pcnt_rank'][(blkdf2['operation'] == 'read&write')].sort_values(ascending=True).to_list()
x3 = [0, rwcdf_rank[0]] + rwcdf_rank + [1]
y3 = [0, 0] + rwcdf + [1]

#scatter
plt.plot(x1, y1, color='blue', label='read', lw=3)
plt.plot(x2, y2, color='red', label='write', lw=3)
plt.plot(x3, y3, color='green', label='read&write', lw=3)
plt.plot(np.arange(len(rcdf_rank)) / len(rcdf_rank), rcdf, '--', color='darkblue', lw=1.5)
plt.plot(np.arange(len(wcdf_rank)) / len(wcdf_rank), wcdf, '--', color='brown', lw=1.5)
plt.plot(np.arange(len(rwcdf_rank)) / len(rwcdf_rank), rwcdf, '--', color='darkgreen', lw=1.5)

# legend
fig.supxlabel('rank (in % form)', fontsize=25)
fig.supylabel('CDF', fontsize=25)   # Cumulative Distribution Function
ax.legend(loc='lower right', ncol=1, fontsize=20)

#plt.show()
plt.savefig(args.output[:-4]+'_cdf.png', dpi=300)
