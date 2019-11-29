# import yaml
#
# with open("config.yml", 'r') as ymlfile:
#     cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
#
# print(type(cfg['writer']['asns']))
#
# # from src.writer import writeAnomalies
# # writeAnomalies("A2:E5")

# a = [1, 2]
# # a. append(a)
# # print(a)
# b = []
# for aa in a:
#     b.append([aa].extend())
# from src.tools import validity_check
# validity_check()
# import numpy as np
# a = [1, 2, 3]
# b = [x/10 for x in a]
# print(type(b[0]))
# c = np.array(b)
# print(type(c[0]))

# import numpy as np
# data = np.loadtxt("data/701/701_2914", delimiter="\n", unpack=True)
# print(np.median([np.abs(data-np.median(data))]))
# data += np.random.normal(0, 0.02, len(data))
# print(np.median([np.abs(data-np.median(data))]))

# import numpy as np
# a = np.array([1]*20)
# print(a.reshape((-1, 4)))

# import numpy as np
# import pandas as pd
# import os
# from datetime import datetime, timedelta
# from src.hegemony import Hegemony
# from src.tools import ts2int
# import shutil
# save_address = "./data/"
#
# class dataWriter1():
#     def __init__(self, originasn, day1, day2, save_address=save_address, labeled=False, labels=[]):
#
#         self.originasn = originasn
#         self.startdate = day1
#         self.enddate = day2
#         self.save_address = save_address
#         self.labeled = labeled
#         self.labels = labels
#
#         if not os.path.exists(self.save_address):
#             os.mkdir(self.save_address)
#         if not os.path.exists(self.save_address+'/'+str(self.originasn)):
#             os.mkdir(self.save_address +'/' + str(self.originasn))
#         self.save_address = self.save_address + str(self.originasn) + '/'
#         d1 = datetime.strptime(self.startdate, '%Y-%m-%d')
#         d2 = datetime.strptime(self.enddate, '%Y-%m-%d')
#         self.dates = [str(d1)[:10]]
#         while d1!=d2:
#             d1 += timedelta(days=1)
#             self.dates.append(str(d1)[:10])
#         self.hegeTable = None
#         self.hegeDict = {}
#         self.lostMark = {}
#         for date in self.dates:
#             self.lostMark[date] = [0]*96
#
#     def main(self):
#         for date in self.dates:
#             self.collect(date)
#         self.fillLost()
#         self.write()
#
#     def collect(self, date):
#         print("Collecting data: " + str(self.originasn) + " on " + date)
#         save_address = self.save_address + date + '/'
#         if os.path.exists(save_address):
#             shutil.rmtree(save_address)
#         os.mkdir(save_address)
#         hege = Hegemony(originasns=self.originasn, start=date + ' 00:00', end=date + ' 23:59')
#
#         for r in hege.get_results():
#             for data in r:
#                 if data['originasn'] == data['asn']:
#                     continue
#                 key = str(data['originasn']) + '_' + str(data['asn'])
#                 ts = ts2int(data['timebin'])
#                 if key in self.hegeDict.keys():
#                     self.hegeDict[key][ts] = data['hege']
#                 else:
#                     self.hegeDict[key] = [0] * 96
#                     self.hegeDict[key][ts] = data['hege']
#         for key in self.hegeDict.keys():
#             self.hegeDict[key] = np.array(self.hegeDict[key])
#         if len(self.hegeDict.keys())==0:
#             data = {date:np.array([0]*96)}
#             data = pd.DataFrame([data], index=["Drop"])
#         else:
#             data = pd.DataFrame([self.hegeDict], index=[date]).T
#         if self.hegeTable is None:
#             self.hegeTable = data
#         else:
#             self.hegeTable = pd.concat([self.hegeTable, data], axis=1, sort=False)
#         self.hegeDict.clear()
#
#         hege = Hegemony(originasns=0, asns=[1299, 174, 3356], start=date + ' 00:00', end=date + ' 23:59')
#         for r in hege.get_results():
#             for data in r:
#                 ts = ts2int(data['timebin'])
#                 self.lostMark[date][ts] += data['hege']
#         self.lostMark[date] = np.array([x!=0 for x in self.lostMark[date]])
#
#     def fillLost(self):
#         for col in self.hegeTable.columns:
#             for row in self.hegeTable.loc[self.hegeTable[col].isnull(), col].index:
#                 self.hegeTable.at[row, col] = np.array([0]*96)
#         # self.hegeTable.fillna(np.array([0]*96))
#         self.hegeTable.drop('Drop', inplace=True)
#         # lostnum = 0
#         # for key in self.lostMark.keys():
#         #     lostnum += sum(1 for x in self.lostMark[key] if x)
#         medians = {}
#         for key in self.hegeTable.index:
#             medians[key] = []
#             for date in self.dates:
#                 medians[key].extend(list(self.hegeTable.loc[key, date][self.lostMark[date]]))
#             medians[key] = np.median(medians[key])
#         for key in self.hegeTable.index:
#             for date in self.dates:
#                 self.hegeTable.at[key, date] = self.hegeTable.loc[key, date] + np.array(np.float64(1)-self.lostMark[date])*medians[key]
#
#     def write(self):
#         for key in self.hegeTable.index:
#             allData = []
#             for date in self.dates:
#                 data = [str(x) for x in self.hegeTable.loc[key, date]]
#                 allData.extend(data)
#                 with open(self.save_address+date+"/"+key, mode="w+") as output:
#                     output.write("\n".join(data))
#             with open(self.save_address+key, mode="w+") as output:
#                 output.write("\n".join(allData))


# a = [{"a":[1, 2, 3], "b":[4, 5, 6]}]
# b = [{"b":[1, 2, 3], "c":[4, 5, 6]}]
# a = pd.DataFrame(a, index=["a"]).T
# b = pd.DataFrame(b, index=["b"]).T
# print(pd.concat([a, b], axis=1))
# a = np.arange(100)
# print(a)
# a = np.array([x>50 for x in a])
# print(a)
# print(1-a)
# testWriter = dataWriter1(396531, '2019-06-10', '2019-06-24')
# testWriter.main()

# a = np.array([0]*10)
# d = dict()
# d["a"] = a
# d["a"][0] = 1
# print(d["a"])

from src.analyser import drawROC
from src.LGhash import drawROC_extended

# drawROC([1e-2, 2e-2, 5e-2, 1e-1])
# drawROC([1e-2], True)
drawROC_extended(originasns=None, parameters=[(1, 1)], record=True)