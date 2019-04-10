from argparse import ArgumentParser

import subprocess
import os

from random import randint

#python Main.py --kubectl=/snap/bin/kubectl --project=cs5052-p2 -m n1-standard-1 -z europe-west4-a -n 2
parser = ArgumentParser()
parser.add_argument("-kc", "--kubectl", required=True, help="Path to your kubectl", metavar="FILE")
#parser.add_argument("-i", "--image", required=True, help="Docker image")
parser.add_argument("-p", "--project", required=True, help="Project Name")
parser.add_argument("-m", "--machinetype", required=True, help="Machine type")
parser.add_argument("-z", "--zone", required=True, help="Zone")
parser.add_argument("-n", "--numnodes", required=True, help="Num nodes")

args = parser.parse_args()

print args

def issueCommand(cmd):
    print "CMD: "," ".join(cmd)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    #out, err = p.communicate()
    #print "STDOUT: ", out
    #print "STDERR: ", err

    o = ""
    e = ""
    print "STDOUT:"
    while True:
        output = p.stdout.readline()
        if output == '' and p.poll() is not None:
            break
        if output:
            o += output
            print output.strip()

    print "STDERR:"
    e = p.stderr.read()
    print e
    rc = p.poll()


    return rc, o, e

def createCluster(clusterPrefix, index, projectName, conf):
    print "CREATE CLUSTER: "
    cmd = ["gcloud", "container", "--project", projectName, "clusters", "create"]

    clusterName = clusterPrefix+str(index)+"-"+str(randint(1000, 10000))
    cmd.append(clusterName)
    cmd.append("--zone")
    cmd.append(conf["zone"])

    cmd.append("--machine-type")
    cmd.append(conf["machineType"])
    
    cmd.append("--num-nodes")
    cmd.append(str(conf["numNodes"]))

    issueCommand(cmd)

    return clusterName


def runBenchmark(clusterName, conf):
    print "RUN BENCHMARK: "
    #TODO It doesnt stream the result
    cmd = ["./PerfKitBenchmarker/pkb.py"]
    cmd.append("--cloud=Kubernetes")
    cmd.append("--kubectl=/snap/bin/kubectl")
    cmd.append("--benchmarks=iperf")
    cmd.append("--kubeconfig=/home/pakawat_nk/.kube/config")
    cmd.append("--image=gcr.io/cs5052-p2/myappmew")

    return issueCommand(cmd)


clusterPrefix = "bm"
configs = [
    {"zone": args.zone, "machineType": args.machinetype, "numNodes": args.numnodes}
    # {"zone": "europe-west4-a", "machineType": "n1-standard-1", "numNodes": 2}
]

index = 1
for c in configs:
    print "CLUSTER CONFIG: "
    print c

    clusterName = createCluster(clusterPrefix, index, args.project, c)
    
    print clusterName 
    issueCommand([
	"gcloud", "compute", "disks", "create", "--project", args.project, "--zone", c["zone"], "--size", "200GB", "mongo-disk"
    ])

    #gcloud compute disks create --project "cs5052-p2" --zone "us-central1-f" --size 200GB mongo-disk


    #clusterName = "bm1-4867"
    issueCommand(["cp", os.path.expanduser('~/.kube/config'), "kubeconfig.yml"])    
    #runBenchmark(clusterName, c)
    index += 1
