#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import pandas as pd
import os 
import wget
import sys
from urllib.parse import urlencode
from pathlib import Path

from jsonapi_client import Filter, Session

API_BASE = "https://www.ebi.ac.uk/metagenomics/api/v1"

params_arr = [
    {
        "experiment_type": "assembly",
        "lineage" : "root:Environmental:Terrestrial"
    },
    {
        "experiment_type": "assembly",
        "lineage" : "root:Environmental:Aquatic:Thermal springs"
    },
    {
        "experiment_type": "assembly",
        "lineage" : "root:Environmental:Aquatic:Aquaculture"        
    },
    {
        "experiment_type": "assembly",
        "lineage" : "root:Environmental:Aquatic:Sediment"        
    },
    {
        "experiment_type": "assembly",
        "lineage" : "root:Environmental:Aquatic:Freshwater:Sediment"        
    },
    {
        "experiment_type": "assembly",
        "lineage" : "root:Environmental:Aquatic:Marine:Sediment"        
    },
    {
        "experiment_type": "assembly",
        "lineage" : "root:Environmental:Aquatic:Marine:Hydrothermal vents"        
    },
    {
        "experiment_type": "assembly",
        "lineage" : "root:Environmental:Aquatic:Marine:Brackish"        
    },
    {
        "experiment_type": "assembly",
        "lineage" : "root:Environmental:Aquatic:Marine:Oil-contaminated sediment"        
    },
]

assembly_file_collection = {}

#Bar progress at download
def bar_progress(current, total, width=80):
  progress_message = "Downloading: %d%% [%d / %d] bytes" % (current / total * 100, current, total)
  # Don't use print() as it will print in new line every time.
  sys.stdout.write("\r" + progress_message)
  sys.stdout.flush()

def metaDataDownloader(sample, tsvfile):
    sample_link = str(sample.url)
    doc = requests.get(sample_link).text
    data = json.loads(doc)
    df = pd.json_normalize(data['data'])
    sample_metadata = df["attributes.sample-metadata"][0]
    pd.json_normalize(sample_metadata).drop(columns = ['unit'], axis = 1).to_csv(tsvfile, sep='\t', index=False, header=False) 

def assemblyDownloader(study, sample_name):
    analyses_urls = study.url

    with Session(analyses_urls) as session:
        for analys in session.iterate(
       	    "analyses"
        ):
            analys_urls = analys.url
            with Session(analys_urls) as s:
                processed_contigs_exist = False
                for link in s.iterate("downloads"):
                    if(link.description.label == 'Processed contigs'):
                        processed_contigs_exist = True
                        response = requests.get(link.url)
                        if response.status_code == 200:
                            url = link.url
                            file_exist = assembly_file_collection.get(url) 
                            if file_exist:
                                print("\nFile already exist create a link")
                                os.symlink(str(Path().absolute()) +"/"+ file_exist, str(Path().absolute()) + "/" + sample_name + "/" + file_exist.split('/')[2])
                            else:
                                print(f"\nDownload 'Processed contigs' [analys: {analys.id} of study:{study.id} for sampele {sample_name}]") # Processed contigs analys: {name_analys}  of study: {study_name} for sampele {sample_name}
                                path = wget.download(url, out=sample_name, bar=bar_progress)
                                assembly_file_collection[url] = "/" + path
                        else:
                            print("file not aviable")

                        break
                if(not processed_contigs_exist):
                    print(f'have no Processed contigs file for analyses of: {analys.id} of study:{study.id} for sampele {sample_name}]')

def goAnnotationDownloader(study, dir_name):
    go_annotation_url = study.url
    with Session(go_annotation_url) as s:
        go_annotation_exist = False
        for link in s.iterate("downloads"):
            if(link.description.label == 'Complete GO annotation'):
                go_annotation_exist = True
                response = requests.get(link.url)
                if response.status_code == 200: 
                    print(f"\ndownload {link.url} to /{dir_name}")
                    wget.download(link.url, out=dir_name, bar=bar_progress)
                else:
                    print("file not aviable")

                break
        if(not go_annotation_exist):
            print(f'have no "Complete GO annotation" file for analyses of {dir_name}')

print("Starting...")

# API call
with Session(API_BASE) as session:

    total_count = 0

    for params in params_arr:

        api_filter = Filter(urlencode(params))


        for sample in session.iterate(
       	    "samples", api_filter
        ):
            total_count = total_count + 1
            
            
            dir_name = sample.id
            if not os.path.exists(dir_name):
                os.mkdir(dir_name)
            
            file_name = ""

            for study in sample.studies:
                assemblyDownloader(study, dir_name)
                print("study:", study.id)
                goAnnotationDownloader(study, dir_name)
                file_name = file_name + study.id + "_"
                print("\n")
            print("\n")

            file_name = file_name + sample.id + ".tsv"

            with open(f"{dir_name}/{file_name}", "w") as tsvfile:
                print(f"meta-data {file_name} is uploading to {dir_name}")
                metaDataDownloader(sample, tsvfile)


    print(f"Data retrieved from the API, total count of samples:{total_count}")