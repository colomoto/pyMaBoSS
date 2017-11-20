"""Tools to draw figures from the MaBoSS results."""


import pandas as pd
import matplotlib.pylab as plt
import numpy as np


def get_states(df):
    cols = list(filter(lambda s: s.startswith("State"), df.columns))
    states = set()
    for i in df.index:
        for c in cols:
            if type(df[c][i]) is str:  # Otherwise it is nan
                states.add(df[c][i])
    return states


def make_plot_table(df):
    """Creates a table giving the probablilty of each state a every moment.

        The rows are indexed by time points and the columns are indexed by
        state name.
    """
    states = get_states(df)
    nb_sates = len(states)
    time_points = np.asarray(df['Time'])
    time_table = pd.DataFrame(np.zeros((len(time_points), nb_sates)),
                              index=time_points, columns=states)

    cols = list(filter(lambda s: s.startswith("State"), df.columns))
    for i in df.index:
        tp = df["Time"][i]
        for c in cols:
            prob_col = c.replace("State", "Proba")
            if type(df[c][i]) is str:  # Otherwise it is nan
                state = df[c][i]
                time_table[state][tp] = df[prob_col][i]

    return time_table


def make_plot_trajectory(prefix, ax):
    table_file = "{}_probtraj.csv".format(prefix)
    df = pd.read_csv(table_file, "\t")
    time_table = make_plot_table(df)

    time_table.plot(ax=ax)


def make_trajectory(prefix):
    table_file = "{}_probtraj.csv".format(prefix)
    table = pd.read_csv(table_file, "\t")
    plot_table = make_plot_table(table)
    plot_table.plot()
    plt.legend(loc='best')
    plt.show()


def plot_piechart(prefix, ax):
    table_file = "{}_probtraj.csv".format(prefix)
    table = pd.read_csv(table_file, "\t")
    plot_table = make_plot_table(table)
    plot_line = plot_table.iloc[-1].rename("")  # Takes the last time point
    plot_line = plot_line[plot_line > 0.01]
    plotting_labels = []
    legend_labels = []
    for value_index, value in enumerate(plot_line):
        if value >= 0.1:
            plotting_labels.append(plot_line.index.values[value_index])
        else:
            plotting_labels.append("")
    ax.pie(plot_line, labels=plotting_labels, radius=1.2, labeldistance=0.4,
           startangle=90)
    ax.legend(plot_line.index.values, loc=(0.9, 0.8), fontsize=8)
