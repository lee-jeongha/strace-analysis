import matplotlib.pyplot as plt

def plot_frame(subplot_matrix : tuple = (1, 1), subplot_figsize : tuple = (7, 7), title = '', xlabel = '', ylabel = '', font_size = 20, log_scale = False, share_xaxis : str or bool = True, share_yaxis : str or bool = True):
    subplot_rows = subplot_matrix[0]
    subplot_cols = subplot_matrix[1]
    subplot_row_size = subplot_matrix[1] * subplot_figsize[0]
    subplot_col_size = subplot_matrix[0] * subplot_figsize[1]

    font_size = font_size
    plt.rc('font', size=font_size)

    fig, ax = plt.subplots(subplot_rows, subplot_cols, figsize=(subplot_row_size, subplot_col_size), constrained_layout=True, sharex=share_xaxis, sharey=share_yaxis)

    if title != '':
        plt.suptitle(title, fontsize = font_size + 10)

    if log_scale:
        plt.xscale('log')
        plt.yscale('log')

    if xlabel != '':
        fig.supxlabel(xlabel, fontsize = font_size + 5)
    if ylabel != '':
        fig.supylabel(ylabel, fontsize = font_size + 5)

    return fig, ax