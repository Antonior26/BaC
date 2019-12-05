#!/usr/bin/env bash

IFS=$'\n'

# conda activate julia

mentalist list_pubmlst > pubmlst_list.txt

for i in $(cat pubmlst_list.txt | grep -v "^#"); do 
	id=$(echo $i | cut -f1)
	name=$(echo $i | cut -f2 | sed "s/ /_/" | sed -E "s/\s+$//g")
	if [ -f "pubmlst_$name.db" ]; then
		echo pubmlst_$name.db exist 
		continue
	fi
	echo $name
	mentalist download_pubmlst -k 31 -o pubmlst_$name -s $id --db pubmlst_$name.db
done

mentalist list_cgmlst > cgmlst_list.txt

for i in $(cat cgmlst_list.txt | grep -v "^#"); do 
	id=$(echo $i | cut -f1)
	name=$(echo $i | cut -f2 | sed "s/ /_/" | sed -E "s/\s+$//g")
	if [ -f "cgmlst_$name.db" ]; then
		echo cgmlst_$name.db exist 
		continue
	fi
	echo $name
	mentalist download_cgmlst -k 31 -o cgmlst_$name -s $id --db cgmlst_$name.db --threads 4
done

