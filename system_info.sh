#!/bin/bash

VM=$(VBoxManage list runningvms | cut -d'"' -f2)

VBoxManage showvminfo "${VM}" | grep -E "Name:|Guest OS|Memory size|CPU exec cap|Number of CPUs|State|SATA Controller (0, 0)|NIC 1|NIC 1 Settings|NIC 1 Rule(0)|NIC 2|OS type" -
