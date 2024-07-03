import matplotlib.pyplot as plt

def plot_frame(subplot_matrix : tuple = (1, 1), subplot_figsize : tuple = (7, 7), title = '', xlabel = '', ylabel = '', font_size = 20, log_scale = False, share_xaxis : str or bool = True, share_yaxis : str or bool = True):
    subplot_rows = subplot_matrix[0]
    subplot_cols = subplot_matrix[1]
    subplot_width = subplot_matrix[1] * subplot_figsize[0]
    subplot_height = subplot_matrix[0] * subplot_figsize[1]

    single_frame = False if subplot_rows * subplot_cols > 1 else True

    font_size = font_size
    plt.rc('font', size=font_size)

    fig, ax = plt.subplots(subplot_rows, subplot_cols, figsize=(subplot_width, subplot_height), constrained_layout=True, sharex=share_xaxis, sharey=share_yaxis)

    if title != '':
        plt.suptitle(title, fontsize = font_size * 1.5)

    if log_scale:
        plt.xscale('log')
        plt.yscale('log')

    if xlabel != '':
        ax.set_xlabel(xlabel, fontsize = font_size * 1.25) if single_frame else fig.supxlabel(xlabel, fontsize = font_size * 1.25)
    if ylabel != '':
        ax.set_ylabel(ylabel, fontsize = font_size * 1.25) if single_frame else fig.supylabel(ylabel, fontsize = font_size * 1.25)

    return fig, ax