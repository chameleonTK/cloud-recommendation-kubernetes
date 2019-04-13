# Cloud Recommendation system on Kubernetes

It is an part of [CS5052](https://info.cs.st-andrews.ac.uk/student-handbook/modules/CS5052.html) at University of St. Andrews.

## Installing

### Setup PerfKit Benchmarker
1. Install python2.7 and vitualenv; `pip install vitualenv`
2. Create isolated Python environment for the system;
`virtualenv -p /usr/bin/python2.7 env`
3. Start using your env; `source env/bin/activate`
4. Follow instructions; [PerfKit Benchmarker](https://github.com/GoogleCloudPlatform/PerfKitBenchmarker)

### Setup Google Cloud SDK and `kubectl`
5. Install `gcloud`; [Follow this link](https://cloud.google.com/sdk/install)
6. Install `kubectl`; [Follow this link](https://kubernetes.io/docs/tasks/tools/install-kubectl/)
7. Run `gcloud init`; It will prompt a dialog to log in and set your project.
8. Enable Google Cloud API; Kubernetes API, Billing API

### Setup your own application
9. build and push your own docker to Google's Container regirtry
10. write your `kubernates configuration files` [Follow this link](https://kubernetes.io/docs/concepts/configuration/manage-compute-resources-container/)

## Running
1. Run:

```bash
$ ./ctrl.sh
```

### Usefull links
* [Configuring cluster access for kubectl
](https://cloud.google.com/kubernetes-engine/docs/how-to/cluster-access-for-kubectl)

### Todos
* Support multiple endpoints (benchmark when it exploits loadbalancer)
* Clean up pods


## Author
[Pakawat Nakwijit](http://curve.in.th); An ordinary programmer who would like to share and challange himself. It is a part of my 2018 tasks to open source every projects in my old treasure chest with some good documentation. 

## License
This project is licensed under the terms of the MIT license.

