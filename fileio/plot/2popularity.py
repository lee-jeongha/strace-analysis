import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# add parser
parser = argparse.ArgumentParser(description="plot popularity graph")

parser.add_argument("--input", "-i", metavar='I', type=str, nargs='?', default='input.txt', help='input file')
parser.add_argument("--output", "-o", metavar='O', type=str, nargs='?', default='output.txt', help='output file')
parser.add_argument("--zipf", "-z", action='store_true', help='calculate zipf parameter')
parser.add_argument("--title", "-t", metavar='T', type=str, nargs='?', default='', help='title of a graph')
args = parser.parse_args()

def save_csv(df, filename, index=0):
  try:
    if index==0:
      df.to_csv(filename, index=True, header=True, mode='w') # encoding='utf-8-sig'
    else: #append mode
      df.to_csv(filename, index=True, header=False, mode='a') # encoding='utf-8-sig'
  except OSError:	# OSError: Cannot save file into a non-existent directory: '~'
    #if not os.path.exists(path):
    target_dir = filename.rfind('/')
    path = filename[:target_dir]
    os.makedirs(path)
    #---
    if index==0:
      df.to_csv(filename, index=True, header=True, mode='w') # encoding='utf-8-sig'
    else: #append mode
      df.to_csv(filename, index=True, header=False, mode='a') # encoding='utf-8-sig'

"""##**blkdf2 = tendency of memory block access**"""
blkdf2 = pd.read_csv(args.input, sep=',', header=0, index_col=0, on_bad_lines='skip')

"""blkdf2.1
* x axis : ranking by references count
* y axis : reference count
"""
# ranking
read_rank = blkdf2['count'][(blkdf2['operation']=='read')].rank(ascending=False)
blkdf2.loc[(blkdf2['operation']=='read'), ['op_rank']] = read_rank

write_rank = blkdf2['count'][(blkdf2['operation']=='write')].rank(ascending=False)
blkdf2.loc[(blkdf2['operation']=='write'), ['op_rank']] = write_rank

rw_rank = blkdf2['count'][(blkdf2['operation']=='read&write')].rank(ascending=False)
blkdf2.loc[(blkdf2['operation']=='read&write'), ['op_rank']] = rw_rank

"""blkdf2.2
* x axis : ranking by % of reference count (in percentile form)
* y axis : % of reference count
"""
total_read = blkdf2['count'][(blkdf2['operation']=='read')].sum()
total_write = blkdf2['count'][(blkdf2['operation']=='write')].sum()
total_rw = blkdf2['count'][(blkdf2['operation']=='read&write')].sum()

# percentage
blkdf2['op_pcnt'] = blkdf2['count']
blkdf2.loc[(blkdf2['operation']=='read'), ['op_pcnt']] /= total_read
blkdf2.loc[(blkdf2['operation']=='write'), ['op_pcnt']] /= total_write
blkdf2.loc[(blkdf2['operation']=='read&write'), ['op_pcnt']] /= total_rw

# ranking in percentile form
read_rank = blkdf2['op_pcnt'][(blkdf2['operation']=='read')].rank(ascending=False, pct=True)
blkdf2.loc[(blkdf2['operation']=='read'), ['op_pcnt_rank']] = read_rank

write_rank = blkdf2['op_pcnt'][(blkdf2['operation']=='write')].rank(ascending=False, pct=True)
blkdf2.loc[(blkdf2['operation']=='write'), ['op_pcnt_rank']] = write_rank

rw_rank = blkdf2['op_pcnt'][(blkdf2['operation']=='read&write')].rank(ascending=False, pct=True)
blkdf2.loc[(blkdf2['operation']=='read&write'), ['op_pcnt_rank']] = rw_rank

save_csv(blkdf2, args.output, 0)

"""zipf"""

if args.zipf:
  def func_powerlaw(x, m, c):
    return x ** m * c

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

font_size=15
parameters = {'axes.labelsize': font_size, 'axes.titlesize': font_size, 'xtick.labelsize': font_size, 'ytick.labelsize': font_size}
plt.rcParams.update(parameters)

if args.title != '':
  plt.suptitle(args.title, fontsize=17)

if args.zipf:
  plt.rcParams['figure.figsize'] = (7, 7)
  plt.rcParams['font.size'] = 12

  plt.scatter(np.arange(len(y1)), y1, color='blue', label='read', s=5)
  plt.scatter(np.arange(len(y2)), y2, color='red', label='write', s=5)
  plt.scatter(np.arange(len(y3)), y3, color='green', label='read&write', s=5)

  s_best1 = zipf_param(y1)
  s_best2 = zipf_param(y2)
  s_best3 = zipf_param(y3)

  plt.plot(x1, func_powerlaw(x1, *s_best1), color="skyblue", lw=2, label="curve_fitting: read")
  plt.plot(x2, func_powerlaw(x2, *s_best2), color="salmon", lw=2, label="curve_fitting: write")
  plt.plot(x3, func_powerlaw(x3, *s_best3), color="limegreen", lw=2, label="curve_fitting: read&write")

  plt.annotate(str(round(s_best1[0],5)), xy=(10, func_powerlaw(10, *s_best1)), xycoords='data',
               xytext=(40.0, 30.0), textcoords="offset points", color="steelblue", size=13,
               arrowprops=dict(arrowstyle="->", ls="--", color="steelblue", connectionstyle="arc3,rad=-0.2"))
  plt.annotate(str(round(s_best2[0],5)), xy=(5, func_powerlaw(5, *s_best2)), xycoords='data',
               xytext=(3.0, 10.0), textcoords="offset points", color="indianred", size=13,  # xytext=(-30.0, -50.0)
               arrowprops=dict(arrowstyle="->", ls="--", color="indianred", connectionstyle="arc3,rad=-0.2"))
  plt.annotate(str(round(s_best3[0],5)), xy=(100, func_powerlaw(100, *s_best3)), xycoords='data',
               xytext=(20.0, 20.0), textcoords="offset points", color="olivedrab", size=13,  # xytext=(-80.0, -50.0)
               arrowprops=dict(arrowstyle="->", ls="--", color="olivedrab", connectionstyle="arc3,rad=-0.2"))
  print(s_best1, s_best2, s_best3)

  plt.xscale('log')
  plt.yscale('log')

  plt.legend(loc='lower left')
  plt.xlabel('rank')
  plt.ylabel('block reference count')

else:
  plt.cla()

  fig, ax = plt.subplots(2, figsize=(6,7), constrained_layout=True, sharex=True, sharey=True) # sharex=True: share x axis

  # read/write graph
  ax[0].scatter(np.arange(len(y1)), y1, color='blue', label='read', s=5)
  ax[0].scatter(np.arange(len(y2)), y2, color='red', label='write', s=5)

  # read+write graph
  ax[1].scatter(np.arange(len(y3)), y3, color='green', label='read&write', s=5)

  # legend
  ax[0].legend(loc='lower left', ncol=1)  # loc = 'best', 'upper right'
  ax[1].legend(loc='lower left', ncol=1)  # loc = 'best', (1.0,0.8)

  plt.xscale('log')
  plt.yscale('log')

  fig.supxlabel('rank', fontsize=17)
  fig.supylabel('block reference count', fontsize=17)

#plt.show()
plt.savefig(args.output[:-4]+'.png', dpi=300)


"""blkdf2.2 graph"""

plt.cla()

plt.figure(figsize=(8,7))
plt.rcParams.update({'font.size': 17})
if args.title != '':
  plt.title(args.title, fontsize=17)
plt.grid(True, color='black', alpha=0.5, linestyle='--')

#read
y1 = blkdf2['op_pcnt'][(blkdf2['operation']=='read')].sort_values(ascending=False).cumsum()
x1 = np.arange(len(y1))
x1 = (x1 / len(y1))
#write
y2 = blkdf2['op_pcnt'][(blkdf2['operation']=='write')].sort_values(ascending=False).cumsum()
x2 = np.arange(len(y2))
x2 = (x2 / len(y2))
#read&write
y3 = blkdf2['op_pcnt'][(blkdf2['operation']=='read&write')].sort_values(ascending=False).cumsum()
x3 = np.arange(len(y3))
x3 = (x3 / len(y3))

#scatter
plt.scatter(x1, y1, color='blue', label='read', s=5)
plt.scatter(x2, y2, color='red', label='write', s=5)
plt.scatter(x3, y3, color='green', label='read&write', s=5)

# legend
plt.xlabel('rank (in % form)', fontsize=17)
plt.ylabel('% of reference count', fontsize=17)
plt.legend(loc='lower right', ncol=1)

#plt.show()
plt.savefig(args.output[:-4]+'_pareto.png', dpi=300)