import json
from matplotlib.ticker import FuncFormatter
import matplotlib.pyplot as plt
import numpy as np


machineTypes = [
    "n1-standard-1",
    "n1-standard-2",
    "n1-standard-4",
    "n1-standard-8",
    "n1-highcpu-2",
    "n1-highcpu-4",
    "n1-highcpu-8",
    "n1-highmem-2",
    "n1-highmem-4",
    "n1-highmem-8"
]

#In benchmark, we used 2 nodes; 1460 hours per month
cost = {
    "n1-standard-1": {"totalPerMonth": 62.55},
    "n1-standard-2": {"totalPerMonth": 125.09},
    "n1-standard-4": {"totalPerMonth": 250.19},
    "n1-standard-8": {"totalPerMonth": 500.37},
    "n1-highcpu-2": {"totalPerMonth": 93.21},
    "n1-highcpu-4": {"totalPerMonth": 186.41},
    "n1-highcpu-8": {"totalPerMonth": 372.83},
    "n1-highmem-2": {"totalPerMonth": 155.65},
    "n1-highmem-4": {"totalPerMonth": 311.30},
    "n1-highmem-8": {"totalPerMonth": 622.60},
}

def getParams(r):
    value = {"value": r["value"]}
    for k in r["labels"].split(","):
        s = k.replace("|", "").split(":")
        if "runtime_in_seconds" == s[0]:
            value["runtime_in_seconds"] = int(s[1])
        elif  "sending_thread_count" == s[0]:
            value["sending_thread_count"] = int(s[1])
        elif  "vm_1_image" == s[0]:
            value["vm_1_image"] = (s[1])
        elif  "vm_1_num_cpus" == s[0]:
            value["vm_1_num_cpus"] = int(s[1])
        elif  "vm_1_os_info" == s[0]:
            value["vm_1_os_info"] = (s[1])

    return value

def getResults():
    results = {}
    for m in machineTypes:
        fileName = "results/ab/"+m+"/perfkitbenchmarker_results.json"
        results[m] = {
            "rps" : [],         #Requests per second
            "t90": [],          #90th percentile of waiting time
            "ab_e2e":[],        #AB's End to End Runtime
            "tp": [],           #network thoughput
            "iperf_e2e":[],     #iperf's End to End Runtime
        }
        with open(fileName) as fin:
            for line in fin:
                r = json.loads(line)

                value = getParams(r)
                if r["metric"] == "Requests per sec":
                    results[m]["rps"].append(value)
                elif r["metric"] == "Longest waiting time":
                    results[m]["t90"].append(value)
                elif r["metric"] == "End to End Runtime":
                    results[m]["ab_e2e"].append(value)
                else:
                    print(r["metric"])
        
        fileName = "results/iperf/"+m+"/perfkitbenchmarker_results.json"
        with open(fileName) as fin:
            for line in fin:
                r = json.loads(line)

                value = getParams(r)


                if r["metric"] == "Throughput":
                    results[m]["tp"].append(value)
                elif r["metric"] == "End to End Runtime":
                    results[m]["iperf_e2e"].append(value)
                else:
                    print(r["metric"])

    return results


results = getResults()
i = np.arange(len(machineTypes))
thoughput = []
for m in machineTypes:
    tp = -1
    for v in results[m]["tp"]:
        tp = max(tp, v["value"])
    thoughput.append(tp)

color = ["#cc0000", "#b20000", "#990000", "#7f0000"]
color.extend(["#135ca4", "#10518f", "#0e457b"])
color.extend(["#005000", "#004600", "#003c00"])

# plt.subplot(3, 1, 1)
ax = plt.subplot(1,1,1)
ax.bar(machineTypes, thoughput, color=color)
# plt.title('Cloud benchmark')
plt.ylabel('Network thoughputs (Mbits/sec)')
handles, labels = ax.get_legend_handles_labels()
plt.xticks(i, machineTypes, rotation='vertical')
plt.tight_layout()
plt.show()


xCon = []

machineSet = [
    {"name": "n1-standard", "machines": machineTypes[0:4]},
    {"name": "n1-highcpu", "machines": machineTypes[4:7]},
    {"name": "n1-highmem", "machines": machineTypes[7:]}
]

index = 0
gindex = 1
lines = []
xCon = []
yConByMachine = {}
for s in machineSet:
    mm = s["machines"]
    ax = plt.subplot(3, 1, gindex)
    if gindex==2:
        ax.set_ylabel('#requests per second')
    
    if gindex==3:
        ax.set_xlabel('#concurrent clients')
    for m in mm:
        tp = []

        rps = sorted(results[m]["rps"], key=lambda x: x["sending_thread_count"])
        sumval = {}
        for v in rps:
            if v["sending_thread_count"] in sumval:
                sumval[v["sending_thread_count"]] += v["value"]
            else:
                sumval[v["sending_thread_count"]] = v["value"]

        xCon = sorted(sumval.keys())    
        yCon = []    
        for x in xCon:
            val = sumval[x]*0.5
            yCon.append(val)

        yConByMachine[m] = yCon
        line = ax.plot(xCon, yCon, label=m, color=color[index])

        index += 1
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels)
    gindex +=1
plt.show()


gindex = 1
ax = None
for r in [2, 4, 6]:
    ax = plt.subplot(3, 1, gindex)
    y = []
    if gindex==1:
        plt.title('Requests per dollar at different number of concurrent clients')
    for m in machineTypes:
        tp = []

        y.append(int(yConByMachine[m][r]/cost[m]["totalPerMonth"]))

        index += 1

    ax.bar(machineTypes, y, color=color)
    gindex +=1
    ax.set_ylabel("At "+str(xCon[r])+" clients")
    ax.set_xticklabels([])
    ax.set_ylim([0,10])

plt.xticks(i, machineTypes, rotation='vertical')
plt.tight_layout()

plt.show()

gindex = 1
ax = None
for r in [2, 4, 6]:
    ax = plt.subplot(3, 1, gindex)
    y = []
    if gindex==1:
        plt.title('#requests load at different number of concurrent clients')
    for m in machineTypes:
        tp = []

        y.append(int(yConByMachine[m][r]))

        index += 1

    ax.bar(machineTypes, y, color=color)
    gindex +=1
    ax.set_ylabel("At "+str(xCon[r])+" clients")
    ax.set_xticklabels([])
    ax.set_ylim([0,1500])

plt.xticks(i, machineTypes, rotation='vertical')
plt.tight_layout()

plt.show()


# fig, ax = plt.subplots()
# plt.bar(x, money)
# plt.xticks(x, ('Bill', 'Fred', 'Mary', 'Sue'))
# plt.show()