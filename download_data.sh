#!/bin/bash

cd $(dirname $0)

echo -n "> Enter the JTA-Key we've sent you by email: "
read key
key=$(echo $key | tr -dc '[:alnum:]-')

echo ""
echo "> The dataset will be download in $(pwd)."
echo "> Press [ENTER] to start download"
read enter

filename="$(wget -q --show-progress -O - "https://drive.google.com/file/d/$key/view" | sed -n -e 's!.*<title>\(.*\)\ \-\ Google\ Drive</title>.*!\1!p')";
wget -q --show-progress --load-cookies /tmp/cookies.txt "https://docs.google.com/uc?export=download&confirm=$(wget -q --show-progress --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate "https://docs.google.com/uc?export=download&id=$key" -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id=$key" -c -O $filename && rm -rf /tmp/cookies.txt;
echo "> Download completed"

echo "> Unzipping $(realpath $filename)..."
unzip $filename

echo "> Done!"
