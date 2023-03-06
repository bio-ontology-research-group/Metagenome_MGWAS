#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import json
import pandas as pd
import os 
import wget
import sys

from jsonapi_client import Session

STUDIES_NAME = "MGYS00005725"

STUDIES_API = "https://www.ebi.ac.uk/metagenomics/api/v1/studies/" + STUDIES_NAME


FILE_NAME = "data.csv"

#Bar progress at download
def bar_progress(current, total, width=80):
  progress_message = "Downloading: %d%% [%d / %d] bytes" % (current / total * 100, current, total)
  # Don't use print() as it will print in new line every time.
  sys.stdout.write("\r" + progress_message)
  sys.stdout.flush()


print("Starting...")

# API call
with Session(STUDIES_API) as session:
    for analys in session.iterate(
       	"analyses"
    ):
        dir_name = analys.id
        if not os.path.exists(dir_name):
            os.mkdir(dir_name)
        
        assembly_name = str(analys.relationships.assembly)[12:]

        #download assembly
        processed_contigs_url = analys.url
        with Session(processed_contigs_url) as s:
            processed_contigs_exist = False
            for link in s.iterate("downloads"):
                if(link.description.label == 'Processed contigs'):
                    processed_contigs_exist = True
                    response = requests.get(link.url)
                    if response.status_code == 200: 
                        print(f"\ndownload {link.url} to /{dir_name}")
                        wget.download(link.url, out=dir_name, bar=bar_progress)
                    else:
                        print("file not aviable")

                    break
            if(not processed_contigs_exist):
                    print(f'have no Processed contigs file for analyses of {dir_name}')

        with open(f"{dir_name}/{FILE_NAME}", "w") as csvfile:
            
            #make csv with sample-metadata
            sample_link = str(analys.relationships.sample.links.related)
            doc = requests.get(sample_link).text
            data = json.loads(doc)
            df = pd.json_normalize(data['data'])
            sample_metadata = df["attributes.sample-metadata"][0]
            md = pd.json_normalize(sample_metadata).drop(columns = ['unit'], axis = 1).to_csv(csvfile, index=False, header=False) 


    print("Data retrieved from the API")
