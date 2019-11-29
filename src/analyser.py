import pygsheets
import pandas as pd
import os
from datetime import datetime, timedelta
from src.tools import dataWriter, dataAnalyser, ThreadPool, plot_roc_curve, plot_signals
import shutil
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve
from sklearn.metrics import roc_auc_score
import re
import yaml

with open("config.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)

data_address = cfg['writer']['save_address']
save_address = cfg['analyser']['save_address']
fig_address = cfg['analyser']['figure_address']
noise_sd_default = cfg['analyser']['noise_sd_default']
tolerance_default = cfg['analyser']['tolerance']
# save_address = "../data_anomalies_rerun/"
# fig_address = "./results_figure_rerun/"
# time_window = 7
# min_anomalies = 0 # 5
# noise_sd_default = 2e-2

def analysingWorker(params):
    if len(params)==2:
        dataAnalyser(origin_dir=data_address, originasn=params[0], noise_sd=params[1]).main()
    else:
        dataAnalyser(origin_dir=data_address, originasn=params[0], start=params[1], end=params[2], noise_sd=params[3], tolerance=tolerance_default).main()

def analyzeAnomalies(params=None, plot=True, noise_sd=None):
    q = []
    pool = ThreadPool(4)
    fig_params = []
    if noise_sd is not None:
        noise_sd_default = noise_sd
    if params is None:
        for dir in os.listdir(data_address):
            if os.path.isdir(data_address + dir):
                q.append([int(dir), noise_sd_default])
    else:
        q = [param.append(noise_sd_default) for param in params]
        q = [param.append(tolerance_default) for param in params]
        q = params
        fig_params = [str(x[0]) for x in params]
    pool.map(analysingWorker, q)
    pool.wait_completion()
    if plot:
        plotAnomalies(originasns=fig_params)

def plotAnomalies(originasns=[], plotBarGraph=True):
    if not os.path.exists(fig_address):
        os.mkdir(fig_address)
    if len(originasns) == 0:
        for dir in os.listdir(data_address):
            address = data_address + dir + "/"
            with open(address + "alerts", mode="r") as input:
                data = input.readlines()
            data = [x.strip().split("\n") for x in "".join(data).split("\n\n")]
            maximums = [x[:-1] for x in data]
            data = [x[-1] for x in data]
            x = [i.split(": ")[0] for i in data]
            y = [int(j.split(": ")[1]) for j in data]
            plt.figure(figsize=(10, 5))
            if plotBarGraph:
                max1st = []
                max2nd = []
                for maximum in maximums:
                    if len(maximum) == 0:
                        max1st.append(("", 0))
                        max2nd.append(("", 0))
                    elif len(maximum) == 1:
                        max1st.append((maximum[0].split(": ")[0], int(maximum[0].split(": ")[1])))
                        max2nd.append(("", 0))
                    else:
                        max1st.append((maximum[0].split(": ")[0], int(maximum[0].split(": ")[1])))
                        max2nd.append((maximum[1].split(": ")[0], int(maximum[1].split(": ")[1])))
                y2 = [x[1] for x in max1st]
                y3 = [x[1] for x in max2nd]
                plt.bar(x, y2, width=0.45, align='center', color='c', alpha=0.9)
                plt.bar(x, y3, width=0.45, bottom=y2, tick_label=y2, align='center', color='y', alpha=0.9)
                for a, b, label in zip(x, y2, [x[0] for x in max1st]):
                    if b != 0:
                        plt.text(a, b, '%s' % label, ha='center', va='bottom', fontsize=10)
                for a, b1, b2, label in zip(x, y2, y3, [x[0] for x in max2nd]):
                    if b2 != 0:
                        plt.text(a, b1 + b2 + 10, '%s' % label, ha='center', va='bottom', fontsize=10)
            plt.xticks(np.arange(len(x)), labels=x, rotation=20)
            plt.plot(x, y, 'r')
            # plt.gca().set_ylim([0, None])
            # plt.savefig(address + dir)
            plt.savefig(fig_address + dir)
            plt.clf()
            plt.cla()
    else:
        for originasn in originasns:
            address = data_address + originasn + "/"
            try:
                with open(address + "alerts", mode="r") as input:
                    data = input.readlines()
            except:
                continue
            data = [x.strip().split("\n") for x in "".join(data).split("\n\n")]
            maximums = [x[:-1] for x in data]
            data = [x[-1] for x in data]
            x = [i.split(": ")[0] for i in data]
            y = [int(j.split(": ")[1]) for j in data]
            plt.figure(figsize=(10, 5))
            if plotBarGraph:
                max1st = []
                max2nd = []
                for maximum in maximums:
                    if len(maximum) == 0:
                        max1st.append(("", 0))
                        max2nd.append(("", 0))
                    elif len(maximum) == 1:
                        max1st.append((maximum[0].split(": ")[0], int(maximum[0].split(": ")[1])))
                        max2nd.append(("", 0))
                    else:
                        max1st.append((maximum[0].split(": ")[0], int(maximum[0].split(": ")[1])))
                        max2nd.append((maximum[1].split(": ")[0], int(maximum[1].split(": ")[1])))
                y2 = [x[1] for x in max1st]
                y3 = [x[1] for x in max2nd]
                plt.bar(x, y2, width=0.45, align='center', color='c', alpha=0.9)
                plt.bar(x, y3, width=0.45, bottom=y2, tick_label=y2, align='center', color='y', alpha=0.9)
                for a, b, label in zip(x, y2, [x[0] for x in max1st]):
                    if b != 0:
                        plt.text(a, b, '%s' % label, ha='center', va='bottom', fontsize=10)
                for a, b1, b2, label in zip(x, y2, y3, [x[0] for x in max2nd]):
                    if b2 != 0:
                        plt.text(a, b1 + b2 + 10, '%s' % label, ha='center', va='bottom', fontsize=10)
            plt.xticks(np.arange(12), rotation=20)
            plt.plot(x, y, 'r')
            # plt.gca().set_ylim([0, None])
            plt.savefig(fig_address + originasn)
            plt.clf()
            plt.cla()

def drawROC(noises, record=False):
    fprs = []
    tprs = []
    draw_labels = []

    gs = pygsheets.authorize(service_file='./anomaly_list/AnomalySheets-be83000cb032.json')
    data = gs.open('AnomalousRoutingEvents')
    sheet = data.worksheet_by_title('Threshold_Madmax')

    for noise_sd in noises:
        analyzeAnomalies(plot=False, noise_sd=noise_sd)
        measured = []
        labels = []
        count = 2
        for dir in os.listdir(data_address):
            sub_address = data_address + dir +"/"
            try:
                with open(sub_address+"alerts", mode="r") as input:
                    alerts = ("".join(input.readlines())).split('\n\n')
                with open(sub_address+"labels", mode="r") as input:
                    labels.extend([int(label) for label in input.readlines()])
                # print(dir)
            except:
                continue
            alerts = [alert.strip().split("\n")[-1] for alert in alerts]
            alerts = [int(alert.split(": ")[1]) for alert in alerts]
            maxAlerts = (len(os.listdir(sub_address))-len(alerts)-2)*48
            if len(noises) == 1 and record:
                sheet.update_value('A'+str(count), dir)
                sheet.update_value('B'+str(count), maxAlerts)
                count += 1
            # print(str(dir)+": ")
            # print(len(os.listdir(sub_address))-len(alerts)-2)
            # print()

            alerts = [alert / maxAlerts for alert in alerts]

            measured.extend(alerts)
        draw_label = "NoiseSD={0}_AUC: {1}".format(noise_sd, roc_auc_score(labels, measured))
        draw_labels.append(draw_label)
        fpr, tpr, thresholds = roc_curve(labels, measured)

        i = np.arange(len(tpr))
        roc = pd.DataFrame({'tf': pd.Series(tpr - (1 - fpr), index=i), 'threshold': pd.Series(thresholds, index=i)})
        roc_t = roc.ix[(roc.tf - 0).abs().argsort()[:1]]
        threshold = list(roc_t['threshold'])[0]
        print("Noise_sd={}, optimal threshold={}".format(noise_sd, threshold))

        if len(noises)==1 and record:
            for i in range(count-2):
                sheet.update_value('C'+str(i+2), int(sheet.get_value('B'+str(i+2)))*threshold)

        fprs.append(fpr)
        tprs.append(tpr)
    # plot_roc_curve(fprs, tprs, draw_labels, save_address="../test_generated/ROC_3mad")
    plot_roc_curve(fprs, tprs, draw_labels,
                   caption='Receiver Operating Characteristic (ROC) Curve with $\gamma=$'+str(tolerance_default),
                   save_address=fig_address+"ROC_"+str(tolerance_default)+"mad.png")

def drawSignals(asns="all"):
    for asn in os.listdir(data_address):
        if asns is not "all" and int(asn) not in asns:
            continue
        da = dataAnalyser(data_address, int(asn), plot_signals=True)
        da.main()
