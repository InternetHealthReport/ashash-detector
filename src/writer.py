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

save_address = cfg['writer']['save_address']
time_window = cfg['writer']['time_window']
boundary = cfg['writer']['range']

def readCell(cell):
  ret = []
  for data in cell:
    ret.append(str(data).split('\'',1)[1].split('\'')[0])
  return ret

def readAnomalies(boundary):
    anomalies = []
    gs = pygsheets.authorize(service_file='./anomaly_list/AnomalySheets-be83000cb032.json')
    data = gs.open('AnomalousRoutingEvents')
    sheet = data.worksheet_by_title('sheet1')
    range1 = sheet.range(boundary) #'A2:E18'
    for cell in range1:
        data = readCell(cell)
        if len(data[0])>0:
            anomalies.append([int(data[0]), data[1], data[2] if len(data[2])==8 else data[1]])
            # if makelist:
            #     with open("./anomalies", mode="w+") as output:
            #         output.write(','.join(data)+'\n')
    return anomalies

def clearAnomalies(deep=False):
    try:
        os.remove("./anomalies")
    except:
        pass
    if deep:
        shutil.rmtree(save_address)
        os.mkdir(save_address)
    else:
        for dir in os.listdir(save_address):
            address = save_address + dir +"/"
            for file in address:
                if os.path.isfile(file):
                    os.remove(file)
    # if not os.path.exists(fig_address):
    #     os.mkdir(fig_address)

def writeAnomalies(boundary=boundary, all_clear=False):
    ret = []
    clearAnomalies(all_clear)
    anomalies = readAnomalies(boundary)
    pool = ThreadPool(4)
    tasks = []
    for anomaly in anomalies:
        # print(anomaly[0])
        t1, t2, labels = calculateTimeWindow(anomaly[1], anomaly[2])
        # print(t1)
        # print(t2)
        ret.append([anomaly[0], t1, t2])
        tasks.append([anomaly[0], t1, t2, save_address, True, labels])
    pool.map(writingWorker, tasks)
    pool.wait_completion()
    return ret
        # dw = dataWriter(anomaly[0], t1, t2, save_address=save_address)
        # dw.main(False)

# F for forward, N for normal
def calculateTimeWindow(t1, t2, mode='F'):
    startTime = datetime.strptime(t1, '%Y-%m-%d')
    endTime = datetime.strptime(t2, '%Y-%m-%d')
    positive_labels = [1]*int(((endTime-startTime)/timedelta(days=1))+1)
    if mode=='N':
        labels = [0]*int(time_window/2)
        labels.extend(positive_labels)
        labels.extend([0]*int(time_window/2))
        return str(startTime-timedelta(days=time_window)/2)[:10],\
               str(endTime+timedelta(days=time_window)/2)[:10], labels
    if mode=='F':
        labels = [0]*(time_window)
        labels.extend(positive_labels)
        return str(datetime.strptime(t1, '%Y-%m-%d')-timedelta(days=time_window))[:10], t2, labels

def writingWorker(params):
    if len(params) == 3:
        dataWriter(params[0], params[1], params[2]).main(True)
    else:
        dataWriter(params[0], params[1], params[2], params[3], params[4], params[5]).main(False)