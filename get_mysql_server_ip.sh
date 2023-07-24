#!/bin/bash

vagrant ssh -c "ip a" | grep -E "inet .*eth1" - | tr -s ' ' | cut -d' ' -f3 | cut -d'/' -f1

