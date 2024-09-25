#!/bin/bash
if [ $EUID -ne 0 ]; then
  echo "root only: # $0" 1>&2
  exit 1
fi
# package needed for buildozer
apt update
#apt upgrade

apt install build-essential cmake libtool automake autoconf-archive autoconf pkg-config git zip unzip openjdk-17-jdk 
apt install zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 libffi-dev libltdl-dev libssl-dev
