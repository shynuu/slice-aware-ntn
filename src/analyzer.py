from .const import APPLICATION_STREAMING, APPLICATION_VOIP, APPLICATION_WEB
from typing import List, Dict
import matplotlib.pyplot as plt
import numpy as np
import os
import codecs
import re
import tikzplotlib


class Plot(object):

    def __init__(self, x, y, legend, linestyle="-", marker=None, color=None):
        self.x = x
        self.y = y
        self.legend = legend
        self.linestyle = linestyle
        self.marker = marker
        self.color = color

    def reset_color(self):
        self.color_index = 0

    @classmethod
    def plot_fig(cls, xlabel, ylabel, title, *plots, savefig=False):
        i = 0
        colors = ["red", "blue", "orange", "green", "purple"]

        for plot in plots:
            if plot.color == None:
                plot.color = colors[i % len(colors)]
            plt.plot(plot.x, plot.y, label=plot.legend,
                     marker=plot.marker, color=plot.color, linestyle=plot.linestyle, linewidth=2)

        plt.ylabel(ylabel)
        plt.xlabel(xlabel)
        plt.title(title)
        plt.legend(loc='upper right')
        plt.plot()
        if savefig != False:
            plt.savefig(fname=f"{savefig}.pdf")


class Slice(object):

    def __init__(self, index, s, aware):
        self.index = index
        self.s = s
        self.pdu = []
        self.qfi = {}
        self.aware = aware

    def order(self, max_duration: int):
        for pdu in self.pdu:
            pdu.order(self.s.start, self.s.end, max_duration)

    def aggregate(self):

        pdus = []

        voip = [Probe(0, 0, 0, 0) for i in range(len(self.pdu[0].probes))]
        streaming = [Probe(0, 0, 0, 0) for i in range(len(self.pdu[0].probes))]
        web = [Probe(0, 0, 0, 0) for i in range(len(self.pdu[0].probes))]
        vi = 0
        si = 0
        wi = 0

        probes = None
        for pdu in self.pdu:
            if pdu.application.code == APPLICATION_VOIP:
                probes = voip
                vi += 1
            elif pdu.application.code == APPLICATION_STREAMING:
                probes = streaming
                si += 1
            else:
                probes = web
                wi += 1
            for i in range(len(probes)):
                if type(pdu.probes[i]) != int:
                    probes[i].jitter += pdu.probes[i].jitter
                    probes[i].trip_time += pdu.probes[i].trip_time
                    probes[i].loss += pdu.probes[i].loss
                    probes[i].throughput += pdu.probes[i].throughput

        if vi > 0:
            for i in range(len(voip)):
                if type(voip[i]) != int:
                    voip[i].jitter /= vi
                    voip[i].trip_time /= vi
                    voip[i].loss /= vi
            vdata = Dataset()
            vdata.legend = f"{'SAW' if self.aware else 'SUAW'} {self.index} - VoIP QFI 7"
            vdata.legend_pdb = f"{'SAW' if self.aware else 'SUAW'} {self.index} - VoIP QFI 7"
            vdata.probes = voip
            pdus.append(vdata)

        if si > 0:
            for i in range(len(streaming)):
                if type(streaming[i]) != int:
                    streaming[i].jitter /= si
                    streaming[i].trip_time /= si
                    streaming[i].loss /= si
            vdata = Dataset()
            vdata.legend = f"{'SAW' if self.aware else 'SUAW'} {self.index} - Streaming QFI 6"
            vdata.legend_pdb = f"{'SAW' if self.aware else 'SUAW'} {self.index} - Streaming QFI 6"
            vdata.probes = streaming
            pdus.append(vdata)

        if wi > 0:
            for i in range(len(streaming)):
                if type(streaming[i]) != int:
                    web[i].jitter /= wi
                    web[i].trip_time /= wi
                    web[i].loss /= wi
            vdata = Dataset()
            vdata.legend = f"{'SAW' if self.aware else 'SUAW'} {self.index} - Web QFI 9"
            vdata.legend_pdb = f"{'SAW' if self.aware else 'SUAW'} {self.index} - Web QFI 9"
            vdata.probes = web
            pdus.append(vdata)

        self.pdu = pdus


class Probe(object):

    def __init__(self, throughput, trip_time, loss, jitter):
        self.throughput = throughput
        self.trip_time = trip_time
        self.loss = loss
        self.jitter = jitter


class Dataset(object):

    def __init__(self):
        self.slice = None
        self.probes = []
        self.application = None
        self.legend = None
        self.legend_pdb = None

    def order(self, start: int, end: int, max_duration: int):
        if len(self.probes) == 0:
            self.probes = [Probe(0, 100, 100, 0) for i in range(max_duration)]
            return
        k = 0
        y = np.zeros(max_duration, dtype=Probe)
        for i in range(start, end):
            y[i] = self.probes[k]
            k += 1
        self.probes = y

    def get_throughput(self):
        return [probe.throughput if probe != 0 else 0 for probe in self.probes]

    def get_trip_time(self):
        return [probe.trip_time if probe != 0 else 0 for probe in self.probes]

    def get_loss(self):
        return [probe.loss if probe != 0 else 0 for probe in self.probes]

    def get_jitter(self):
        return [probe.jitter if probe != 0 else 0 for probe in self.probes]


class Parser(object):

    def __init__(self):
        pass

    @classmethod
    def parse_throughput(cls, thpt):
        return float(thpt) / 1000 / 1000

    @classmethod
    def parse_jitter(cls, jitter):
        return float(jitter)

    @classmethod
    def parse_trip_time(cls, tt):
        return float(tt)

    @classmethod
    def parse_loss(cls, loss):
        regex = r"([0-9]+)"
        rate = re.findall(regex, loss)[0]
        return float(rate)

    @classmethod
    def parse_web_application(cls, lines, duration):
        k = 0
        dataset = Dataset()
        for line in lines:
            if "received" not in line and k < duration:
                l = line.strip().split()
                thpt, jitter, error_rate, rt = l[6], l[8], l[11], l[12].split(
                    "/")[0]
                dataset.probes.append(
                    Probe(cls.parse_throughput(thpt),
                          cls.parse_trip_time(rt),
                          cls.parse_loss(error_rate),
                          cls.parse_jitter(jitter),
                          )
                )
                k += 1
        return dataset

    @classmethod
    def parse_voip_application(cls, lines, duration):
        k = 0
        dataset = Dataset()
        for line in lines:
            if "received" not in line and k < duration:
                l = line.strip().split()
                thpt, jitter, error_rate, rt = l[6], l[8], l[11], l[12].split(
                    "/")[0]
                dataset.probes.append(
                    Probe(cls.parse_throughput(thpt),
                          cls.parse_trip_time(rt),
                          cls.parse_loss(error_rate),
                          cls.parse_jitter(jitter),
                          )
                )
                k += 1
        return dataset

    @classmethod
    def parse_streaming_application(cls, lines, duration):
        k = 0
        dataset = Dataset()
        for line in lines:
            if "received" not in line and k < duration:
                l = line.strip().split()
                thpt, jitter, error_rate, rt = l[6], l[8], l[11], l[12].split(
                    "/")[0]
                dataset.probes.append(
                    Probe(cls.parse_throughput(thpt),
                          cls.parse_trip_time(rt),
                          cls.parse_loss(error_rate),
                          cls.parse_jitter(jitter),
                          )
                )
                k += 1
        return dataset

    @classmethod
    def parse_application(cls, application, ue_index, slice_index, file_path, duration):
        pth = f"{file_path}/ue-{ue_index}_{application.name.lower()}_{slice_index}_probes.txt"
        lines = None
        with codecs.open(pth, "r", encoding="utf-8") as f:
            lines = f.readlines()

        dataset = None
        if application.code == APPLICATION_WEB:
            dataset = cls.parse_web_application(lines[7::], duration)
        elif application.code == APPLICATION_STREAMING:
            dataset = cls.parse_streaming_application(lines[7::], duration)
        else:
            dataset = cls.parse_voip_application(lines[7::], duration)

        dataset.application = application
        dataset.slice = slice_index
        dataset.legend = f"UE-{ue_index} - Slice {slice_index} - {application.name} QFI {application.qi} - {application.get_data_rate()}"
        dataset.legend_pdb = f"UE-{ue_index} - Slice {slice_index} - {application.name} QFI {application.qi} - {application.pdb} ms"
        return dataset


def plot(scenario, folder=None, tikz=None, tex=None):

    iterations = 10
    sl_saw = []
    sl_suaw = []

    n_slice = len(scenario.slices)
    n_ue = len(scenario.users)

    for i in range(iterations):

        pth: str
        if folder != None:
            pth = os.path.abspath(folder)
        else:
            pth = os.path.abspath(f"scenarios/{scenario.name}")

        sa_folder = f"{pth}/{i}/results-sa"
        non_sa_folder = f"{pth}/{i}/results-non-sa"

        max_duration = scenario.get_max_duration()

        slices_sa: List[Slice] = [Slice(i, scenario.slices[i], True)
                                  for i in range(n_slice)]
        slices_non_sa: List[Slice] = [Slice(i, scenario.slices[i], False)
                                      for i in range(n_slice)]

        for k in range(len(scenario.slices)):
            for j in range(n_ue):
                for app in scenario.slices[k].applications:
                    slices_sa[k].pdu.append(Parser.parse_application(
                        app, j, k, sa_folder, (scenario.slices[k].end - scenario.slices[k].start)))

        for s in slices_sa:
            s.order(max_duration)

        for k in range(len(scenario.slices)):
            for j in range(n_ue):
                for app in scenario.slices[k].applications:
                    slices_non_sa[k].pdu.append(Parser.parse_application(
                        app, j, k, non_sa_folder, (scenario.slices[k].end - scenario.slices[k].start)))

        for s in slices_non_sa:
            s.order(max_duration)

        for s in slices_sa:
            s.aggregate()

        for s in slices_non_sa:
            s.aggregate()

        sl_saw.append(slices_sa)
        sl_suaw.append(slices_non_sa)

    slices_sa = []
    slices_non_sa = []

    aa = sl_saw[::][0]
    bb = sl_suaw[::][0]

    for i in range(1, iterations):
        for k in range(len(aa)):
            for p in range(len(sl_saw[i][k].pdu)):
                for j in range(len(sl_saw[i][k].pdu[p].probes)):
                    if type(sl_saw[i][k].pdu[p].probes[j]) != int:
                        aa[k].pdu[p].probes[j].jitter += sl_saw[i][k].pdu[p].probes[j].jitter
                        aa[k].pdu[p].probes[j].trip_time += sl_saw[i][k].pdu[p].probes[j].trip_time
                        aa[k].pdu[p].probes[j].loss += sl_saw[i][k].pdu[p].probes[j].loss
                        aa[k].pdu[p].probes[j].throughput += sl_saw[i][k].pdu[p].probes[j].throughput

    for k in range(len(aa)):
        for p in range(len(aa[k].pdu)):
            for j in range(len(aa[k].pdu[p].probes)):
                if type(aa[k].pdu[p].probes[j]) != int:
                    aa[k].pdu[p].probes[j].jitter /= iterations
                    aa[k].pdu[p].probes[j].trip_time /= iterations
                    aa[k].pdu[p].probes[j].loss /= iterations
                    aa[k].pdu[p].probes[j].throughput /= iterations

    for i in range(1, iterations):
        for k in range(len(bb)):
            for p in range(len(sl_suaw[i][k].pdu)):
                for j in range(len(sl_saw[i][k].pdu[p].probes)):
                    if type(sl_saw[i][k].pdu[p].probes[j]) != int:
                        bb[k].pdu[p].probes[j].jitter += sl_suaw[i][k].pdu[p].probes[j].jitter
                        bb[k].pdu[p].probes[j].trip_time += sl_suaw[i][k].pdu[p].probes[j].trip_time
                        bb[k].pdu[p].probes[j].loss += sl_suaw[i][k].pdu[p].probes[j].loss
                        bb[k].pdu[p].probes[j].throughput += sl_suaw[i][k].pdu[p].probes[j].throughput

    for k in range(len(bb)):
        for p in range(len(bb[k].pdu)):
            for j in range(len(bb[k].pdu[p].probes)):
                if type(bb[k].pdu[p].probes[j]) != int:
                    bb[k].pdu[p].probes[j].jitter /= iterations
                    bb[k].pdu[p].probes[j].trip_time /= iterations
                    bb[k].pdu[p].probes[j].loss /= iterations
                    bb[k].pdu[p].probes[j].throughput /= iterations

    slices_sa = aa
    slices_non_sa = bb

    x = np.arange(max_duration)

    i = 0
    colors = ["red", "blue", "orange", "green", "purple"]

    markers = [None, None, "*"]
    p = []
    k = 0
    for s in slices_non_sa:
        for a in s.pdu:
            p.append(Plot(x, a.get_throughput(),
                          legend=a.legend, marker=markers[k], color=colors[i % len(colors)], linestyle="dashed"))
            i += 1
    k += 1
    i = 0
    for s in slices_sa:
        for a in s.pdu:
            p.append(Plot(x, a.get_throughput(),
                          legend=a.legend, marker=markers[k], color=colors[i % len(colors)]))
            i += 1
    plt.figure(1)
    Plot.plot_fig("Time (s)", "Throughput (Mbit/s)",
                  "Throughput of each flow", *p)

    tikzplotlib.clean_figure()
    tikzplotlib.save("tikz_thpt.tex", textsize=5, axis_width="\\textwidth")

    p = []
    k = 0
    i = 0
    for s in slices_non_sa:
        for a in s.pdu:
            p.append(Plot(x, a.get_trip_time(),
                          legend=a.legend, marker=markers[k], color=colors[i % len(colors)], linestyle="dashed"))
            i += 1
    k += 1
    i = 0
    for s in slices_sa:
        for a in s.pdu:
            p.append(Plot(x, a.get_trip_time(),
                          legend=a.legend, marker=markers[k], color=colors[i % len(colors)]))
            i += 1

    plt.figure(2)
    Plot.plot_fig("Time (s)", "Trip Time (ms)",
                  "Packet Delay Budget of each flow", *p)

    tikzplotlib.clean_figure()
    tikzplotlib.save("tikz_pdb.tex", textsize=5, axis_width="\\textwidth")

    p = []
    k = 0
    i = 0

    for s in slices_non_sa:
        for a in s.pdu:
            p.append(Plot(x, a.get_loss(),
                          legend=a.legend, marker=markers[k], color=colors[i % len(colors)], linestyle="dashed"))
            i += 1
    k += 1
    i = 0
    for s in slices_sa:
        for a in s.pdu:
            p.append(Plot(x, a.get_loss(),
                          legend=a.legend, marker=markers[k], color=colors[i % len(colors)]))
            i += 1

    plt.figure(3)
    Plot.plot_fig("Time (s)", "Packet Error Rate (%)",
                  "Packet Error Rate of each flow", *p)

    tikzplotlib.clean_figure()
    tikzplotlib.save("tikz_per.tex", textsize=5, axis_width="\\textwidth")

    p = []
    k = 0
    i = 0
    for s in slices_non_sa:
        for a in s.pdu:
            p.append(Plot(x, a.get_jitter(),
                          legend=a.legend, marker=markers[k], color=colors[i % len(colors)], linestyle="dashed"))
            i += 1
    k += 1
    i = 0
    for s in slices_sa:
        for a in s.pdu:
            p.append(Plot(x, a.get_jitter(),
                          legend=a.legend, marker=markers[k], color=colors[i % len(colors)]))
            i += 1

    plt.figure(4)
    Plot.plot_fig("Time (s)", "Jitter (ms)",
                  "Jitter of each flow", *p)

    tikzplotlib.clean_figure()
    tikzplotlib.save("tikz_jitter.tex", textsize=5, axis_width="\\textwidth")

    plt.show()
