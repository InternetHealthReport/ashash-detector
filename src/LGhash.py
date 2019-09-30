import logging
from multiprocessing import Pool
import mmh3
# import requests
import json
import itertools
from more_itertools import unique_justseen
from collections import defaultdict
import simhash
import os
from src.tools import sortDates, recordWriter, plot_roc_curve
from datetime import datetime, timedelta
from sklearn.metrics import roc_auc_score, roc_curve
import yaml

with open("config.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)

anomaly_data = cfg['writer']['save_address']
counter_file = cfg['analyser']['save_address'] + 'LGhash_counter'
min_dist = cfg['analyser']['dist_threshold']
# anomaly_data = "./data_anomalies_rerun/"
# counter_file = "./gm_test2"

def sketchesSimhash(sketches):
    hashes = {}
    for sketch, asProb in sketches[1].items():
        hashes[sketch] = simhash.Simhash(asProb, f=64)

    return hashes

class hegemonyPipe():
    def __init__(self, original_dir, scope, start="all", end="all"):
        self.original_dir=original_dir
        self.scope = scope
        self.start = start
        self.end = end
        self.dir = self.original_dir+str(self.scope)+"/"
        self.hegeDict = {}
        for file in os.listdir(self.dir):
            if os.path.isdir(self.dir + file):
                if self.start is not "all" \
                    and (datetime.strptime(file, '%Y-%m-%d')<datetime.strptime(self.start, '%Y-%m-%d')
                            or datetime.strptime(file, '%Y-%m-%d')>datetime.strptime(self.end, '%Y-%m-%d')):
                    continue
                self.hegeDict[file] = self.collect(file)
            elif len(file.split("_"))>1:
                pass
        self.dates = list(self.hegeDict.keys())
        self.dates = sortDates(self.dates)
        self.currTS = self.start
        self.currts = 96
        self.currHege = None

    def recv(self):
        if self.currts == 96:
            try:
                self.currTS = self.dates.pop(0)
                self.currts = 0
                self.currHege = self.hegeDict[self.currTS]
            except:
                return None, None, None
        self.currts += 1
        return self.currTS+" "+str((self.currts-1)/4), self.scope, self.currHege[self.currts-1]

    def collect(self, date):
        heges = dict()
        for i in range(96):
            heges[i] = {}
        for file in os.listdir(self.dir+date):
            key = int(file.split("_")[1])
            if key == self.scope:
                continue
            with open(self.dir+date+"/"+file) as input:
                hege = input.readlines()
                for i in range(96):
                    heges[i][key] = float(hege[i].strip())
        #TODO max? min?
        return heges

class graphMonitor():
    def __init__(self, hegemonyPipe, N, M, distThresh=min_dist, minVoteRatio=0.5, saverQueue=None, nbProc=4, cleanOutput=True):
        # threading.Thread.__init__(self)

        self.hegemonyPipe = hegemonyPipe
        self.N = N
        self.M = M
        self.distThresh = distThresh
        self.minVotes = minVoteRatio * N
        self.cleanMode = cleanOutput
        # self.nbProc = nbProc
        self.seeds = [2 ** i for i in range(1, self.N + 1)]

        self.ts = None
        self.scope = None
        self.hegemony = None
        self.Counter = {}
        self.dailyCounter = 0
        self.previousResults = dict()
        # self.hashCache = defaultdict(dict)
        self.workers = Pool(nbProc)
        self.saverQueue = saverQueue

        logging.debug(" New Graph Monitor")
        self.run()

    def hash(self, asn, seed):
        if self.scope == "all":
            return mmh3.hash128(str(asn), seed=seed) % self.M
        else:
            return mmh3.hash128(str(asn), seed=seed) % self.M
        # try:
        # return self.hashCache[asn][seed]
        # except KeyError:
        # h = mmh3.hash128(asn,seed=seed)%self.M
        # self.hashCache[asn][seed] = h
        # return h

    def run(self):
        # self.saverQueue.add(str(self.hegemonyPipe.scope))
        self.ts, self.scope, self.hegemony = self.hegemonyPipe.recv()
        while self.ts is not None:
            # logging.debug("Waiting for data")

            # logging.debug("Before sketching (AS %s)" % self.scope)
            res = self.sketching()
            # logging.debug("Sketching done")
            if self.scope in self.previousResults:
                ano = "%s: %s" % (self.ts, self.compareSimhash(res))
            self.previousResults[self.scope] = res
            if self.ts[11:] == "23.75":
                self.Counter[self.ts[:10]] = self.dailyCounter
                self.dailyCounter = 0
            self.ts, self.scope, self.hegemony = self.hegemonyPipe.recv()

        # self.saverQueue.add("\n\n")
        if self.cleanMode:
            rows = [(key+": "+str(value)) for key, value in self.Counter.items()]
            with open(counter_file, mode="a+") as output:
                output.write(str(self.hegemonyPipe.scope)+": \n")
                output.write("\n".join(rows))
                output.write("\n\n")

        self.saverQueue.write(mode="a+")
        # print(self.hegemonyPipe.scope)
        return

            # logging.debug("done (AS %s)" % self.scope)

    def sketching(self):
        sketches = defaultdict(lambda: defaultdict(dict))
        for seed in self.seeds:
            for asn, prob in self.hegemony.items():
                sketches[seed][self.hash(asn, seed)][str(asn)] = prob

        # compute the simhash for each hash function
        # hashes = self.workers.map(sketchesSimhash, sketches.items())
        hashes = []
        for item in sketches.items():
            hashes.append(sketchesSimhash(item))

        # hashes= map(sketchesSimhash, sketches.itervalues())

        return dict(zip(sketches.keys(), hashes)), sketches

    def compareSimhash(self, results):
        prevHash, prevSketches = self.previousResults[self.scope]
        currHash, currSketches = results
        cumDistance = 0
        nbAnomalousSketches = 0
        votes = defaultdict(int)
        diff = defaultdict(int)
        for seed, sketchSet in prevHash.items():
            for m, _prevHash in sketchSet.items():
                if not m in currHash[seed]:
                    continue
                distance = _prevHash.distance(currHash[seed][m])
                cumDistance += distance
                if distance > self.distThresh:
                    nbAnomalousSketches += 1
                    # self.dailyCounter += 1
                    for asn, currProb in currSketches[seed][m].items():
                        votes[asn] += 1
                        self.dailyCounter += 1
                        prevProb = 0.0
                        if asn in prevSketches[seed][m]:
                            prevProb = prevSketches[seed][m][asn]
                        diff[asn] = currProb - prevProb

        anomalies = [(asn, count, diff[asn]) for asn, count in votes.items() if
                     count >= self.minVotes]

        if anomalies:
            for ano in anomalies:
                # self.saverQueue.put(("graphchange", [self.ts, self.scope, ano[0], ano[1], ano[2]]))
                # print(",".join(str(x) for x in [self.ts, self.scope, ano[0], ano[1], ano[2]]))
                self.saverQueue.add(",".join(str(x) for x in [self.ts, self.scope, ano[0], ano[1], ano[2]]))

        # return anomalousAsn, nbAnomalousSketches, cumDistance

    # def hashfunc(self, x):
    # return int(hashlib.sha512(x).hexdigest(), 16)

    # def getPrefixPerCountry(self, cc):
    # geoinfo = "http://geoinfo.bgpmon.io/201601/prefixes_announced_from_country/%s" % cc
    # resp = requests.get(url=geoinfo)
    # geoinfodata = json.loads(resp.text)
    # prefixes = set([x["BGPPrefix"] for x in geoinfodata])

    # return prefixes

def clean(filename):
    with open(filename, mode="w+") as output:
        output.write("")

def main(scope):
    rw = recordWriter("./gm_test")
    hegePipe = hegemonyPipe(original_dir=anomaly_data, scope=scope)
    gm = graphMonitor(hegemonyPipe=hegePipe, N=1, M=1, distThresh=3, minVoteRatio=0, saverQueue=rw)

def drawROC(originasns="all", parameter=None):
    # maxAlerts = 95
    labels = []
    measured = []
    measured_dict = {}
    with open(counter_file, mode="r") as input:
        lines = input.readlines()
    anomalies = ("".join(lines)).split("\n\n")
    for anomaly in anomalies:
        anomaly = anomaly.split("\n")
        mea_ = [int(x.split(": ")[1]) for x in anomaly[1:]]
        key = anomaly[0][:-2]
        measured_dict[key] = [x/(max(mea_)+0.01) for x in mea_]
    for dir in os.listdir(anomaly_data):
        if originasns is not "all" and dir not in originasns:
            continue
        sub_address = anomaly_data + dir + "/"
        with open(sub_address + "labels", mode="r") as input:
            labels.extend([int(label) for label in input.readlines()])
        measured.extend(measured_dict[dir])
    # draw_label = "Threshold={0}--AUC: {1}".format(parameter, roc_auc_score(labels, measured))
    draw_label = "N={0}, M={1}--AUC: {2}".format(parameter[0], parameter[1], roc_auc_score(labels, measured))
    # draw_labels.append(draw_label)
    fpr, tpr, thresholds = roc_curve(labels, measured)
    return fpr, tpr, draw_label
    # fprs.append(fpr)
    # tprs.append(tpr)
    # plot_roc_curve(fprs, tprs, draw_labels, save_address="./test_generated/ROC_GM")

if __name__ == "__main__":
    draw_labels = []
    fprs = []
    tprs = []
    originasns = [600, 197426, 13335, 12880, 35160, 29256, 58224, 204317, 3833, 57958]
    parameters = [(1, 1), (5, 2), (2, 5), (5, 5)]
    # parameters = [3, 5, 7, 10]
    for parameter in parameters:
        rw = recordWriter("./gm_test")
        for originasn in originasns:
            hegePipe = hegemonyPipe(original_dir=anomaly_data, scope=originasn)
            # hegePipe = hegemonyPipe(original_dir="./data_anomalies/", scope=600)
            # gm = graphMonitor(hegemonyPipe=hegePipe, N=1, M=1, distThresh=parameter, minVoteRatio=0, saverQueue=rw)
            gm = graphMonitor(hegemonyPipe=hegePipe, N=parameter[0], M=parameter[1], distThresh=3, minVoteRatio=0, saverQueue=rw)
        fpr, tpr, draw_label = drawROC([str(x) for x in originasns], parameter)
        clean(counter_file)
        draw_labels.append(draw_label)
        fprs.append(fpr)
        tprs.append(tpr)
    plot_roc_curve(fprs, tprs, draw_labels, save_address="./test_generated/ROC_GM_mn")
