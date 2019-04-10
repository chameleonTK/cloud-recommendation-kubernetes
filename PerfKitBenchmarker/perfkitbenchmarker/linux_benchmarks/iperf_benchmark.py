# Copyright 2014 PerfKitBenchmarker Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Runs plain Iperf.

Docs:
http://iperf.fr/

Runs Iperf to collect network throughput.
"""

import logging
import re

from perfkitbenchmarker import configs
from perfkitbenchmarker import flags
from perfkitbenchmarker import sample
from perfkitbenchmarker import vm_util

flags.DEFINE_integer('iperf_sending_thread_count', 1,
                     'Number of connections to make to the '
                     'server for sending traffic.',
                     lower_bound=1)
flags.DEFINE_integer('iperf_runtime_in_seconds', 60,
                     'Number of seconds to run iperf.',
                     lower_bound=1)
flags.DEFINE_integer('iperf_timeout', None,
                     'Number of seconds to wait in '
                     'addition to iperf runtime before '
                     'killing iperf client command.',
                     lower_bound=1)

FLAGS = flags.FLAGS

BENCHMARK_NAME = 'iperf'
BENCHMARK_CONFIG = """
iperf:
  description: Run iperf
  vm_groups:
    vm_1:
      vm_spec: *default_single_core
    vm_2:
      vm_spec: *default_single_core
"""

#IPERF_PORT = 20000
IPERF_PORT = 5000
IPERF_RETRIES = 5


def GetConfig(user_config):
  return configs.LoadConfig(BENCHMARK_CONFIG, user_config, BENCHMARK_NAME)


def Prepare(benchmark_spec):
  """Install iperf and start the server on all machines.

  Args:
    benchmark_spec: The benchmark specification. Contains all data that is
        required to run the benchmark.
  """
  vms = benchmark_spec.vms
  if len(vms) != 2:
    raise ValueError(
        'iperf benchmark requires exactly two machines, found {0}'.format(len(
            vms)))

  for vm in vms:
    vm.Install('iperf')
    if vm_util.ShouldRunOnExternalIpAddress():
      vm.AllowPort(IPERF_PORT)
    stdout, _ = vm.RemoteCommand(('nohup iperf --server --port %s &> /dev/null'
                                  '& echo $!') % IPERF_PORT)
    # TODO store this in a better place once we have a better place
    vm.iperf_server_pid = stdout.strip()


#@vm_util.Retry(max_retries=IPERF_RETRIES)
def _RunIperf(sending_vm, receiving_vm, receiving_ip_address, ip_type, thread_count = 1):
  """Run iperf using sending 'vm' to connect to 'ip_address'.

  Args:
    sending_vm: The VM sending traffic.
    receiving_vm: The VM receiving traffic.
    receiving_ip_address: The IP address of the iperf server (ie the receiver).
    ip_type: The IP type of 'ip_address' (e.g. 'internal', 'external')
  Returns:
    A Sample.
  """
  iperf_cmd = ('iperf --client %s --port %s --format m --time %s -P %s' %
               (receiving_ip_address, IPERF_PORT,
                FLAGS.iperf_runtime_in_seconds,
                thread_count))
  # the additional time on top of the iperf runtime is to account for the
  # time it takes for the iperf process to start and exit
  timeout_buffer = FLAGS.iperf_timeout or 30 + thread_count
  stdout, _ = sending_vm.RemoteCommand(iperf_cmd, should_log=True,
                                       timeout=FLAGS.iperf_runtime_in_seconds +
                                       timeout_buffer, on_host=True)

  # Example output from iperf that needs to be parsed
  # STDOUT: ------------------------------------------------------------
  # Client connecting to 10.237.229.201, TCP port 5001
  # TCP window size: 0.04 MByte (default)
  # ------------------------------------------------------------
  # [  6] local 10.76.234.115 port 53527 connected with 10.237.229.201 port 5001
  # [  3] local 10.76.234.115 port 53524 connected with 10.237.229.201 port 5001
  # [  4] local 10.76.234.115 port 53525 connected with 10.237.229.201 port 5001
  # [  5] local 10.76.234.115 port 53526 connected with 10.237.229.201 port 5001
  # [ ID] Interval       Transfer     Bandwidth
  # [  4]  0.0-60.0 sec  3730 MBytes  521.1 Mbits/sec
  # [  5]  0.0-60.0 sec  3499 MBytes   489 Mbits/sec
  # [  6]  0.0-60.0 sec  3044 MBytes   425 Mbits/sec
  # [  3]  0.0-60.0 sec  3738 MBytes   522 Mbits/sec
  # [SUM]  0.0-60.0 sec  14010 MBytes  1957 Mbits/sec

  thread_values = re.findall(r'\[SUM].*\s+(\d+\.?\d*).Mbits/sec', stdout)
  if not thread_values:
    # If there is no sum you have try and figure out an estimate
    # which happens when threads start at different times.  The code
    # below will tend to overestimate a bit.
    thread_values = re.findall('\[.*\d+\].*\s+(\d+\.?\d*).Mbits/sec', stdout)

    if len(thread_values) != thread_count:
      raise ValueError('Only %s out of %s iperf threads reported a'
                       ' throughput value.' %
                       (len(thread_values), thread_count))

  total_throughput = 0.0
  for value in thread_values:
    total_throughput += float(value)

  metadata = {
      # The meta data defining the environment
      'receiving_machine_type': receiving_vm.machine_type,
      'receiving_zone': receiving_vm.zone,
      'sending_machine_type': sending_vm.machine_type,
      'sending_thread_count': thread_count,
      'sending_zone': sending_vm.zone,
      'runtime_in_seconds': FLAGS.iperf_runtime_in_seconds,
      'ip_type': ip_type
  }
  return sample.Sample('Throughput', total_throughput, 'Mbits/sec', metadata)


#@vm_util.Retry(max_retries=IPERF_RETRIES)
def _RunAB(sending_vm, receiving_vm, receiving_ip_address, ip_type, thread_count = 1):
  """Run iperf using sending 'vm' to connect to 'ip_address'.

  Args:
    sending_vm: The VM sending traffic.
    receiving_vm: The VM receiving traffic.
    receiving_ip_address: The IP address of the iperf server (ie the receiver).
    ip_type: The IP type of 'ip_address' (e.g. 'internal', 'external')
  Returns:
    A Sample.
  """
  ab_cmd = ('ab -k -c %s -n %s http://%s/' % (thread_count, 2000, receiving_ip_address))
  # the additional time on top of the iperf runtime is to account for the
  # time it takes for the iperf process to start and exit
  timeout_buffer = FLAGS.iperf_timeout or 10
  stdout, _ = sending_vm.RemoteCommand(ab_cmd, should_log=True,
                                       timeout=FLAGS.iperf_runtime_in_seconds +
                                       timeout_buffer, on_host=True)

  # This is ApacheBench, Version 2.3 <$Revision: 1807734 $>
  # Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
  # Licensed to The Apache Software Foundation, http://www.apache.org/

  # Benchmarking 35.204.84.116 (be patient)
  # Completed 200 requests
  # Completed 400 requests
  # Completed 600 requests
  # Completed 800 requests
  # Completed 1000 requests
  # Completed 1200 requests
  # Completed 1400 requests
  # Completed 1600 requests
  # Completed 1800 requests
  # Completed 2000 requests
  # Finished 2000 requests


  # Server Software:        
  # Server Hostname:        35.204.84.116
  # Server Port:            80

  # Document Path:          /
  # Document Length:        660 bytes

  # Concurrency Level:      1
  # Time taken for tests:   25.586 seconds
  # Complete requests:      2000
  # Failed requests:        0
  # Keep-Alive requests:    2000
  # Total transferred:      1648000 bytes
  # HTML transferred:       1320000 bytes
  # Requests per second:    78.17 [#/sec] (mean)
  # Time per request:       12.793 [ms] (mean)
  # Time per request:       12.793 [ms] (mean, across all concurrent requests)
  # Transfer rate:          62.90 [Kbytes/sec] received

  # Connection Times (ms)
  #               min  mean[+/-sd] median   max
  # Connect:        0    0   0.3      0      12
  # Processing:    12   13   1.1     13      37
  # Waiting:       12   13   1.1     12      37
  # Total:         12   13   1.2     13      37

  # Percentage of the requests served within a certain time (ms)
  #   50%     13
  #   66%     13
  #   75%     13
  #   80%     13
  #   90%     13
  #   95%     14
  #   98%     16
  #   99%     18
  # 100%     37 (longest request)

  thread_values = re.findall(r'Requests per second:.*\s+(\d+\.?\d*).\[#\/sec\] \(mean\)', stdout)

  total_throughput = 0.0
  for value in thread_values:
    total_throughput += float(value)

  metadata = {
      # The meta data defining the environment
      'receiving_machine_type': receiving_vm.machine_type,
      'receiving_zone': receiving_vm.zone,
      'sending_machine_type': sending_vm.machine_type,
      'sending_thread_count': thread_count,
      'sending_zone': sending_vm.zone,
      'runtime_in_seconds': FLAGS.iperf_runtime_in_seconds,
      'ip_type': ip_type
  }

  long_request_values = re.findall(r'99%\s+(\d+\.?\d*)', stdout)
  n_long_req = 0.0
  for value in long_request_values:
    n_long_req += float(value)

  return [
    sample.Sample('Requests per sec', total_throughput, '#/sec', metadata),
    sample.Sample('Longest waiting time', n_long_req, 'ms', metadata)
  ]

def Run(benchmark_spec):
  """Run iperf on the target vm.

  Args:
    benchmark_spec: The benchmark specification. Contains all data that is
        required to run the benchmark.

  Returns:
    A list of sample.Sample objects.
  """
  vms = benchmark_spec.vms
  results = []

  logging.info('Iperf Results:')

  # Send traffic in both directions
  for sending_vm, receiving_vm in vms, reversed(vms):
    for p in [1, 10, 20, 40]:
      try:
        r = _RunIperf(sending_vm, receiving_vm, receiving_vm.ip_address, 'external', thread_count = p)
        results.append(r)
      except Exception as e:
        metadata = {
            # The meta data defining the environment
            'receiving_machine_type': receiving_vm.machine_type,
            'receiving_zone': receiving_vm.zone,
            'sending_machine_type': sending_vm.machine_type,
            'sending_thread_count': p,
            'sending_zone': sending_vm.zone,
            'runtime_in_seconds': FLAGS.iperf_runtime_in_seconds,
            'ip_type': "external"
        }

        results.append(sample.Sample('Throughput', 0, 'Mbits/sec', metadata))

  logging.info('AB Results:')
  
  # Stress test
  for sending_vm, receiving_vm in vms, reversed(vms):
    for p in [5, 10, 50, 100, 200, 500, 1000]:
      try:
        r = _RunAB(sending_vm, receiving_vm, receiving_vm.ip_address, 'external', thread_count = p)
        results.extend(r)
      except Exception as e:
        metadata = {
            # The meta data defining the environment
            'receiving_machine_type': receiving_vm.machine_type,
            'receiving_zone': receiving_vm.zone,
            'sending_machine_type': sending_vm.machine_type,
            'sending_thread_count': p,
            'sending_zone': sending_vm.zone,
            'runtime_in_seconds': FLAGS.iperf_runtime_in_seconds,
            'ip_type': "external"
        }

        results.append(sample.Sample('Requests per sec', -1, '#/sec', metadata))
        
  return results


def Cleanup(benchmark_spec):
  """Cleanup iperf on the target vm (by uninstalling).

  Args:
    benchmark_spec: The benchmark specification. Contains all data that is
        required to run the benchmark.
  """
  vms = benchmark_spec.vms
  for vm in vms:
    vm.RemoteCommand('kill -9 ' + vm.iperf_server_pid, ignore_failure=True)
