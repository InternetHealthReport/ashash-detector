# ashash-detector
Detecting routing anomalies
## Setting parameters through init.py
Firstly, you may need to clear all the parameters and restore some of them into defaults. Use code:
```
python init.py -c
```
### Parameters in writer
| Command | Meaning | Example Values |
| ------- | ------- | -------------- |
| -wm | mode for writer | L/D |
| -wr | list range for writer in mode L | A2:E5 |
| -wsa | save address for writer | "./data/" |
| -wt | time window for writer | 30 |
| -wa | as number(s) for writer | 13335,900 |
| -we | end time for writer | 2019-11-01 |
- `-wm` is the keyword to determine writer's behaviour. "L" for reading anomaly list while "D" for reading according to dates.
- `-wr` is required if mode is set to "L".
- `-wt` and `-we` is required if mode is set to "D".
### Parameters in Analyser
| Command | Meaning | Example Values |
| ------- | ------- | -------------- |
| -am | mode for analyser | L/M |
| -asa | save address for analyser | "./result/" |
| -afa | save address for figures produced by analyser | "./results/figures/"
| -aa | as number(s) for analyser | 13335,900/all |
| -ama | minimum anomalies threshold for analyser | 0 |
| -ans | standard deviation of white noise for Madmax | 0.02 |
| -at | tolerance of safe zone for Madmax | 5 |
| -ad | threshold of fingerprints for LGhash | 3 |
- `-am` is the keyword to determine analyser's behaviour. "L" for using LGhash while "M" for using Madmax.
- `-aa` accept either normal integers sequence which is the same as `-wa` or string "all" 
which indicate analysing all ASes collected by writer.
## Run both writer and analyser through main.py
After setting all the parameters properly, run the following code:
```
python main.py
```
-Values other than "L","D" found in `-wm` will mute writer's function. Similar to analyser.
