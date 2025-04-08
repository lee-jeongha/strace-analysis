import matplotlib.pyplot as plt
import numpy as np

def plot_frame(subplot_matrix : tuple = (1, 1), subplot_figsize : tuple = (7, 7), title = '', xlabel = '', ylabel = '', font_size = 20, log_scale = False, share_xaxis : str or bool = True, share_yaxis : str or bool = True):
    subplot_rows = subplot_matrix[0]
    subplot_cols = subplot_matrix[1]
    subplot_width = subplot_matrix[1] * subplot_figsize[0]
    subplot_height = subplot_matrix[0] * subplot_figsize[1]

    single_frame = False if subplot_rows * subplot_cols > 1 else True

    font_size = font_size
    plt.rc('font', size=font_size)

    fig, ax = plt.subplots(subplot_rows, subplot_cols, figsize=(subplot_width, subplot_height), constrained_layout=True, sharex=share_xaxis, sharey=share_yaxis)
    if isinstance(ax, np.ndarray):
        ax = ax.flatten()

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

def plot_frame_odd(subplot_matrix : tuple = (1, 1), subplot_figsize : tuple = (7, 7), title = '', xlabel = '', ylabel = '', font_size = 20, log_scale = False, share_xaxis : str or bool = True, share_yaxis : str or bool = True, pad=(1,1)):
    import matplotlib.gridspec as gridspec

    subplot_row_size = subplot_matrix[1] * subplot_figsize[0] + pad[0] * (subplot_matrix[1] - 1)
    subplot_col_size = subplot_matrix[0] * subplot_figsize[1] + pad[1] * (subplot_matrix[0] - 1)

    font_size = font_size
    plt.rc('font', size=font_size)

    #fig = plt.figure(constrained_layout=True, figsize=(subplot_row_size, subplot_col_size))
    fig = plt.figure(figsize=(subplot_row_size, subplot_col_size))

    gs_row_pads = pad[1] * (subplot_matrix[0] - 1)
    gs_rows = int(round(subplot_figsize[1] * (subplot_matrix[0]) + gs_row_pads))

    gs_col_pad_ratio = pad[0] / (subplot_matrix[1] + pad[0])
    gs_col_division = (subplot_figsize[0] * (subplot_matrix[1] * (subplot_matrix[1] - 1) * 2))
    gs_cols = int(round(gs_col_division * (1 + gs_col_pad_ratio)))
    gs_col_pads = int(round(gs_col_division * gs_col_pad_ratio))
    gs = gridspec.GridSpec(nrows=gs_rows, ncols=gs_cols, figure=fig)

    y_pad = pad[1]
    x_pad = gs_col_pads // (subplot_matrix[1] - 1)

    fig_cnt = subplot_matrix[0]*subplot_matrix[1] - 1
    fig_cnt_row = subplot_matrix[1]
    fig_cnt_row_ = fig_cnt % subplot_matrix[1]
    fig_width = (gs_cols - gs_col_pads) // subplot_matrix[1]
    fig_height = (gs_rows - gs_row_pads) // subplot_matrix[0]
    fig_mod_pad = (gs_cols - (fig_cnt_row_ * fig_width) - x_pad * (fig_cnt_row_ - 1)) // 2

    for i in range(0, subplot_matrix[0]):
        if fig_cnt >= fig_cnt_row:
            for j in range(0, subplot_matrix[1]):
                fig.add_subplot(gs[((fig_height + y_pad) * i) : ((fig_height + y_pad) * i + fig_height),
                                   ((fig_width + x_pad) * j) : ((fig_width + x_pad) * j + fig_width)])
            fig_cnt -= fig_cnt_row
        else:
            for j in range(0, fig_cnt_row_):
                fig.add_subplot(gs[((fig_height + y_pad) * i) : ((fig_height + y_pad) * i + fig_height),
                                   (fig_mod_pad + (fig_width + x_pad) * j) : (fig_mod_pad + (fig_width + x_pad) * j + fig_width)])

    ax = fig.get_axes()
    if share_xaxis:
        for a in ax[1:]:
            a.sharex(ax[0])
    if share_yaxis:
        for a in ax[1:]:
            a.sharey(ax[0])

    if log_scale:
        plt.xscale('log')
        plt.yscale('log')

    if xlabel != '':
        fig.supxlabel(xlabel, fontsize = font_size + 5)
    if ylabel != '':
        fig.supylabel(ylabel, fontsize = font_size + 5)

    if title != '':
        plt.suptitle(title, fontsize = font_size + 10)

    return fig, ax