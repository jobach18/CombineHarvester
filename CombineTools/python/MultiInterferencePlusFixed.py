from HiggsAnalysis.CombinedLimit.PhysicsModel import PhysicsModelBase_NiceSubclasses

class MultiInterferencePlusFixed(PhysicsModelBase_NiceSubclasses):
    def __init__(self):
        self.signal_parts = ['_neg', '_pos', '_res']
        self.signals = []
        self.pois    = []
        self.verbose = False
        self.nor = False
        self.oner = False
        self.r_is_uninitialized = True
        self.printonce = True
        super(MultiInterferencePlusFixed, self).__init__()

    def setPhysicsOptions(self, physOptions):
        if len([po for po in physOptions if po.startswith("signal=")]) != 1:
            raise RuntimeError, 'Model expects a signal=s1,s2,...,sN option, provided exactly once'

        if any([po == "no-r" for po in physOptions]) and any([po == "one-r" for po in physOptions]):
            raise RuntimeError, "--no-r and --one-r can't be simultaneously provided!"

        for po in physOptions[:]:
            if po.startswith("signal="):
                signals = po.split('=')[1].split(',')

                for ss in signals:
                    if not (ss.startswith("A_m") or ss.startswith("H_m")):
                        raise RuntimeError, 'Model expects only A/H signals'
                    if any([sp in ss for sp in self.signal_parts]):
                        raise RuntimeError, 'Model expects all parts of A/H signal together i.e. it does not handle them piecewise. specify as e.g. signal=A_m400_w5p0,...'

        super(MultiInterferencePlusFixed, self).setPhysicsOptions(physOptions)

    def processPhysicsOptions(self, physOptions):
        processed = []
        physOptions.sort(key = lambda x: x.startswith("no-r"), reverse = True)
        physOptions.sort(key = lambda x: x.startswith("one-r"), reverse = True)
        physOptions.sort(key = lambda x: x.startswith("verbose"), reverse = True)
        for po in physOptions:
            if po == "verbose":
                self.verbose = True
            if po == "no-r":
                self.nor = True
                self.oner = False
            if po == "one-r":
                self.nor = False
                self.oner = True
            if po.startswith("signal="):
                signals = po.split('=')[1].split(',')

                for ss in signals:
                    self.add_poi_per_signal(ss)

            processed.append(po)

        return processed + super(MultiInterferencePlusFixed, self).processPhysicsOptions(physOptions)

    def add_poi_per_signal(self, signal):
        self.signals.append(signal)
        self.pois.append('g{ss}'.format(ss = self.signals.index(signal) + 1))

        if not self.nor and not self.oner:
            self.pois.append('r{ss}'.format(ss = self.signals.index(signal) + 1))
        elif self.oner and 'r' not in self.pois:
            self.pois.append('r')

    def doParametersOfInterest(self):
        for ii, signal in enumerate(self.signals):
            self.modelBuilder.doVar('g{ss}[1,0,5]'.format(ss = ii + 1))

            if self.nor:
                self.modelBuilder.factory_('expr::g2_{ss}("@0*@0", g{ss})'.format(ss = ii + 1))
                self.modelBuilder.factory_('expr::mg2_{ss}("-@0*@0", g{ss})'.format(ss = ii + 1))
                self.modelBuilder.factory_('expr::g4_{ss}("@0*@0*@0*@0", g{ss})'.format(ss = ii + 1))
                self.modelBuilder.factory_('expr::mg4_{ss}("-@0*@0*@0*@0", g{ss})'.format(ss = ii + 1))
            else:
                if self.oner and self.r_is_uninitialized:
                    self.modelBuilder.doVar('r[1,0,10]')
                    self.r_is_uninitialized = False
                else:
                    self.modelBuilder.doVar('r{ss}[1,0,10]'.format(ss = ii + 1))

                self.modelBuilder.factory_('expr::g2_{ss}("(@0*@0)*@1", g{ss}, r{tt})'.format(ss = ii + 1, tt = '' if self.oner else ii + 1))
                self.modelBuilder.factory_('expr::mg2_{ss}("(-@0*@0)*@1", g{ss}, r{tt})'.format(ss = ii + 1, tt = '' if self.oner else ii + 1))
                self.modelBuilder.factory_('expr::g4_{ss}("(@0*@0*@0*@0)*@1", g{ss}, r{tt})'.format(ss = ii + 1, tt = '' if self.oner else ii + 1))
                self.modelBuilder.factory_('expr::mg4_{ss}("(-@0*@0*@0*@0)*@1", g{ss}, r{tt})'.format(ss = ii + 1, tt = '' if self.oner else ii + 1))

        self.modelBuilder.doSet('POI', ','.join(self.pois))

    def getPOIList(self):
        return self.pois

    def getYieldScale(self, bin, process):
        if not self.DC.isSignal[process]:
            return 1

        idx = process
        for sp in self.signal_parts:
            idx = idx.replace(sp, "")
        idx = self.signals.index(idx) + 1

        if self.verbose and self.printonce:
            if self.nor:
                print "INFO: using model version without the r term."
            elif self.oner:
                print "INFO: using model version with one common r term for all signals."
            else:
                print "INFO: using model version where all signals get their own r term."

            self.printonce = False

        if '_neg' in process:
            if '_res' in process:
                if self.verbose:
                    print 'Scaling', process, 'in bin', bin, 'with negative coupling modifier', 'g' + str(idx), 'to the 4'
                    print 'WARNING: negative resonance, are you sure this is what you want?'
                return 'mg4_' + str(idx)
            else:
                if self.verbose:
                    print 'Scaling', process, 'in bin', bin, 'with negative coupling modifier', 'g' + str(idx), 'squared'
                return 'mg2_' + str(idx)
        elif '_res' in process:
            if self.verbose:
                print 'Scaling', process, 'in bin', bin, 'with coupling modifier', 'g' + str(idx), 'to the 4'
            return 'g4_' + str(idx)

        if self.verbose:
            print 'Scaling', process, 'in bin', bin, 'with coupling modifier', 'g' + str(idx), 'squared'
        return 'g2_' + str(idx)

multiInterferencePlusFixed = MultiInterferencePlusFixed()
