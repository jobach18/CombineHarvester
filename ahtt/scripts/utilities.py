#!/usr/bin/env python
# utilities containing functions to be imported
# as dumping everything into make_datacard is becoming unreadable

import os
import sys
import math
import fnmatch
import platform

from datetime import datetime
from collections import OrderedDict
from desalinator import remove_quotes, tokenize_to_list

from ROOT import TFile, gDirectory, TH1, TH1D
TH1.AddDirectory(False)
TH1.SetDefaultSumw2(True)

from numpy import random as rng

min_g = 0.
max_g = 3.

cluster = None
if "desy" in platform.node():
    cluster = "naf"
elif "cern" in platform.node():
    cluster = "lxplus"
else:
    raise NotImplementedError("unknown cluster! can't provide a default input storage base!")

def input_storage_base_directory():
    if cluster == "naf":
        return "/nfs/dust/cms/group/exotica-desy/HeavyHiggs/"
    if cluster == "lxplus":
        return "/eos/cms/store/user/afiqaize/"

input_base = input_storage_base_directory()
condordir = "/nfs/dust/cms/user/afiqaize/cms/sft/condor/" if "desy" in input_base else "/afs/cern.ch/work/a/afiqaize/public/randomThings/misc/condor/"
condorsub = condordir + "condorSubmit.sh"
condorpar = condordir + "condorParam.txt" if "desy" in input_base else condordir + "condorParam_lxpCombine.txt"
condorrun = condordir + "condorRun.sh" if "desy" in input_base else condordir + "condorRun_lxpCombine.sh"

kfactor_file_name = {
    171: input_base + "ahtt_kfactor_sushi/ulkfactor_final_mt171p5_230329.root",
    172: input_base + "ahtt_kfactor_sushi/ulkfactor_final_220129.root",
    173: input_base + "ahtt_kfactor_sushi/ulkfactor_final_mt173p5_230329.root"
}

def make_submission_script_header():
    script = "Job_Proc_ID = $(Process) + 1 \n"
    script += "executable = {script}\n".format(script=condorrun)
    script += "notification = error\n"
    script += 'requirements = (OpSysAndVer == "CentOS7")\n'

    if cluster == "naf":
        script += "universe = vanilla\n"
        script += "getenv = true\n"
        script += 'environment = "LD_LIB_PATH={ldpath} JOB_PROC_ID=$INT(Job_Proc_ID)"\n'.format(ldpath=os.getenv('LD_LIBRARY_PATH'))

    elif cluster == "lxplus":
        script += 'environment = "cmssw_base={cmssw} JOB_PROC_ID=$INT(Job_Proc_ID)"\n'.format(cmssw=os.getenv('CMSSW_BASE'))

        # Afiq's Special Treatment
        if os.getlogin() == 'afiqaize':
            grp = 'group_u_CMST3.all' if rng.binomial(1, 0.5) else 'group_u_CMS.u_zh.users'
            script += '+AccountingGroup = "{grp}"\n'.format(grp=grp)

    script += "\n"

    return script
    
def make_submission_script_single(name, directory, executable, arguments, cpus = None, runtime = None, memory = None, runtmp = False):
    script = """
batch_name = {name}
output = {directory}/{name}.o$(Cluster).$INT(Job_Proc_ID)
error = {directory}/{name}.o$(Cluster).$INT(Job_Proc_ID)
arguments = {executable} {args}
"""

    script = script.format(name = name, directory = directory, executable = executable, args = ' '.join(arguments.split()))
    if cpus is not None and cpus != "" and cpus > 1:
        script += "request_cpus = {cpus}\n".format(cpus = cpus)

    if memory is not None and memory != "":
        script += "RequestMemory = {memory}\n".format(memory = memory)

    if runtime is not None and runtime != "":
        script += "+RequestRuntime = {runtime}\n".format(runtime = runtime)

    if runtmp or cluster == "lxplus":
        script += "should_transfer_files = YES\n"
        script += "when_to_transfer_output = ON_EXIT_OR_EVICT\n"
    else:
        script += "initialdir = {cwd}\n".format(cwd = os.getcwd())

    if cluster == "lxplus":
        script += 'transfer_output_files = tmp/\n'
        script += '+MaxRuntime = {runtime}\n'.format(runtime = runtime)

    script += "queue\n\n"
    return script

def syscall(cmd, verbose = True, nothrow = False):
    if verbose:
        print ("Executing: %s" % cmd)
        sys.stdout.flush()
    retval = os.system(cmd)
    if not nothrow and retval != 0:
        raise RuntimeError("Command failed with exit code {ret}!".format(ret = retval))

def get_point(sigpnt):
    pnt = sigpnt.split('_')
    return (pnt[0][0], float(pnt[1][1:]), float(pnt[2][1:].replace('p', '.')))

def stringify(gtuple):
    return str(gtuple)[1: -1]

def tuplize(gstring):
    return tuple([float(gg) for gg in gstring.replace(" ", "").split(",")])

def right_now():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")

def flat_reldev_wrt_nominal(varied, nominal, offset):
    for ii in range(1, nominal.GetNbinsX() + 1):
        nn = nominal.GetBinContent(ii)
        varied.SetBinContent(ii, nn * (1. + offset))

def scale(histogram, factor, epsilon = 1e-3):
    if abs(factor - 1.) < epsilon:
        return

    for ii in range(1, histogram.GetNbinsX() + 1):
        histogram.SetBinContent(ii, histogram.GetBinContent(ii) * factor)
        histogram.SetBinError(ii, histogram.GetBinError(ii) * abs(factor))

def zero_out(histogram):
    for ii in range(1, histogram.GetNbinsX() + 1):
        if histogram.GetBinContent(ii) < 0.:
            histogram.SetBinContent(ii, 0.)
            histogram.SetBinError(ii, 0.)

# translate nD bin index to unrolled 1D
def index_n1(idxn, nbins):
    idx1 = idxn[0]
    for ii in range(1, len(idxn)):
        multiplier = 1
        for jj in range(ii - 1, -1, -1):
            multiplier *= nbins[jj]

        idx1 += idxn[ii] * multiplier

    return idx1

# and the inverse operation
def index_1d_1n(idx1, dim, nbins):
    multiplier = 1
    for dd in range(dim - 1, -1, -1):
        multiplier *= nbins[dd]

    return (idx1 // multiplier) % nbins[dim]

# as above, but over all dimensions in a go
def index_1n(idx1, nbins):
    idxn = [-1] * len(nbins)
    for iv in range(len(nbins)):
        idxn[iv] = index_1d_1n(idx1, iv, nbins)

    return idxn

def project(histogram, rule):
    src_nbin1 = histogram.GetNbinsX()
    src_nbinn = [int(bb) for bb in rule[0].split(',')]

    if len(src_nbinn) <= 1:
        print "aint nuthin to project for 1D histograms innit???"
        return histogram

    if reduce(lambda a, b: a * b, src_nbinn, 1) != src_nbin1:
        print "number of bins given in rule doesnt match the histogram. skipping projection."
        return histogram

    target = sorted([int(tt) for tt in rule[1].split(',')])
    if any([tt >= len(src_nbinn) or tt < 0 for tt in target]) or len(target) >= len(src_nbinn) or len(target) <= 0:
        print "target dimension indices not compatible with assumed dimensionality. skipping projection."
        return histogram

    tgt_nbinn = [src_nbinn[tt] for tt in target]
    tgt_nbin1 = reduce(lambda a, b: a * b, tgt_nbinn, 1)

    hname = histogram.GetName()
    histogram.SetName(hname + "_" + right_now())

    hist = TH1D(hname, histogram.GetTitle(), tgt_nbin1, 0., tgt_nbin1)
    for is1 in range(src_nbin1):
        isn = index_1n(is1, src_nbinn)
        src_content = histogram.GetBinContent(is1 + 1)
        src_error = histogram.GetBinError(is1 + 1)

        itn = [isn[ii] for ii in range(len(src_nbinn)) if ii in target]
        it1 = index_n1(itn, tgt_nbinn)

        tgt_content = hist.GetBinContent(it1 + 1)
        tgt_error = hist.GetBinError(it1 + 1)

        hist.SetBinContent(it1 + 1, tgt_content + src_content)
        hist.SetBinError(it1 + 1, math.sqrt(tgt_error**2 + src_error**2))

    return hist

def add_scaled_nuisance(varied, nominal, original, factor):
    added = varied.Clone(varied.GetName() + "_" + right_now())
    added.Add(original, -1.)
    scale(added, factor)
    added.Add(nominal)
    return added

def apply_relative_nuisance(varied, nominal, target):
    applied = varied.Clone(varied.GetName() + "_" + right_now())
    applied.Add(nominal, -1.)
    applied.Divide(nominal)
    applied.Multiply(target)
    applied.Add(target)
    return applied

def chop_up(varied, nominal, indices):
    chopped = varied.Clone(varied.GetName() + "_" + right_now())
    for ii in range(1, chopped.GetNbinsX() + 1):
        content = varied.GetBinContent(ii) if ii in indices else nominal.GetBinContent(ii)
        error = varied.GetBinError(ii) if ii in indices else nominal.GetBinError(ii)
        chopped.SetBinContent(ii, content)
        chopped.SetBinError(ii, error)
    return chopped

def get_nbin(fname, channel, year):
    hfile = TFile.Open(fname, "read")
    hfile.cd(channel + "_" + year)
    keys = gDirectory.GetListOfKeys()
    histogram = keys[0].ReadObj()
    nbin = histogram.GetNbinsX()
    hfile.Close()
    return nbin

def original_nominal_impl(hist = None, directory = None, process = None):
    # for saving the original nominal templates before manipulations (but after kfactors for signal)
    # to be used in some manipulations later
    if not hasattr(original_nominal_impl, "content"):
        original_nominal_impl.content = {}

    if directory is not None and process is not None:
        if hist is not None:
            if directory not in original_nominal_impl.content:
                original_nominal_impl.content[directory] = {}
            if process not in original_nominal_impl.content[directory]:
                original_nominal_impl.content[directory][process] = hist.Clone(hist.GetName() + "_original_no_bootleg_frfr")
                original_nominal_impl.content[directory][process].SetDirectory(0)
        else:
            hname = original_nominal_impl.content[directory][process].GetName().replace("_original_no_bootleg_frfr", "_") + right_now()
            return original_nominal_impl.content[directory][process].Clone(hname)

    return None

def add_original_nominal(hist, directory, process):
    return original_nominal_impl(hist, directory, process)

def read_original_nominal(directory, process):
    return original_nominal_impl(None, directory, process)

def chunks(lst, npart):
    '''
    split a list of length nlst into npart chunks of length ~nlst / npart
    FIXME: seems to not work very well when setting --impact-n < 3, which relies this method
    '''
    if npart > math.ceil(float(len(lst)) / 2) or npart < 1:
        print 'chunks called with a invalid npart. setting it to 2.'
        npart = 2

    nf = float(len(lst)) / npart
    nc = int(math.ceil(nf))
    ni = len(lst) / npart
    ii = 0
    result = []
    if nf - ni > 0.5:
        ni, nc = nc, ni
    result.append(lst[ii:ii + nc])
    ii += nc
    for i in xrange(ii, len(lst), ni):
        result.append(lst[i:i + ni])
    return result

def input_bkg(background, channels):
    # far be it for us to get in the way of those who know what they are doing
    if background != "":
        return background

    backgrounds = []
    if any(cc in channels for cc in ["ee", "em", "mm"]):
        backgrounds.append(input_base + "templates_ULFR2/breaktype3_mtAH_230314/ll/bkg_ll_3D-33_rate_mtuX_pca.root")
    if any(cc in channels for cc in ["e3j", "e4pj", "m3j", "m4pj"]):
        backgrounds.append(input_base + "templates_ULFR2/breaktype3_mtAH_230314/lj/templates_lj_bkg_rate_mtuX_pca.root")

    return ','.join(backgrounds)

def input_sig(signal, points, injects, channels, years):
    # far be it for us to get in the way of those who know what they are doing
    if signal != "":
        return signal

    signals = []
    masses = ["m" + str(im) for im in [365, 380] + range(400, 1001, 25)]
    for im in masses:
        if im in points or im in injects:
            if any(cc in channels for cc in ["ee", "em", "mm"]):
                signals.append(input_base + "templates_ULFR2/breaktype3_mtAH_230314/ll/sig_ll_3D-33_" + im + ".root")
            if any(cc in channels for cc in ["e3j", "e4pj", "m3j", "m4pj"]):
                signals.append(input_base + "templates_ULFR2/breaktype3_mtAH_230314/lj/templates_lj_sig_" + im + ".root")

    return ','.join(signals)

# Array to store all buffered submission scripts
current_submissions = []
max_jobs_per_submit = 4000

def aggregate_submit():
    return 'conSub_' + right_now() + '.txt'

def submit_job(job_agg, job_name, job_arg, job_time, job_cpu, job_mem, job_dir, executable, runtmp = False, runlocal = False):
    global current_submissions
    if not hasattr(submit_job, "firstjob"):
        submit_job.firstjob = True

    # figure out symlinks (similar to $(readlink))
    job_dir = os.path.realpath(job_dir)

    # for some reason this is given with the "-t" already in the python argument. workaround here for compability
    job_time = job_time.split("-t ")[1] if "-t " in job_time else job_time

    if runlocal:
        lname = "{log}.olocal.1".format(log = job_dir + '/' + job_name)
        syscall("touch {log}".format(log = lname), False)
        syscall('echo "Job execution starts at {atm}" |& tee -a {log}'.format(atm = datetime.now(), log = lname), False)
        syscall('{executable} {job_arg} |& tee -a {log}'.format(executable = executable, job_arg = job_arg, log = lname), True)
        syscall('echo "Job execution ends at {atm}" |& tee -a {log}'.format(atm = datetime.now(), log = lname), False)
    else:
        sub_script = make_submission_script_single(
            name = job_name,
            directory = job_dir,
            executable = executable,
            arguments = job_arg,
            cpus = job_cpu,
            runtime = job_time,
            memory = job_mem,
            runtmp = runtmp
        )

        if submit_job.firstjob:
            print("Submission script:")
            print(sub_script)
            sys.stdout.flush()
            submit_job.firstjob = False

        current_submissions.append(sub_script)

        if len(current_submissions) >= max_jobs_per_submit:
            flush_jobs(job_agg)

def flush_jobs(job_agg):
    global current_submissions
    if len(current_submissions) > 0:
        print("Submitting {njobs} jobs".format(njobs = len(current_submissions)))
        header = make_submission_script_header()
        script = header + "\n" + "\n".join(current_submissions)
        with open(job_agg, "w") as f:
            f.write(script)

        syscall("condor_submit {job_agg}".format(job_agg = job_agg), False)
        os.remove(job_agg)

        current_submissions = []
    else:
        print("Nothing to submit.")
        
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

# problem is, setparameters and freezeparameters may appear only once
# so --extra-option is not usable to study shifting them up if we set g etc
def set_parameter(set_freeze, extopt, masks):
    setpar = list(set_freeze[0])
    frzpar = list(set_freeze[1])

    extopt = [] if extopt == "" else extopt.split(' ')
    for option in ['--setParameters', '--freezeParameters']:
        while option in extopt:
            iopt = extopt.index(option)
            parameters = tokenize_to_list(remove_quotes(extopt.pop(iopt + 1))) if iopt + 1 < len(extopt) else []
            extopt.pop(iopt)
            if option == '--setParameters':
                setpar += parameters
            elif option == '--freezeParameters':
                frzpar += parameters

    return '{stp} {frz} {ext}'.format(
        stp = "--setParameters '" + ",".join(setpar + masks) + "'" if len(setpar + masks) > 0 else "",
        frz = "--freezeParameters '" + ",".join(frzpar) + "'" if len(frzpar) > 0 else "",
        ext = ' '.join(extopt)
    )

def make_best_fit(dcdir, card, point, asimov, strategy, poi_range, set_freeze, extopt = "", masks = []):
    fname = point + "_best_fit_" + right_now()

    syscall("combineTool.py -v -1 -M MultiDimFit -d {dcd} -n _{bff} {stg} {prg} {asm} {wsp} {prm}".format(
        dcd = dcdir + card,
        bff = fname,
        stg = strategy,
        prg = poi_range,
        asm = "-t -1" if asimov else "",
        wsp = "--saveWorkspace --saveSpecifiedNuis=all",
        prm = set_parameter(set_freeze, extopt, masks)
    ))
    syscall("mv higgsCombine*{bff}.MultiDimFit*.root {dcd}{bff}.root".format(dcd = dcdir, bff = fname), False)
    return "{dcd}{bff}.root".format(dcd = dcdir, bff = fname)

def read_nuisance(dname, points, qexp_eq_m1 = True):
    dfile = TFile.Open(dname)
    dtree = dfile.Get("limit")

    skip = ["r", "g", "r1", "r2", "g1", "g2", "deltaNLL", "quantileExpected",
            "limit", "limitErr", "mh", "syst",
            "iToy", "iSeed", "iChannel", "t_cpu", "t_real"]

    nuisances = [bb.GetName() for bb in dtree.GetListOfBranches()]
    hasbb = False

    setpar = []
    frzpar = []

    for i in dtree:
        if (dtree.quantileExpected != -1. and qexp_eq_m1) or (dtree.quantileExpected == -1. and not qexp_eq_m1):
            continue

        for nn in nuisances:
            if nn in skip:
                continue

            if "prop_bin" not in nn:
                frzpar.append(nn)
            else:
                hasbb = True

            vv = round(getattr(dtree, nn), 2)
            if abs(vv) > 0.01:
                setpar.append(nn + "=" + str(vv))

        if len(frzpar) > 0:
            break

    if hasbb:
        frzpar.append("rgx{prop_bin.*}")

    return [setpar, frzpar]

def starting_nuisance(point, frz_bb_zero = True, frz_bb_post = False, frz_nuisance_post = False, best_fit_file = ""):
    if frz_bb_zero:
        return [["rgx{prop_bin.*}=0"], ["rgx{prop_bin.*}"]]
    elif frz_bb_post or frz_nuisance_post:
        if best_fit_file == "":
            raise RuntimeError("postfit bb/nuisance freezing is requested, but no best fit file is provided!!!")

        setpar, frzpar = read_nuisance(best_fit_file, point, True)

        if not frz_nuisance_post:
            setpar = [nn for nn in setpar if "prop_bin" in nn]
            frzpar = [nn for nn in frzpar if "prop_bin" in nn]

        return [setpar, frzpar]

    return [[], []]

def elementwise_add(list_of_lists):
    if len(list_of_lists) < 1 or any(len(ll) < 1 or len(ll) != len(list_of_lists[0]) for ll in list_of_lists):
        raise RuntimeError("this method assumes that the argument is a list of lists of nonzero equal lengths!!!")

    result = list(list_of_lists[0])
    for ll in range(1, len(list_of_lists)):
        for rr in range(len(result)):
            result[rr] += list_of_lists[ll][rr]

    return result

def fit_strategy(strat, robust = False, high_tolerance = False):
    fstr = "--cminPreScan --cminDefaultMinimizerAlgo Migrad --cminDefaultMinimizerStrategy {ss} --cminFallbackAlgo Minuit2,Simplex,{ss}".format(ss = strat)
    if high_tolerance:
        fstr += ":0.5 --cminDefaultMinimizerTolerance 0.5 "
    if robust:
        fstr += " --robustFit 1 --setRobustFitStrategy {ss} {tt}".format(
            ss = strat,
            tt = "--setRobustFitTolerance 0.5 --setCrossingTolerance 5e-4" if high_tolerance else ""
        )
    return fstr

def recursive_glob(base_directory, pattern):
    # https://stackoverflow.com/a/2186639
    results = []
    for base, dirs, files in os.walk(base_directory):
        goodfiles = fnmatch.filter(files, pattern)
        results.extend(os.path.join(base, f) for f in goodfiles)
    return results

def make_datacard_with_args(scriptdir, args):
    syscall("{scr}/make_datacard.py --signal {sig} --background {bkg} --point {pnt} --channel {ch} --year {yr} "
            "{psd} {inj} {tag} {drp} {kee} {kfc} {thr} {lns} {shp} {mcs} {rpr} {prj} {cho} {rep} {rsd}".format(
                scr = scriptdir,
                pnt = ','.join(args.point),
                sig = args.signal,
                bkg = args.background,
                ch = args.channel,
                yr = args.year,
                psd = "--add-pseudodata" if args.asimov else "",
                inj = "--inject-signal " + args.inject if args.inject != "" else "",
                tag = "--tag " + args.tag if args.tag != "" else "",
                drp = "--drop '" + args.drop + "'" if args.drop != "" else "",
                kee = "--keep '" + args.keep + "'" if args.keep != "" else "",
                kfc = "--sushi-kfactor" if args.kfactor else "",
                thr = "--threshold " + args.threshold if args.threshold != "" else "",
                lns = "--lnN-under-threshold" if args.lnNsmall else "",
                shp = "--use-shape-always" if args.alwaysshape else "",
                mcs = "--no-mc-stats" if not args.mcstat else "",
                rpr = "--float-rate '" + args.rateparam + "'" if args.rateparam != "" else "",
                prj = "--projection '" + args.projection + "'" if args.projection != "" else "",
                cho = "--chop-up '" + args.chop + "'" if args.chop != "" else "",
                rep = "--replace-nominal '" + args.repnom + "'" if args.repnom != "" else "",
                rsd = "--seed " + args.seed if args.seed != "" else ""
            ))

def update_mask(masks):
    new_masks = []
    for mask in masks:
        channel, year = mask.split("_")
        if channel == "ll":
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

def index_list(index_string, baseline = 0):
    """
    builds a list of indices from an index string, to be used in some options
    index_string can be a mixture of comma separated non-negative integers, or the form A..B where A < B and A, B non-negative
    where the comma separated integers are plainly the single indices and
    the A..B version builds a list of indices from [A, B). If A is omitted, it is assumed to be the baseline (0 by default)
    the returned list of indices is sorted, with duplicates removed
    returns empty list if syntax is not followed
    """

    if not all([ii in "0123456789" for ii in index_string.replace("..", "").replace(",", "")]):
        return []

    index_string = tokenize_to_list(index_string)
    idxs = []

    for istr in index_string:
        if ".." in istr:
            ilst = tokenize_to_list(istr, '..' )
            idxs += range(int(ilst[0]), int(ilst[1])) if ilst[0] != "" else range(baseline, int(ilst[1]))
        else:
            idxs.append(int(istr))

    return list(set(idxs))
