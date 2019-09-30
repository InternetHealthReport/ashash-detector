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
from src.tools import validity_check
validity_check()