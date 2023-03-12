#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import pandas as pd
import os 
import wget
import sys
from urllib.parse import urlencode

from jsonapi_client import Filter, Session

API_BASE = "https://www.ebi.ac.uk/metagenomics/api/v1"

#Bar progress at download
def bar_progress(current, total, width=80):
  progress_message = "Downloading: %d%% [%d / %d] bytes" % (current / total * 100, current, total)
  # Don't use print() as it will print in new line every time.
  sys.stdout.write("\r" + progress_message)
  sys.stdout.flush()


#example
#https://www.ebi.ac.uk/metagenomics/api/v1/analyses?filter&experiment_type=assembly&lineage=root:Environmental:Terrestrial

print("Starting...")

# API call
with Session(API_BASE) as session:

    # configure the filters ?filter&experiment_type=assembly&lineage=root:Environmental:Terrestrial
    params = {
        "experiment_type": "assembly",
        "lineage" : "root:Environmental:Terrestrial"
    }

    api_filter = Filter(urlencode(params))

    # sessions.iterate will take care of the pagination for us
    # get analyses like https://www.ebi.ac.uk/metagenomics/api/v1/analyses
    for analys in session.iterate(
       	"analyses", api_filter
    ):
        

        assembly_name = str(analys.relationships.assembly)[12:]

        file_name = analys.study.id + "_" + analys.sample.id + ".tsv"
        print(file_name)
        with open(f"{file_name}", "w") as tsvfile:
            #make csv with sample-metadata
            sample_link = str(analys.relationships.sample.links.related)
            doc = requests.get(sample_link).text
            data = json.loads(doc)
            df = pd.json_normalize(data['data'])
            sample_metadata = df["attributes.sample-metadata"][0]
            md = pd.json_normalize(sample_metadata).drop(columns = ['unit'], axis = 1).to_csv(tsvfile, sep='\t', index=False, header=False) 


    print("Data retrieved from the API")
