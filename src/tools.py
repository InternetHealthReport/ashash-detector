from src.hegemony import Hegemony
import os
from datetime import datetime,timedelta
import shutil
from threading import Thread
from queue import Queue
import numpy as np
from operator import itemgetter
import re
import matplotlib.pyplot as plt
import yaml
import pandas as pd

with open("config.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)

save_address = cfg['writer']['save_address']
fig_address = cfg['analyser']['figure_address']
tw = cfg['writer']['time_window']
# save_address = '/Users/sylar/work/Ashash_analysis/data_test/'
# fig_address = '/Users/sylar/work/Ashash_analysis/data_test/figures/'

def validity_check(clear=False, clear_target=[]):
    for asn in os.listdir(save_address):
        origin_dir = save_address + asn + "/"
        files = 0
        for dir in os.listdir(origin_dir):
            if os.path.isdir(origin_dir+dir) and len(os.listdir(origin_dir+dir))>0:
                files += 1
        if files != tw:
            print(files)
            print("Error found writing AS number %s!" %asn)
            if clear and (len(clear_target)==0 or int(asn) in clear_target):
                shutil.rmtree(origin_dir)
                print("Removed " + origin_dir)

def clear(target_dir):
    shutil.rmtree(target_dir)
    os.mkdir(target_dir)

def sortDates(original_dates):
    dates = []
    for date in original_dates:
        date = tuple([int(x) for x in date.split("-")])
        dates.append(date)
    dates = sorted(dates, key=itemgetter(0, 1, 2))
    dates = [datetime(date[0], date[1], date[2]) for date in dates]
    dates = [str(date)[:10] for date in dates]
    return dates

def plot_roc_curve(fprs, tprs, labels, caption, save_address=save_address):
    # plt.figure(1)
    for fpr, tpr, label in zip(fprs, tprs, labels):
        plt.plot(fpr, tpr, color=np.random.rand(3, ), label=label)
    plt.plot([0, 1], [0, 1], color='darkblue', linestyle='--')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title(caption)
    plt.legend()
    plt.savefig(save_address)
    plt.clf()
    plt.cla()

def plot_signals(signals, upperbound, lowerbound, xticks, save_address):
    x = np.arange(len(signals))
    plt.plot(x, signals, color='r')
    plt.plot(x, [upperbound]*len(signals), color='darkblue', linestyle='--')
    plt.plot(x, [lowerbound]*len(signals), color='darkblue', linestyle='--')
    plt.xticks([x*96+48 for x in np.arange(int(len(signals))/96)], xticks, rotation=23)
    plt.gca().set_ylim([0, None])
    plt.ylabel("AS Hegemony")
    plt.grid(True)
    plt.savefig(save_address)
    plt.clf()
    plt.cla()

def ts2int(ts):
    hr = ts[11:13]
    min = ts[14:16]
    return int(int(hr)*4+int(min)/15)

class Worker(Thread):
    """ Thread executing tasks from a given tasks queue """
    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try:
                func(*args, **kargs)
            except Exception as e:
                # An exception happened in this thread
                print(e)
            finally:
                # Mark this task as done, whether an exception happened or not
                self.tasks.task_done()


class ThreadPool:
    """ Pool of threads consuming tasks from a queue """
    def __init__(self, num_threads):
        self.tasks = Queue(num_threads)
        for _ in range(num_threads):
            Worker(self.tasks)

    def add_task(self, func, *args, **kargs):
        """ Add a task to the queue """
        self.tasks.put((func, args, kargs))

    def map(self, func, args_list):
        """ Add a list of tasks to the queue """
        for args in args_list:
            self.add_task(func, args)

    def wait_completion(self):
        """ Wait for completion of all the tasks in the queue """
        self.tasks.join()

# class dataWriter(object):
#     def __init__(self, originasn, day1, day2, save_address=save_address, labeled=False, labels=[]):
#         self.hegeDict = {}
#         self.HegeDict = {}
#         self.originasn = originasn
#         self.startdate = day1
#         self.enddate = day2
#         self.save_address = save_address
#         self.labeled = labeled
#         self.labels = labels
#         self.daylist = []
#         self.lost = []
#         self.mainHege = {}
#         if not os.path.exists(self.save_address):
#             os.mkdir(self.save_address)
#         if not os.path.exists(self.save_address+'/'+str(self.originasn)):
#             os.mkdir(self.save_address +'/' + str(self.originasn))
#         else:
#             self.daylist = os.listdir(self.save_address+'/'+str(self.originasn))
#         self.save_address = self.save_address + str(self.originasn) + '/'
#
#     def main(self, clear):
#         count = 0
#         if clear:
#             self.clear()
#         if self.labeled:
#             with open(self.save_address+"labels", "w+") as output:
#                 output.write("\n".join([str(x) for x in self.labels]))
#         d1 = datetime.strptime(self.startdate, '%Y-%m-%d')
#         d2 = datetime.strptime(self.enddate, '%Y-%m-%d')+timedelta(days=1)
#         while d1 != d2:
#             count += 96
#             self.collect(str(d1)[:10])
#             d1 += timedelta(days=1)
#
#         self.fillLost()
#
#         for day in self.daylist:
#             shutil.rmtree(self.save_address+day)
#         for key in self.HegeDict.keys():
#             with open(self.save_address+key, mode='w+') as output:
#                 data = self.HegeDict[key]
#                 if len(data)<count:
#                     data.extend(['0']*(count-len(data)))
#                 output.write('\n'.join(self.HegeDict[key])+'\n')
#
#     def collect(self, day):
#         if os.path.exists(self.save_address+day):
#             print("Data found: "+str(self.originasn)+" on "+day)
#             self.daylist.remove(day)
#             for file in os.listdir(self.save_address+day):
#                 with open(self.save_address+day+"/"+file, mode="r") as input:
#                     if file in self.hegeDict.keys():
#                         self.hegeDict[file].extend([x.strip() for x in input.readlines()])
#                     else:
#                         self.hegeDict[file] = [x.strip() for x in input.readlines()]
#             self.aggregate()
#         else:
#             print("Collecting data: "+str(self.originasn)+" on "+day)
#             save_address = self.save_address+day+'/'
#             os.mkdir(save_address)
#             hege = Hegemony(originasns=self.originasn, start=day + ' 00:00', end=day + ' 23:59')
#             for r in hege.get_results():
#                 for data in r:
#                     if data['originasn'] == data['asn']:
#                         continue
#                     key = str(data['originasn']) + '_' + str(data['asn'])
#                     ts = ts2int(data['timebin'])
#                     if key in self.hegeDict.keys():
#                         self.hegeDict[key][ts] = str(data['hege'])
#                     else:
#                         self.hegeDict[key] = ['0'] * 96
#                         self.hegeDict[key][ts] = str(data['hege'])
#             self.mainHege[day] = self.hegeDict
#             self.aggregate()
#
#         # hege = Hegemony(originasns=0, asns=[3356, 174, 1299], start=day + ' 00:00', end=day + ' 23:59')
#         # globals = []
#         # for r in hege.get_results():
#         #     for data in r:
#         #         globals.append(data['hege'])
#         # self.lost[day] = [0 if sum(x)>0 else 1 for x in np.array(globals).reshape((-1, 3))]
#         # print(self.lost[day])
#
#
#             # self.write(save_address)
#
#         # if len(os.listdir(self.save_address+day)) == 0:
#         #     lost = True
#         #     hege = Hegemony(originasns=0, asns=[3356, 174, 1299], start=day + ' 12:00', end=day + ' 12:00')
#         #     for r in hege.get_results():
#         #         if sum(data['hege'] for data in r) > 0:
#         #             lost = False
#         #             break
#         #     if lost:
#         #         print("LOST: " + day)
#         #         self.lostdates.append(day)
#
#     def write(self, save_address):
#         for key in self.hegeDict.keys():
#             # if len(self.hegeDict[key])<96:
#             #     self.hegeDict[key].extend(['0']*(96-len(self.hegeDict[key])))
#             with open(save_address+key, mode='w+') as output:
#                 output.write('\n'.join(self.hegeDict[key]) + '\n')
#         self.aggregate()
#
#     def aggregate(self):
#         for key in self.hegeDict.keys():
#             if key in self.HegeDict.keys():
#                 self.HegeDict[key].extend(self.hegeDict[key])
#             else:
#                 self.HegeDict[key] = self.hegeDict[key]
#         self.hegeDict.clear()
#
#     def clear(self):
#         shutil.rmtree(self.save_address)
#         os.mkdir(self.save_address)
#
#     # def fillLost(self):
#     #     for date in self.lostdates:
#     #         for key in self.HegeDict.keys():
#     #             self.hegeDict[key] = [str(np.median([np.float64(x) for x in self.HegeDict[key]]))]*96
#     #         save_address = self.save_address + date + '/'
#     #         self.write(save_address)
#     def fillLost(self):
#         for date in self.mainHege.keys():
#             for key in self.mainHege[date]:
#                 save_address = self.save_address + date + "/" + key
#                 with open(save_address, mode="w+") as output:
#                     output.write('\n'.join(self))

class dataWriter():
    def __init__(self, originasn, day1, day2, save_address=save_address, labeled=False, labels=[]):

        self.originasn = originasn
        self.startdate = day1
        self.enddate = day2
        self.save_address = save_address
        self.labeled = labeled
        self.labels = labels

        if not os.path.exists(self.save_address):
            os.mkdir(self.save_address)
        if not os.path.exists(self.save_address+'/'+str(self.originasn)):
            os.mkdir(self.save_address +'/' + str(self.originasn))
        self.save_address = self.save_address + str(self.originasn) + '/'
        d1 = datetime.strptime(self.startdate, '%Y-%m-%d')
        d2 = datetime.strptime(self.enddate, '%Y-%m-%d')
        self.dates = [str(d1)[:10]]
        while d1!=d2:
            d1 += timedelta(days=1)
            self.dates.append(str(d1)[:10])
        self.hegeTable = None
        self.hegeDict = {}
        self.lostMark = {}
        for date in self.dates:
            self.lostMark[date] = [0]*96

    def main(self, clear=True):
        if clear:
            self.clear()
        if self.labeled:
            with open(self.save_address+"labels", "w+") as output:
                output.write("\n".join([str(x) for x in self.labels]))
        for date in self.dates:
            self.collect(date)
        self.fillLost()
        self.write()

    def collect(self, date):
        print("Collecting data: " + str(self.originasn) + " on " + date)
        save_address = self.save_address + date + '/'
        if os.path.exists(save_address):
            shutil.rmtree(save_address)
        os.mkdir(save_address)
        hege = Hegemony(originasns=self.originasn, start=date + ' 00:00', end=date + ' 23:59')

        for r in hege.get_results():
            for data in r:
                if data['originasn'] == data['asn']:
                    continue
                key = str(data['originasn']) + '_' + str(data['asn'])
                ts = ts2int(data['timebin'])
                if key in self.hegeDict.keys():
                    self.hegeDict[key][ts] = data['hege']
                else:
                    self.hegeDict[key] = [0] * 96
                    self.hegeDict[key][ts] = data['hege']
        for key in self.hegeDict.keys():
            self.hegeDict[key] = np.array(self.hegeDict[key])
        if len(self.hegeDict.keys())==0:
            data = {date:np.array([0]*96)}
            data = pd.DataFrame([data], index=["Drop"])
        else:
            data = pd.DataFrame([self.hegeDict], index=[date]).T
        if self.hegeTable is None:
            self.hegeTable = data
        else:
            self.hegeTable = pd.concat([self.hegeTable, data], axis=1, sort=False)
        self.hegeDict.clear()

        hege = Hegemony(originasns=0, asns=[1299, 174, 3356], start=date + ' 00:00', end=date + ' 23:59')
        for r in hege.get_results():
            for data in r:
                ts = ts2int(data['timebin'])
                self.lostMark[date][ts] += data['hege']
        self.lostMark[date] = np.array([x!=0 for x in self.lostMark[date]])

    def fillLost(self):
        for col in self.hegeTable.columns:
            for row in self.hegeTable.loc[self.hegeTable[col].isnull(), col].index:
                self.hegeTable.at[row, col] = np.array([0]*96)
        # self.hegeTable.fillna(np.array([0]*96))
        if 'Drop' in self.hegeTable.index:
            self.hegeTable.drop('Drop', inplace=True)
        # lostnum = 0
        # for key in self.lostMark.keys():
        #     lostnum += sum(1 for x in self.lostMark[key] if x)
        medians = {}
        for key in self.hegeTable.index:
            medians[key] = []
            for date in self.dates:
                medians[key].extend(list(self.hegeTable.loc[key, date][self.lostMark[date]]))
            medians[key] = np.median(medians[key])
        for key in self.hegeTable.index:
            for date in self.dates:
                self.hegeTable.at[key, date] = self.hegeTable.loc[key, date] + np.array(np.float64(1)-self.lostMark[date])*medians[key]

    def write(self):
        for key in self.hegeTable.index:
            allData = []
            for date in self.dates:
                data = [str(x) for x in self.hegeTable.loc[key, date]]
                allData.extend(data)
                with open(self.save_address+date+"/"+key, mode="w+") as output:
                    output.write("\n".join(data))
            with open(self.save_address+key, mode="w+") as output:
                output.write("\n".join(allData))

    def clear(self):
        shutil.rmtree(self.save_address)
        os.mkdir(self.save_address)

class recordWriter(object):
    def __init__(self, filename):
        self.outputs = []
        self.filename = filename

    def add(self, output):
        self.outputs.append(str(output))

    def write(self, mode):
        with open(self.filename, mode=mode) as output:
            output.write("\n".join(self.outputs))

class dataAnalyser(object):
    '''
    plot_signals cannot be set to True manually, please use drawSignals() in readAnomalies.py if you want to get the figures of signals
    '''
    def __init__(self, origin_dir, originasn, add_noise=True, noise_sd=0.02, tolerance=5, start="all", end="all", min_anomalies=0, plot_signals=False):
        self.origin_dir = origin_dir + str(originasn) + "/"
        self.originasn = originasn
        self.add_noise = add_noise
        self.noise_sd = noise_sd
        self.start = start
        self.end = end
        self.min_anomalies = min_anomalies
        self.mad_param = tolerance
        self.plot_signals = plot_signals
        self.baseline_median = {}
        self.baseline_mad = {}
        self.alertCounter = {}
        save_address = self.origin_dir + "alerts"
        self.rw = recordWriter(save_address)

    def main(self, save_disk=False):
        for file in os.listdir(self.origin_dir):
            if os.path.isfile(self.origin_dir + file):
                if len(re.findall("_", file)) == 0:
                    # print(file)
                    continue
                # print(self.origin_dir+file)
                data = np.loadtxt(self.origin_dir+file, delimiter="\n", unpack=True)
                median, mad = self.getBaseline(data)
                self.baseline_median[file] = median
                self.baseline_mad[file] = mad
            else:
                if self.start is not "all":
                    if (datetime.strptime(file, '%Y-%m-%d')-datetime.strptime(self.start, '%Y-%m-%d'))/timedelta(days=1) > -1 \
                            and (datetime.strptime(file, '%Y-%m-%d')-datetime.strptime(self.end, '%Y-%m-%d'))/timedelta(days=1) < 1:
                        self.alertCounter[file] = 0
                    elif save_disk:
                        shutil.rmtree(self.origin_dir+file)
                else:
                    self.alertCounter[file] = 0
        # if self.plot_signals:
        #     for file in os.listdir(self.origin_dir):
        #         if
        # print(self.baseline_mad)
        # print(self.alertCounter)
        self.updateAlerts()
        if self.plot_signals:
            with open(self.origin_dir + "alerts", mode="r") as input:
                data = input.readlines()
            data = [x.strip().split("\n") for x in "".join(data).split("\n\n")]
            data = [x[-1] for x in data]
            ticks = [i.split(": ")[0] for i in data]
            sub_fig_address = fig_address + str(self.originasn) + "/" + ticks[0] + "_" + ticks[-1] + "/"
            if not os.path.exists(sub_fig_address):
                os.makedirs(sub_fig_address)
            for file in os.listdir(self.origin_dir):
                if os.path.isfile(self.origin_dir + file) and len(re.findall('_', file)) > 0:
                    with open(self.origin_dir + file) as input:
                        signals = [float(x.strip()) for x in input.readlines()]
                    plot_signals(signals, self.baseline_median[file]+self.mad_param*self.baseline_mad[file],
                                 self.baseline_median[file]-self.mad_param*self.baseline_mad[file], ticks, sub_fig_address+file)

    def getBaseline(self, data):
        if self.add_noise:
            data += np.random.normal(0, self.noise_sd, len(data))
        mad = np.median(np.abs(data - np.median(data)))
        # print(np.median(data))
        # print(mad)
        return np.median(data), mad

    def updateAlerts(self):
        dates = sortDates(list(self.alertCounter.keys()))
        for date in dates:
            count = 0
            _count = 0
            data_address = self.origin_dir + date + "/"
            asns = list(self.baseline_mad.keys())
            sub_anomalies = []
            # print(self.baseline_mad.keys())
            for file in os.listdir(data_address):
                if os.path.isdir(file) and (datetime.strptime(self.end, '%Y-%m-%d') > datetime.strptime(file, '%Y-%m-%d')
                        or datetime.strptime(self.start, '%Y-%m-%d') < datetime.strptime(file, '%Y-%m-%d')):
                    continue
                key = file
                asns.remove(file)
                # print(file)
                data = np.loadtxt(data_address+file, delimiter="\n", unpack=True)
                sub_count = sum([1 if (x > self.baseline_median[key]+self.mad_param*self.baseline_mad[key]
                                       or x < self.baseline_median[key]-self.mad_param*self.baseline_mad[key]) else 0 for x in data])
                _sub_count = int(sum([abs(x-self.baseline_median[key]) if (x > self.baseline_median[key]+self.mad_param*self.baseline_mad[key]
                                       or x < self.baseline_median[key]-self.mad_param*self.baseline_mad[key]) else 0 for x in data])/self.baseline_mad[key])
                count += sub_count
                _count += _sub_count

                # TODO test codes
                count = _count
                sub_count = _sub_count

                if sub_count>self.min_anomalies:
                    # self.rw.add(key.split("_")[1] + ": " + str(sub_count))
                    sub_anomalies.append((key.split("_")[1], sub_count))

            #
            # sub_anomalies = sorted(sub_anomalies, key=lambda x: x[1], reverse=True)
            # for (a, b) in sub_anomalies:
            #     self.rw.add(a + ": " + str(b))


            if len(asns) > 0:
                for asn in asns:
                    with open(data_address+asn, mode="w+") as output:
                        output.write("\n".join(["0"]*96))
                    key = asn
                    data = np.loadtxt(data_address + asn, delimiter="\n", unpack=True)
                    sub_count = sum([1 if (x > self.baseline_median[key] + self.mad_param * self.baseline_mad[key]
                                           or x < self.baseline_median[key] - self.mad_param * self.baseline_mad[
                                               key]) else 0 for x in data])
                    _sub_count = int(sum([abs(x - self.baseline_median[key]) if (
                                x > self.baseline_median[key] + self.mad_param * self.baseline_mad[key]
                                or x < self.baseline_median[key] - self.mad_param * self.baseline_mad[key]) else 0 for x
                                          in data]) / self.baseline_mad[key])
                    count += sub_count
                    _count += _sub_count

                    # TODO test codes
                    count = _count
                    sub_count = _sub_count

                    if sub_count > self.min_anomalies:
                        # self.rw.add(key.split("_")[1] + ": " + str(sub_count))
                        sub_anomalies.append((key.split("_")[1], sub_count))
            sub_anomalies = sorted(sub_anomalies, key=lambda x: x[1], reverse=True)
            for (a, b) in sub_anomalies:
                self.rw.add(a + ": " + str(b))
            # deal with 0*96 "invisible" file in each day # TODO should we?
            # for asn in asns:
            #     if 0 < self.baseline_median[asn] - self.baseline_mad[asn]*3:
                    # count += 96
                    # self.rw.add(asn.split("_")[1] + ": 96(0)")
            self.rw.add(date + ": " + str(count) + "\n")
            self.alertCounter[date] = count
        self.rw.write("w+")

if __name__ == "__main__":
    dw = dataWriter(3833, "2019-05-13", "2019-05-19", "./data_daily/")
    dw.main(True)
    # da = dataAnalyser("./data_anomalies/", 58224)
    # da.main()