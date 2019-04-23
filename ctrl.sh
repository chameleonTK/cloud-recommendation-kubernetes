#!/bin/bash

# Author : Pakawat Nakwijit

echo "Welcome to the my cloud recommendation"
KUBECTL=$(which kubectl)

echo "Enter project name: "
read PROJECT_NAME

echo "Enter zome(europe-west4-a): "
read ZONE
if [ -z "$ZONE" ]; then
  ZONE="europe-west4-a"
fi

RANDOMSTR=$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 13 ; echo '')
mkdir /tmp/perfkitbenchmarker/backup_${RANDOMSTR}
mv /tmp/perfkitbenchmarker/runs/* /tmp/perfkitbenchmarker/backup_${RANDOMSTR}

mkdir -p $HOME/bm-result
declare -a machineType=("n1-standard-1" "n1-standard-2" "n1-standard-4" "n1-standard-8" "n1-highcpu-2" "n1-highcpu-4" "n1-highcpu-8" "n1-highmem-2" "n1-highmem-4" "n1-highmem-8")
for m in ${machineType[@]}; do
   echo "Do you want to run with ${m}? (Y/n)"
   read confirm
   if [[ "$confirm" == 'n' ]]; then
     continue
   fi

   python CreateCluster.py --kubectl=${KUBECTL} --project=${PROJECT_NAME} -m ${m} -z ${ZONE} -n 2
   ./PerfKitBenchmarker/pkb.py --cloud=Kubernetes --kubectl=/snap/bin/kubectl --benchmarks=iperf --kubeconfig=${HOME}/.kube/config --json_path=${HOME}/bm-result/${m}.json
done
 
#cp -r /tmp/perfkitbenchmarker/runs results
