#!/usr/bin/env python
# merge the pull jsons for use by HIG-style plotImpacts.py

from argparse import ArgumentParser
import os
import sys

import glob
from collections import OrderedDict
import json

from desalinator import prepend_if_not_empty, tokenize_to_list, remove_spaces_quotes

def dump_pull(directories, onepoi, gvalue, rvalue, fixpoi):
    for directory, tag in directories:
        pulls = OrderedDict()
        impacts = glob.glob("{dcd}/{pnt}_{tag}_impacts_{mod}{gvl}{rvl}{fix}*.json".format(
            dcd = directory,
            tag = tag,
            pnt = '_'.join(directory.split('_')[:3]),
            mod = "one-poi" if onepoi else "g-scan",
            gvl = "_g_" + str(gvalue).replace(".", "p") if gvalue >= 0. else "",
            rvl = "_r_" + str(rvalue).replace(".", "p") if rvalue >= 0. and not onepoi else "",
            fix = "_fixed" if fixpoi and (gvalue >= 0. or rvalue >= 0.) else "",
        ))

        for ii, imp in enumerate(impacts):
            print("merge_pull :: opening file " + imp)
            with open(imp) as ff:
                result = json.load(ff)

            if ii == 0:
                pulls["POIs"] = result["POIs"]
                pulls["method"] = result["method"]
                pulls["params"] = result["params"]
            else:
                if pulls["POIs"] != result["POIs"]:
                    print("merge_pull :: WARNING :: incompatible POI best fit between input jsons!!")

                pulls["params"] += result["params"]

        with open("{dcd}/{pnt}_{tag}_impacts_{mod}{gvl}{rvl}{fix}_all.json".format(
                dcd = directory,
                tag = tag,
                pnt = '_'.join(directory.split('_')[:3]),
                mod = "one-poi" if onepoi else "g-scan",
                gvl = "_g_" + str(gvalue).replace(".", "p") if gvalue >= 0. else "",
                rvl = "_r_" + str(rvalue).replace(".", "p") if rvalue >= 0. and not onepoi else "",
                fix = "_fixed" if fixpoi and (gvalue >= 0. or rvalue >= 0.) else "",
        ), "w") as jj:
            json.dump(pulls, jj, indent = 1)



if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("--point", help = "signal point to plot the pulls of", default = "", required = True, type = remove_spaces_quotes)
    parser.add_argument("--tag", help = "input tag-output-tag pairs to search. the pairs are semicolon separated, and tags colon-separated, "
                        "so e.g. when there are 2 tags: 't1:o1;t2:o2...", dest = "itag", default = "", required = False, type = lambda s: tokenize_to_list( remove_spaces_quotes(s), ';' ))
    parser.add_argument("--one-poi", help = "plot pulls obtained with the g-only model", dest = "onepoi", action = "store_true", required = False)

    parser.add_argument("--g-value",
                        help = "g to use when evaluating impacts/fit diagnostics/nll. "
                        "does NOT freeze the value, unless --fix-poi is also used. "
                        "note: semantically sets value of 'r' with --one-poi, as despite the name it plays the role of g.",
                        dest = "setg", default = "-1.", required = False, type = lambda s: float(remove_spaces_quotes(s)))
    parser.add_argument("--r-value",
                        help = "r to use when evaluating impacts/fit diagnostics/nll, if --one-poi is not used."
                        "does NOT freeze the value, unless --fix-poi is also used.",
                        dest = "setr", default = "-1.", required = False, type = lambda s: float(remove_spaces_quotes(s)))
    parser.add_argument("--fix-poi", help = "fix pois in the fit, through --g-value and/or --r-value",
                        dest = "fixpoi", action = "store_true", required = False)

    args = parser.parse_args()
    dirs = [[[args.point + '_' + tag.split(':')[0]], tag.split(':')[1] if len(tag.split(':')) > 1 else tag.split(':')[0]] for tag in args.itag]
    dump_pull(dirs, args.onepoi, args.setg, args.setr, args.fixpoi)
