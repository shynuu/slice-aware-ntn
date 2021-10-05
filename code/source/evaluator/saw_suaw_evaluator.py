"""
Copyright (c) 2021 Youssouf Drif

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import codecs
import os
import re
import tikzplotlib
import numpy as np
import matplotlib.pyplot as plt
from typing import List
from . import Evaluator
from ..testbed.testbed import Testbed


APPLICATION_WEB = 0x01
APPLICATION_STREAMING = 0x02
APPLICATION_VOIP = 0x03


class Plot(object):
    """
    Plot class helper
    """

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
        px = 1/plt.rcParams['figure.dpi']
        i = 0
        colors = ["red", "blue", "orange", "green", "purple"]

        if savefig != False:
            plt.figure(figsize=(2000*px, 1000*px))
        else:
            plt.figure()
        for plot in plots:
            if plot.color == None:
                plot.color = colors[i % len(colors)]
            plt.plot(plot.x, plot.y, label=plot.legend,
                     marker=plot.marker, color=plot.color, linestyle=plot.linestyle, linewidth=2)

        plt.ylabel(ylabel)
        plt.xlabel(xlabel)
        plt.title(title)
        plt.legend(loc='upper right')
        if savefig != False:
            plt.savefig(fname=f"{savefig}.pdf")


class Slice(object):
    """
    Slice class
    """

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
            for i in range(len(web)):
                if type(web[i]) != int:
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


class SSEvaluator(Evaluator):
    """SAW and SUAW evaluator"""

    def init_folder(self, receipes_folder: str):
        pth = f"{receipes_folder}/eval_{self.t1.scenario.name}_{self.t2.scenario.name}"
        self.output_path = pth
        if not os.path.exists(pth):
            os.makedirs(pth)

    def parse_slices(self, testbed: Testbed, aware: bool) -> List:

        parsed = []
        slices = testbed.scenario.repository.get_misc("slices")
        n_slice = len(slices)
        n_ue = len(testbed.scenario.repository.get_misc("users"))
        iterations = testbed.iterations
        base_path = testbed.receipes

        for i in range(iterations):
            pth: str = f"{base_path}/iteration-{i}"

            max_duration = testbed.scenario.get_max_duration(slices)

            slices_probes: List[Slice] = [Slice(i, slices[i], aware)
                                          for i in range(n_slice)]

            for k in range(len(slices)):
                for j in range(n_ue):
                    for app in slices[k].applications:
                        slices_probes[k].pdu.append(Parser.parse_application(
                            app, j, k, pth, (slices[k].end - slices[k].start)))

            for s in slices_probes:
                s.order(max_duration)

            for s in slices_probes:
                s.aggregate()

            parsed.append(slices_probes)

        return parsed

    def mean_slices(self, probes: List, testbed: Testbed) -> List:

        tmp = probes[::][0]
        iterations = testbed.iterations
        for i in range(1, iterations):
            for k in range(len(tmp)):
                for p in range(len(probes[i][k].pdu)):
                    for j in range(len(probes[i][k].pdu[p].probes)):
                        if type(probes[i][k].pdu[p].probes[j]) != int:
                            tmp[k].pdu[p].probes[j].jitter += probes[i][k].pdu[p].probes[j].jitter
                            tmp[k].pdu[p].probes[j].trip_time += probes[i][k].pdu[p].probes[j].trip_time
                            tmp[k].pdu[p].probes[j].loss += probes[i][k].pdu[p].probes[j].loss
                            tmp[k].pdu[p].probes[j].throughput += probes[i][k].pdu[p].probes[j].throughput

        for k in range(len(tmp)):
            for p in range(len(tmp[k].pdu)):
                for j in range(len(tmp[k].pdu[p].probes)):
                    if type(tmp[k].pdu[p].probes[j]) != int:
                        tmp[k].pdu[p].probes[j].jitter /= iterations
                        tmp[k].pdu[p].probes[j].trip_time /= iterations
                        tmp[k].pdu[p].probes[j].loss /= iterations
                        tmp[k].pdu[p].probes[j].throughput /= iterations

        return tmp

    def evaluate(self, contribution: bool, plot: bool) -> None:

        sl_saw = self.parse_slices(self.t1, True)
        sl_suaw = self.parse_slices(self.t2, False)

        slices_sa = self.mean_slices(sl_saw, self.t1)
        slices_non_sa = self.mean_slices(sl_suaw, self.t2)

        max_duration = self.t1.scenario.get_max_duration(
            self.t1.scenario.repository.get_misc("slices"))
        x = np.arange(max_duration)

        i = 0
        colors = ["red", "blue", "orange", "green", "purple"]

        if contribution:
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
            Plot.plot_fig("Time (s)", "Throughput (Mbit/s)",
                          "Throughput of each QFI", *p, savefig=f"{self.output_path}/throughput")

            tikzplotlib.clean_figure()
            tikzplotlib.save(f"{self.output_path}/throughput.tex", textsize=5,
                             axis_width="\\textwidth")
            plt.clf()
            plt.cla()
            plt.close()

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

            Plot.plot_fig("Time (s)", "Trip Time (ms)",
                          "Packet Delay Budget of each QFI", *p)

            tikzplotlib.clean_figure()
            tikzplotlib.save(f"{self.output_path}/packet_delay_budget.tex", textsize=5,
                             axis_width="\\textwidth")
            plt.clf()
            plt.cla()
            plt.close()

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

            Plot.plot_fig("Time (s)", "Packet Error Rate (%)",
                          "Packet Error Rate of each QFI", *p)

            tikzplotlib.clean_figure()
            tikzplotlib.save(f"{self.output_path}/packet_error_rate.tex", textsize=5,
                             axis_width="\\textwidth")
            plt.clf()
            plt.cla()
            plt.close()

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

            Plot.plot_fig("Time (s)", "Jitter (ms)",
                          "Jitter of each QFI", *p)

            tikzplotlib.clean_figure()
            tikzplotlib.save(f"{self.output_path}/jitter.tex", textsize=5,
                             axis_width="\\textwidth")
            plt.clf()
            plt.cla()
            plt.close()

        ###########################
        markers = [None, None, "*"]
        i = 0
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
        Plot.plot_fig("Time (s)", "Throughput (Mbit/s)",
                      "Throughput of each QFI", *p, savefig=f"{self.output_path}/throughput")

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

        Plot.plot_fig("Time (s)", "Trip Time (ms)",
                      "Packet Delay Budget of each QFI", *p, savefig=f"{self.output_path}/packet_delay_budget")

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

        Plot.plot_fig("Time (s)", "Packet Error Rate (%)",
                      "Packet Error Rate of each QFI", *p, savefig=f"{self.output_path}/packet_error_rate")

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

        Plot.plot_fig("Time (s)", "Jitter (ms)",
                      "Jitter of each QFI", *p, savefig=f"{self.output_path}/jitter")

        if plot:
            plt.show()
