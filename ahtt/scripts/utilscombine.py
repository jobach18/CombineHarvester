#!/usr/bin/env python
# utilities containing functions used throughout - combine file

import glob
import os
import sys

from desalinator import remove_quotes, remove_spaces, tokenize_to_list, clamp_with_quote
from utilspy import syscall, right_now

from ROOT import TFile, gDirectory, TH1, TH1D
TH1.AddDirectory(False)
TH1.SetDefaultSumw2(True)

min_g = 0.
max_g = 3.

def problematic_datacard_log(logfile):
    if not hasattr(problematic_datacard_log, "problems"):
        problematic_datacard_log.problems = [
            r"'up/down templates vary the yield in the same direction'",
            r"'up/down templates are identical'",
            r"'At least one of the up/down systematic uncertainty templates is empty'",
            r"'Empty process'",
            r"'Bins of the template empty in background'",
        ]

    with open(logfile) as lf:
        for line in lf:
            for problem in problematic_datacard_log.problems:
                if problem in line and 'no warnings' not in line:
                    lf.close()
                    return True
        lf.close()
    return False

def set_range(parameters):
    '''
    given a list of parameters, return the set of combine setting their ranges
    parameter is a string in the following syntax: name[: min, max]
    where the range in the square bracket is optional
    when the range is not given, it defaults to -20, 20
    '''
    parameters = ['='.join(remove_spaces(param).split(':')) if ':' in param else param + '=-20,20' for param in parameters]
    return "--setParameterRanges '{ranges}'".format(ranges = ':'.join(parameters))

def set_parameter(set_freeze, extopt, masks):
    '''
    problem is, setparameters and freezeparameters may appear only once
    so --extra-option is not usable to study shifting them up if we set g etc
    this method harmonizes the set/freezeParameter options and ignore all others
    '''
    setpar = list(set_freeze[0])
    frzpar = [par for par in set_freeze[1] if "__grp__" not in par]
    grppar = [par.replace("__grp__", "") for par in set_freeze[1] if "__grp__" in par]

    extopt = [] if extopt == "" else extopt.split(' ')
    for option in ['--setParameters', '--freezeParameters', '--freezeNuisanceGroups']:
        while option in extopt:
            iopt = extopt.index(option)
            parameters = tokenize_to_list(remove_quotes(extopt.pop(iopt + 1))) if iopt + 1 < len(extopt) else []
            extopt.pop(iopt)
            if option == '--setParameters':
                setpar += parameters
            elif option == '--freezeParameters':
                frzpar += parameters
            elif option == '--freezeNuisanceGroups':
                grppar += parameters

    return '{stp} {frz} {grp}'.format(
        stp = "--setParameters '" + ",".join(setpar + masks) + "'" if len(setpar + masks) > 0 else "",
        frz = "--freezeParameters '" + ",".join(frzpar) + "'" if len(frzpar) > 0 else "",
        grp = "--freezeNuisanceGroups '" + ",".join(grppar) + "'" if len(grppar) > 0 else ""
    )

def nonparametric_option(extopt):
    '''
    removes the parametric part of extopt, and returns the rest as one option string to be passed to combine
    '''
    if extopt == "":
        return ""

    extopt = extopt.split(' ')
    for option in ['--setParameters', '--freezeParameters', "--freezeNuisanceGroups"]:
        while option in extopt:
            iopt = extopt.index(option)
            parameters = tokenize_to_list(remove_quotes(extopt.pop(iopt + 1))) if iopt + 1 < len(extopt) else []
            extopt.pop(iopt)

    return " ".join(extopt)

def get_best_fit(dcdir, point, tags, usedefault, useexisting, default, asimov, modifier, scenario, ranges, set_freeze, extopt = "", masks = []):
    ptag = lambda pnt, tag: "{pnt}{tag}".format(pnt = point, tag = tag)

    if usedefault:
        return default
    elif useexisting:
        workspace = glob.glob("{dcd}{ptg}_best-fit_{asm}*{mod}.root".format(
            dcd = dcdir,
            ptg = ptag(point, tags[0]),
            asm = "exp" if asimov else "obs",
            mod = "_" + modifier if modifier != "" else "",
        ))

        if len(workspace) == 0 or not os.path.isfile(workspace[0]):
            # try again, but using tag instead of otag
            workspace = glob.glob("{dcd}{ptg}_best-fit_{asm}*{mod}.root".format(
                dcd = dcdir,
                ptg = ptag(point, tags[1]),
                asm = "exp" if asimov else "obs",
                mod = "_" + modifier if modifier != "" else "",
            ))

        if len(workspace) and os.path.isfile(workspace[0]):
            return workspace[0]
        else:
            useexisting = False

    if not usedefault and not useexisting:
        # ok there really isnt a best fit file, make them
        print "\nxxx_point_ahtt :: making best fits"
        for asm in [not asimov, asimov]:
            workspace = make_best_fit(dcdir, default, point, asm, ranges, set_freeze, extopt, masks)
            syscall("rm robustHesse_*.root", False, True)

            newname = "{dcd}{ptg}_best-fit_{asm}{sce}{mod}.root".format(
                dcd = dcdir,
                ptg = ptag(point, tags[0]),
                asm = "exp" if asm else "obs",
                sce = "_" + scenario if scenario != "" else "",
                mod = "_" + modifier if modifier != "" else "",
            )
            syscall("mv {wsp} {nwn}".format(wsp = workspace, nwn = newname), False)
            workspace = newname
    return workspace

def starting_nuisance(freeze_zero, freeze_post):
    set_freeze = [[], []]
    setp, frzp = set_freeze

    for frz in freeze_zero | freeze_post:
        if frz in ["autoMCStats", "mcstat"]:
            param = r"rgx{prop_bin.*}"
        elif frz in ["experiment", "theory", "norm", "expth"]:
            param = "__grp__{frz}".format(frz = frz)
        else:
            param = frz

        # --setNuisanceGroups xxx=0 ain't a thing
        if frz in freeze_zero and "__grp__" not in param:
            setp.append("{param}=0".format(param = param))
        frzp.append("{param}".format(param = param))

    return set_freeze

def fit_strategy(strategy, optimize = True, robust = False, use_hesse = False, tolerance = 0):
    fstr = "--X-rtd OPTIMIZE_BOUNDS=0 --X-rtd MINIMIZER_MaxCalls=9999999"
    if optimize:
        fstr += " --X-rtd FAST_VERTICAL_MORPH --X-rtd CACHINGPDF_NOCLONE"
    fstr += " --cminPreScan --cminDefaultMinimizerAlgo Combined --cminDefaultMinimizerStrategy {ss} --cminFallbackAlgo GSLMultiMin,BFGS2,{ss}".format(ss = strategy)
    fstr += ":{tol} --cminDefaultMinimizerTolerance {tol}".format(tol = 2.**(tolerance - 4))

    if robust:
        fstr += " --robustFit 1 --setRobustFitAlgo Minuit2 --maxFailedSteps 9999999 --setRobustFitStrategy {ss} {t0} {t1} {t2} {hh}".format(
            ss = strategy,
            t0 = "--setRobustFitTolerance {tol}".format(tol = 2.**(tolerance - 4)),
            t1 = "--stepSize {tol}".format(tol = 2.**(tolerance - 4)),
            t2 = "--setCrossingTolerance {tol}".format(tol = 2.**(tolerance - 12)),
            hh = "--robustHesse 1" if use_hesse else ""
        )
    return fstr

def is_good_fit(fit_fname, fit_names):
    '''
    checks if fit is good
    fit_fname is the filename of the file containing buncha RooFitResults to be checked
    fit_names is an iterable containing the names of said RooFitResults
    returns True if all fit_names are good, otherwise False
    '''
    ffile = TFile.Open(fit_fname, "read")
    fgood = []
    for fname in fit_names:
        fresult = ffile.Get("{fname}".format(fname = fname))
        fit_quality = fit_result.covQual()
        print "\nxxx_point_ahtt :: fit with name {fname} has a covariance matrix of status {fql}".format(fname = fname, fql = fit_quality)
        sys.stdout.flush()
        fgood.append(fit_quality != 3)
    ffile.Close()

    all_good = all(fgood)
    if not all_good:
        syscall("rm {ffn}".format(ffn = fit_fname), False, True)
        print "xxx_point_ahtt :: one of the matrices is bad."
        sys.stdout.flush()

    return all_good

def never_gonna_give_you_up(command, optimize = True, followups = [], fit_result_names = None, post_conditions = [], failure_cleanups = [],
                            usehesse = False, robustness = [True, False], strategies = list(range(3)), tolerances = list(range(2)),
                            throw_upon_failure = True):
    '''
    run fits with multiple settings until one works
    command: command to run. should contain a {strategy} in there to be substituted in

    optimize is just an extra flag for fit strategy, due to prepost needing it to be False, and elsewhere True

    followups: a list of lists where each inner list is the function to run
    and arguments to be passed to it

    fit_result_names: a list where first element is the name of the file containing the fit result,
    and the second the list of fit result names to run is_good_fit() on. pass None to skip running it

    post_condition: like followups, but said function should return a truthy value

    fit is accepted if is_good_fit and all of post_conditions are true

    failure_cleanups has the same syntax as post_conditions, but the functions do not need to return a truthy value
    they are steps to be run when a fit is not accepted

    the function throws if no fit is accepted
    '''
    all_strategies = [(irobust, istrat, itol) for irobust in robustness for istrat in strategies for itol in tolerances]
    for irobust, istrat, itol in all_strategies:
        if usehesse and not irobust:
            continue
        robusthesse = irobust and usehesse

        syscall(command.format(
            fit_strategy = fit_strategy(strategy = istrat, robust = irobust, use_hesse = robusthesse, tolerance = itol, optimize = optimize),
        ))

        for fu in followups:
            fu[0](*fu[1:])

        fgood = True if fit_result_names is None or robusthesse else is_good_fit(*fit_result_names)
        pgood = all([pc[0](*pc[1:]) for pc in post_conditions])

        if robusthesse:
            syscall("rm robustHesse_*.root", False, True)

        if fgood and pgood:
            return None
        else:
            for fc in failure_cleanups:
                fc[0](*fc[1:])

    print "\nnever_gonna_give_you_up :: no accepted fit found. argument and state variables:"
    print locals()
    print "\n\n"
    sys.stdout.flush()
    if throw_upon_failure:
        raise RuntimeError("never_gonna_give_you_up :: unfortunately, with this set, the function has to give up...")

def make_best_fit(dcdir, workspace, point, asimov, ranges, set_freeze, extopt = "", masks = []):
    fname = point + "_best_fit_" + right_now()
    never_gonna_give_you_up(
        command = "combineTool.py -v 0 -M MultiDimFit -d {dcd} -n _{bff} {stg} {prg} {asm} {wsp} {prm} {ext}".format(
            dcd = workspace,
            bff = fname,
            stg = "{fit_strategy}",
            prg = ranges,
            asm = "-t -1" if asimov else "",
            wsp = "--saveWorkspace --saveSpecifiedNuis=all --saveNLL",
            prm = set_parameter(set_freeze, extopt, masks),
            ext = nonparametric_option(extopt)
        ),

        failure_followups = [
            [syscall, "rm higgsCombine*{bff}.MultiDimFit*.root".format(bff = fname), False]
        ]
    )
    syscall("mv higgsCombine*{bff}.MultiDimFit*.root {dcd}{bff}.root".format(dcd = dcdir, bff = fname), False)
    return "{dcd}{bff}.root".format(dcd = dcdir, bff = fname)

def make_datacard_with_args(scriptdir, args):
    syscall("{scr}/make_datacard.py --signal {sig} --background {bkg} --point {pnt} --channel {ch} --year {yr} "
            "{psd} {inj} {ass} {exc} {tag} {drp} {kee} {kfc} {thr} {lns} {shp} {mcs} {rpr} {igb} {prj} {cho} {rep} {rsd}".format(
                scr = scriptdir,
                pnt = ','.join(args.point),
                sig = args.signal,
                bkg = args.background,
                ch = args.channel,
                yr = args.year,
                psd = "--add-pseudodata" if args.asimov else "",
                inj = clamp_with_quote(string = args.inject, prefix = '--inject-signal '),
                ass = clamp_with_quote(string = args.assignal, prefix = '--as-signal '),
                exc = clamp_with_quote(string = args.excludeproc, prefix = '--exclude-process '),
                tag = clamp_with_quote(string = args.tag, prefix = '--tag '),
                drp = clamp_with_quote(string = args.drop, prefix = '--drop '),
                kee = clamp_with_quote(string = args.keep, prefix = '--keep '),
                kfc = "--sushi-kfactor" if args.kfactor else "",
                thr = clamp_with_quote(string = args.threshold, prefix = '--threshold '),
                lns = "--lnN-under-threshold" if args.lnNsmall else "",
                shp = "--use-shape-always" if args.alwaysshape else "",
                mcs = "--no-mc-stats" if not args.mcstat else "",
                rpr = clamp_with_quote(string = args.rateparam, prefix = '--float-rate '),
                msk = clamp_with_quote(string = ','.join(args.mask), prefix = '--mask '),
                igb = clamp_with_quote(string = args.ignorebin, prefix = '--ignore-bin '),
                prj = clamp_with_quote(string = args.projection, prefix = '--projection '),
                cho = clamp_with_quote(string = args.chop, prefix = '--chop-up '),
                rep = clamp_with_quote(string = args.repnom, prefix = '--replace-nominal '),
                rsd = clamp_with_quote(string = args.seed, prefix = '--seed '),
            ))

def update_mask(masks):
    new_masks = []
    for mask in masks:
        channel, year = mask.split("_")
        if channel == "lx":
            channels = ["ee", "em", "mm", "e3j", "e4pj", "m3j", "m4pj"]
        elif channel == "ll":
            channels = ["ee", "em", "mm"]
        elif channel == "sf":
            channels = ["ee", "mm"]
        elif channel == "lj":
            channels = ["e3j", "e4pj", "m3j", "m4pj"]
        elif channel == "l3j":
            channels = ["e3j", "m3j"]
        elif channel == "l4pj":
            channels = ["e4pj", "m4pj"]
        elif channel == "ej":
            channels = ["e3j", "e4pj"]
        elif channel == "mj":
            channels = ["m3j", "m4pj"]
        else:
            channels = [channel]

        if year == "all" or year == "run2":
            years = ["2016pre", "2016post", "2017", "2018"]
        elif year == "2016":
            years = ["2016pre", "2016post"]
        else:
            years = [year]

        for cc in channels:
            for yy in years:
                new_masks.append(cc + "_" + yy)

    return list(set(new_masks))
