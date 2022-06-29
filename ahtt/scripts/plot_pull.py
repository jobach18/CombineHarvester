#!/usr/bin/env python3
# draw the model-independent limit on gAH plot
# requires matplotlib > 3.3 e.g. source /cvmfs/sft.cern.ch/lcg/views/setupViews.sh LCG_100 x86_64-centos7-gcc10-opt

from argparse import ArgumentParser
import os
import sys
import numpy as np
import math

import glob
from collections import OrderedDict
import json
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.legend_handler import HandlerErrorbar

nuisance_per_page = 30
axes = {
    "mass" :    r"m$_{\mathrm{\mathsf{%s}}}$ [GeV]",
    "width":    r"$\Gamma_{\mathrm{\mathsf{%s}}}$ [\%% m$_{\mathrm{\mathsf{%s}}}$]",
    "coupling": r"g$_{\mathrm{\mathsf{%s}}}$"
}

first  = lambda vv: [i for i, _ in vv]
second = lambda vv: [i for _, i in vv]

def get_point(sigpnt):
    pnt = sigpnt.split('_')
    return (pnt[0][0], float(pnt[1][1:]), float(pnt[2][1:].replace('p', '.')))

def read_pull(directories, onepoi):
    pulls = [OrderedDict() for dd in directories]
    for ii, dd in enumerate(directories):
        with open("{dd}/{pnt}_impacts_{mod}.json".format(dd = dd, pnt = '_'.join(dd.split('_')[:3]), mod = "one-poi" if onepoi else "g-scan")) as ff:
            result = json.load(ff)

        nuisances = result["params"]
        for nn in nuisances:
            if nn["name"] != "g":
                pulls[ii][nn["name"]] = nn["fit"]

    return pulls

def plot_pull(oname, labels, pulls, nuisances, extra, point, reverse, transparent, plotformat):
    fig, ax = plt.subplots()
    xval = [np.zeros(nuisance_per_page) for pp in pulls]
    yval = [np.zeros(nuisance_per_page) for pp in pulls]
    err = [np.zeros((2, nuisance_per_page)) for pp in pulls]

    offset = [0.2, -0.2] if len(pulls) == 2 else [0.]
    colors = ["#cc0033", "#0033cc"] if len(pulls) == 2 else ["black"]
    markers = ["o", "s"] if len(pulls) == 2 else ["o"]
    counter = math.ceil(len(nuisances) / nuisance_per_page) - 1 # not floor, because that doesn't give 0, 1, 2, ... for integer multiples

    if reverse:
        nuisances = list(reversed(nuisances))

    for ii, nn in enumerate(nuisances):
        for jj in range(len(pulls)):
            xval[jj][ii % nuisance_per_page] = pulls[jj][nn][1] if nn in pulls[jj] else 0.

            err[jj][0, ii % nuisance_per_page] = pulls[jj][nn][1] - pulls[jj][nn][0] if nn in pulls[jj] else 0.
            err[jj][1, ii % nuisance_per_page] = pulls[jj][nn][2] - pulls[jj][nn][1] if nn in pulls[jj] else 0.

            yval[jj][ii % nuisance_per_page] = (ii % nuisance_per_page) + offset[jj]

        if ii % nuisance_per_page == nuisance_per_page - 1 or ii == len(nuisances) - 1:
            ymax = (ii % nuisance_per_page) + 1 if ii == len(nuisances) - 1 else nuisance_per_page

            ax.fill_between(np.array([-1, 1]), np.array([-0.5, -0.5]), np.array([ymax - 0.5, ymax - 0.5]), color = "silver", linewidth = 0)

            plots = []
            for jj in range(len(pulls)):
                plots.append(ax.errorbar(xval[jj][:ymax], yval[jj][:ymax], xerr = err[jj][0:, :ymax], ls = "none", elinewidth = 1.5,
                                         marker = markers[jj], ms = 5, capsize = 5, color = colors[jj], label = labels[jj]))

            ax.set_yticks([kk for kk in range(ymax)])
            ax.set_yticklabels(nuisances[ii - ymax + 1 : ii + 1] + r"$\,$")
            plt.xlabel(point[0] + '(' + str(int(point[1])) + ", " + str(point[2]) + "%) nuisance pulls", fontsize = 21, labelpad = 10)
            ax.margins(x = 0, y = 0)
            plt.xlim((-1.5, 1.5))
            plt.ylim((-0.5, ymax - 0.5))

            if len(pulls) == 2:
                legend = ax.legend(loc = "lower left", ncol = len(pulls), bbox_to_anchor = (0.05, 1.005, 0.9, 0.01),
                                   mode = "expand", borderaxespad = 0., handletextpad = 1.5, fontsize = 15, frameon = False,
                                   handler_map = {plots[0]: HandlerErrorbar(xerr_size = 1.5), plots[1]: HandlerErrorbar(xerr_size = 1.5)})

            ax.minorticks_on()
            ax.tick_params(axis = "both", which = "both", direction = "in", bottom = True, top = True, left = True, right = True)
            ax.tick_params(axis = "x", which = "major", width = 1, length = 8, labelsize = 18)
            ax.tick_params(axis = "y", which = "major", width = 1, length = 8, labelsize = 14)
            ax.tick_params(axis = "x", which = "minor", width = 1, length = 3)
            ax.tick_params(axis = "y", which = "minor", width = 0, length = 0)

            fig.set_size_inches(9., 16.)
            fig.tight_layout()
            if len(pulls) == 2:
                fig.savefig(oname + extra + str(counter) + plotformat, bbox_extra_artists = (legend,), transparent = transparent)
            else:
                fig.savefig(oname + extra + str(counter) + plotformat, transparent = transparent)
            fig.clf()

            fig, ax = plt.subplots()
            counter = counter - 1

def draw_pull(oname, directories, labels, onepoi, mcstat, transparent, plotformat):
    pulls = read_pull(directories, onepoi)
    point = get_point('_'.join(directories[0].split('_')[:3]))

    expth = []
    for pull in pulls:
        for nn in pull.keys():
            if "prop_bin" not in nn:
                expth.append(nn)
    plot_pull(oname, labels, pulls, sorted(list(set(expth))), "_expth_", point, True, transparent, plotformat)

    if mcstat:
        stat = []
        for pull in pulls:
            for nn in pull.keys():
                if "prop_bin" in nn:
                    stat.append(nn)
        plot_pull(oname, labels, pulls, sorted(list(set(stat))), "_stat_", point, True, transparent, plotformat)

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("--point", help = "signal point to plot the pulls of", default = "", required = True)
    parser.add_argument("--itag", help = "input directory tags to plot pulls of, semicolon separated", default = "", required = False)
    parser.add_argument("--otag", help = "extra tag to append to plot names", default = "", required = False)
    parser.add_argument("--odir", help = "output directory to dump plots in", default = ".", required = False)
    parser.add_argument("--label", help = "labels to attach on plot for each input tags, semicolon separated", default = "Pulls", required = False)
    parser.add_argument("--one-poi", help = "plot pulls obtained with the g-only model", dest = "onepoi", action = "store_true", required = False)
    parser.add_argument("--no-mc-stats", help = "don't consider nuisances due to limited mc stats (barlow-beeston lite)",
                        dest = "mcstat", action = "store_false", required = False)
    parser.add_argument("--transparent-background", help = "make the background transparent instead of white",
                        dest = "transparent", action = "store_true", required = False)
    parser.add_argument("--plot-format", help = "format to save the plots in", default = "pdf", dest = "fmt", required = False)

    args = parser.parse_args()
    if (args.otag != "" and not args.otag.startswith("_")):
        args.otag = "_" + args.otag

    if (args.fmt != "" and not args.fmt.startswith(".")):
        args.fmt = "." + args.fmt

    tags = args.itag.replace(" ", "").split(';')
    labels = args.label.split(';')

    if len(tags) != len(labels):
        raise RuntimeError("length of tags isnt the same as labels. aborting")

    dirs = [args.point + '_' + tag for tag in tags]
    draw_pull(args.odir + "/" + args.point + "_pull" + args.otag, dirs, labels, args.onepoi, args.mcstat, args.transparent, args.fmt)

    pass