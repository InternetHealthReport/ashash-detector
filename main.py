import yaml
from src.writer import writeAnomalies, writingWorker
from src.tools import ThreadPool, validity_check

with open("config.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)

if cfg['writer']['mode']=='L': #List
    print("Writing according to the list")
    writeAnomalies(cfg['writer']['range'])
elif cfg['writer']['mode'] == 'D': #Dates
    print("Writing according to dates")
    if type(cfg['writer']['asns']) is int:
        asns = [cfg['writer']['asns']]
    else:
        asns = [int(x) for x in cfg['writer']['asns'].split(",")]
    # start = cfg['writer']['start']
    from datetime import timedelta
    end = cfg['writer']['end']
    start = str(end - timedelta(days=cfg['writer']['time_window']-1))[:10]
    params = []
    for asn in asns:
        param = [asn]
        param.extend([start, str(end)])
        params.append(param)
    pool = ThreadPool(4)
    pool.map(writingWorker, params)
    pool.wait_completion()
    validity_check()
else:
    pass

if cfg['analyser']['mode'] == 'M': #Madmax
    print("Analysing using Madmax")
    from src.analyser import analyzeAnomalies
    analyzeAnomalies()
elif cfg['analyser']['mode'] == 'L': #LGhash
    print("Analysing using LGhash")
    from src.LGhash import hegemonyPipe, graphMonitor
    asns = cfg['analyser']['asns']
    for asn in asns:
        graphMonitor(hegemonyPipe(original_dir=cfg['writer']['save_address'], scope=asn), 1, 1)
else:
    pass