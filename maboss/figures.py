"""Tools to draw figures from the MaBoSS results."""

import operator

import pandas as pd
import matplotlib.pylab as plt
import numpy as np

def persistent_color(palette, state):

    reordered = " -- ".join(sorted(state.split(" -- ")))
    if state in palette:
        return palette[state]
    if reordered in palette:
        return palette[reordered]
    if state == "Others":
        color = "lightgray"
    else:
        count = len(palette)
        if "Others" not in palette:
            count += 1
        color = "C%d" % (count % 10)
    palette[state] = color
    palette[reordered] = color
    return color

def register_states_for_color(palette, collection):
    [persistent_color(palette, state) for state in collection]

def make_plot_trajectory(time_table, ax, palette, legend=True, error_table=None):
    register_states_for_color(palette, time_table.columns.values)
    color_list = [persistent_color(palette, idx) \
                    for idx in time_table.columns.values]
    time_table.plot(ax=ax, color=color_list, legend=legend, yerr=error_table)
    if legend:
        plt.legend(loc='upper right')


def plot_node_prob(time_table, ax, palette, legend=True, error_table=None):
    """Plot the probability of each node being up over time."""
    register_states_for_color(palette, time_table.columns.values)
    color_list = [persistent_color(palette, idx) \
                    for idx in time_table.columns.values]
    time_table.plot(ax=ax, color=color_list, legend=legend, yerr=error_table)
    if legend:
        plt.legend(loc='upper right')


def plot_piechart(plot_table, ax, palette, embed_labels=False, autopct=4, \
                    prob_cutoff=0.01):
    plot_line = plot_table.iloc[-1].rename("")  # Takes the last time point

    others = plot_line[plot_line <= prob_cutoff].sum()

    plot_line = plot_line[plot_line > prob_cutoff]
    plot_line.sort_values(ascending=False, inplace=True)

    if others:
        plot_line.at["Others"] = others

    register_states_for_color(palette, plot_line.index)

    plotting_labels = []
    color_list = []
    for value_index, value in enumerate(plot_line):
        state = plot_line.index.values[value_index]
        color_list.append(persistent_color(palette, state))
        if embed_labels and value >= 0.1:
            plotting_labels.append(state)
        else:
            plotting_labels.append("")

    opts = {}
    if autopct:
        cutoff = autopct if type(autopct) is not bool else 4
        opts.update(autopct=lambda p: '%1.1f%%' % p if p >= cutoff else "")
    else:
        opts.update(labeldistance=0.4)

    if others:
        plot_line = plot_line.rename({"Others": "Others (%1.2f%%)" % (others*100)})

    ax.pie(plot_line, labels=plotting_labels, radius=1.2,
           startangle=90, colors=color_list, **opts)
    ax.axis('equal')
    ax.legend(plot_line.index.values, loc=(0.9, 0.2))


def plot_fix_point(table, ax, palette):
    """Plot a piechart representing the fixed point probability."""
    palette['no_fp'] = '#121212'
    prob_list = []
    color_list = []
    labels = []
    for i in range(len(table)):
        prob = table['Proba'][i]
        state = table['State'][i]
        prob_list.append(prob)
        color_list.append(persistent_color(palette, state))
        labels.append('FP '+str(i+1))
    prob_ns = 1 - sum(prob_list)
    if prob_ns > 0.01:
        prob_list.append(prob_ns)
        color_list.append(persistent_color(palette, "no_fp"))
        labels.append('no_fp')
    ax.pie(prob_list, labels=labels, colors=color_list)



