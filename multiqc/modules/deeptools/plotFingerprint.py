#!/usr/bin/env python

""" MultiQC submodule to parse output from deepTools plotFingerprint """

import logging
import re
from collections import OrderedDict
import numpy as np

from multiqc import config
from multiqc.plots import bargraph, linegraph

# Initialise the logger
log = logging.getLogger(__name__)

class plotFingerprintMixin():
    def parse_plotFingerprint(self):
        """Find plotFingerprint output. Both --outQualityMetrics and --outRawCounts"""
        self.deeptools_plotFingerprintOutQualityMetrics = dict()
        for f in self.find_log_files('deeptools/plotFingerprintOutQualityMetrics'):
            parsed_data = self.parsePlotFingerprintOutQualityMetrics(f['f'], f['fn'])
            for k, v in parsed_data.items():
                if k in self.deeptools_plotFingerprintOutQualityMetrics:
                    log.warning("Replacing duplicate sample {}.".format(k))
                self.deeptools_plotFingerprintOutQualityMetrics[k] = v

            if len(parsed_data) > 0:
                self.add_data_source(f, section='plotFingerprint')

        self.deeptools_plotFingerprintOutRawCounts= dict()
        for f in self.find_log_files('deeptools/plotFingerprintOutRawCounts'):
            parsed_data = self.parsePlotFingerprintOutRawCounts(f['f'], f['fn'])
            for k, v in parsed_data.items():
                if k in self.deeptools_plotFingerprintOutRawCounts:
                    log.warning("Replacing duplicate sample {}.".format(k))
                self.deeptools_plotFingerprintOutRawCounts[k] = v

            if len(parsed_data) > 0:
                self.add_data_source(f, section='plotFingerprint')

        if len(self.deeptools_plotFingerprintOutQualityMetrics) > 0:
            d = OrderedDict()
            categories = []
            for sample, v in self.deeptools_plotFingerprintOutQualityMetrics.items():
                sample = str(sample)
                for category, v2 in v.items():
                    if category not in d:
                        d[category] = dict()
                        categories.append(category)
                    d[category][sample] = v2
            config = dict(cpswitch=False, hide_zero_cats=False, ymin=0.0, ymax=1.0, ylab='Value', stacking=None, tt_percentages=False, tt_decimals=3)
            self.add_section(name="plotFingerprint (quality metrics)",
                             anchor="plotFingerprint",
                             plot=bargraph.plot(d, pconfig=config))

        if len(self.deeptools_plotFingerprintOutRawCounts) > 0:
            config = dict(xmin=0.0, xmax=1.0, ymin=0.0, ymax=1.0, xlab='rank', ylab='Fraction w.r.t. bin with highest coverage')
            self.add_section(name="plotFingerprint",
                             anchor="plotFingerprint",
                             plot=linegraph.plot(self.deeptools_plotFingerprintOutRawCounts, config))

        return len(self.deeptools_plotFingerprintOutQualityMetrics), len(self.deeptools_plotFingerprintOutRawCounts)

    def parsePlotFingerprintOutQualityMetrics(self, f, fname):
        d = {}
        firstLine = True
        header = []
        for line in f.splitlines():
            cols = line.strip().split("\t")

            if len(cols) < 7:
                log.warning("{} was initially flagged as the output from plotFingerprint --outQualityMetrics, but that seems to not be the case. Skipping...".format(fname))
                return dict()

            if firstLine:
                header = [str(x) for x in cols[1:]]
                firstLine = False
                continue

            if cols[0] in d:
                log.warning("Replacing duplicate sample {}.".format(cols[0]))
            d[cols[0]] = OrderedDict()

            try:
                for i, c in enumerate(cols[1:]):
                    if i >= len(header):
                        log.warning("{} was initially flagged as the output from plotFingerprint --outQualityMetrics, but that seems to not be the case. Skipping...".format(fname))
                        return dict()
                    if header[i] == "AUC" or header[i] == "Synthetic AUC":
                        continue
                    d[cols[0]][header[i]] = float(c)
            except:
                log.warning("{} was initially flagged as the output from plotFingerprint --outQualityMetrics, but that seems to not be the case. Skipping...".format(fname))
                return dict()
        return d

    def parsePlotFingerprintOutRawCounts(self, f, fname):
        d = dict()
        samples = []
        firstLine = True
        for line in f.splitlines():
            cols = line.strip().split('\t')
            if cols[0] == "#plotFingerprint --outRawCounts":
                continue

            if firstLine:
                for c in cols:
                    c = str(c).strip("'")
                    d[c] = []
                    samples.append(c)
                firstLine = False
                continue

            for idx, c in enumerate(cols):
                d[samples[idx]].append(int(c))

        # Switch to numpy, get the normalized cumsum
        x = np.linspace(0, len(d[samples[0]]) - 1, endpoint=True, num=100, dtype=int)  # The indices into the vectors that we'll actually return for plotting
        xp = np.arange(len(d[samples[0]]) + 1) / float(len(d[samples[0]]) + 1)
        for k, v in d.items():
            v = np.array(v)
            v = np.sort(v)
            cs = np.cumsum(v)
            cs = cs / float(cs[-1])
            # Convert for plotting
            v2 = dict()
            v2[0.0] = 0.0
            for _ in x:
                v2[xp[_]] = cs[_]
            d[k] = v2
        return d
