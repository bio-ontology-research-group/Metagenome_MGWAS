import urllib.request
import json
import pandas as pd
import os 

pd.set_option('display.max_rows', 5000)

def getDumpFilename(biome):
    return "mgnify_"+biome.replace(":","_").lower()+".pkl"


def downloadBiomeSamples(biome = 'root:Environmental:Terrestrial', dump_filename = ''):
    try:
        biome.__len__
    except NameError:
        print("biome not defined")
        
    url = f'https://www.ebi.ac.uk/metagenomics/api/v1/biomes/{biome}/samples?page=1'
    if not dump_filename:
        dump_filename = getDumpFilename(biome)

    last_page = 'unknown'
    parse = True
    while parse == True:
        print("page "+(url.split("=")[1])+" of "+last_page)

        doc = urllib.request.urlopen(url).read()
        data = json.loads(doc)
        df = pd.json_normalize(data['data'])

        if 'all' in locals():
            all = pd.concat([all, df])#, ignore_index=True)
        else: 
            all = df
    
        # check for the next page
        if data['links']['next']:
            # e.g. "next": "https://www.ebi.ac.uk/metagenomics/api/v1/biomes/root:Environmental:Terrestrial/samples?page=2",
            url = data['links']['next']
            last_page = data['links']['last'].split("=")[1]            
            continue
        else:
            break

    all.to_pickle(dump_filename)
    return True


biome = 'root:Environmental:Terrestrial'
folder =  os.getcwd() + "/data/" 
file = folder + getDumpFilename(biome)
if not os.path.isfile(file):
    try:
        downloadBiomeSamples()
    except:
        print("Error in downloading content")
        exit

data = pd.read_pickle(file)
# data.columns()

# Index(['type', 'id', 'attributes.latitude', 'attributes.longitude', 'attributes.biosample', 'attributes.sample-metadata', 'attributes.accession', 'attributes.analysis-completed', 'attributes.collection-date', 'attributes.geo-loc-name', 'attributes.sample-desc', 'attributes.environment-biome', 'attributes.environment-feature', 'attributes.environment-material', 'attributes.sample-name', 'attributes.sample-alias', 'attributes.host-tax-id', 'attributes.species', 'attributes.last-update', 'relationships biome.data.type', 'relationships.biome.data.id', 'relationships.biome.links.related', 'relationships.runs.links.related', 'relationships.studies.links.related', 'relationships.studies.data', 'links.self'], dtype='object')

features = ["attributes.environment-biome","attributes.environment-feature","attributes.environment-material"]
for f in features:
    l = data.groupby(f).size()
    l.to_frame().to_pickle(f'{folder}{f}.pkl')
    l.to_csv(f'{folder}{f}.csv',';')



