from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS
import uuid
import pandas as pd
import numpy as np


# get data from table.tsv, prepare and put it in a list
def get_data():
    # read the TSV file
    data = pd.read_csv('table.tsv', sep='\t')

    # data[gps] separate at lat and len
    data['lat'] = data['gps'].str.split(',').str[0]
    data['lon'] = data['gps'].str.split(',').str[1]

    # data['lat'] get number only
    data['lat'] = data['lat'].str.extract('(\d+.\d+)')
    data['lon'] = data['lon'].str.extract('(\d+.\d+)')

    # prepare data for the graph
    data = data.drop(['date'], axis=1)
    data = data.drop(['additional site notes'], axis=1)
    data = data.drop(['ph'], axis=1)
    data = data.drop(['id'], axis=1)
    data = data.drop(['salinity'], axis=1)
    data = data.drop(['gps'], axis=1)

    # clear data from exceptions in site id
    data['site id'] = pd.to_numeric(data['site id'], errors='coerce')
    data = data.dropna(subset=['site id'])
    data = data.reset_index(drop=True)

    # clear data from eceptions in lat and lon
    data['lat'] = pd.to_numeric(data['lat'], errors='coerce')
    data = data.dropna(subset=['lat'])
    data['lon'] = pd.to_numeric(data['lon'], errors='coerce')
    data = data.dropna(subset=['lon'])
    data = data.reset_index(drop=True)

    # named variables of properties
    siteIDList = list(data['site id'])
    latList = list(data['lat'])
    lonList = list(data['lon'])
    tempList = list(data['temperature'])
    humList = list(data['humidity'])
    pressList = list(data['pressure'])
    biomeList = list(data['biome'])
    featureList = list(data['feature'])

    return siteIDList, latList, lonList, tempList, humList, pressList, biomeList, featureList


# get correspondence table from enum.tsv and put it in a list
def get_enum():

    # read the TSV file
    data = pd.read_csv('enum.tsv', sep='\t')

    # prepare data for the graph
    data = data.drop(['definition'], axis=1)

    # drop data with empty or NaN
    data = data.dropna()

    # drop keyword 'code' like not valid
    data = data.loc[data['code'] != 'code']

    correspondence = data.set_index('biome')['code'].to_dict()

    return correspondence


def main():

    # Define namespaces
    SIO = Namespace("http://semanticscience.org/resource/")
    QUDT = Namespace("http://qudt.org/vocab/unit/")
    PATO = Namespace("http://purl.obolibrary.org/obo/PATO_")
    ENVO = Namespace("http://purl.obolibrary.org/obo/ENVO_")

    OBO = Namespace("http://purl.obolibrary.org/obo/")
    GEO = Namespace("http://www.opengis.net/#geosparql")
    WGS = Namespace("http://www.w3.org/2003/01/geo/wgs84_pos#")
    EGP = Namespace("http://w3id.org/eqp/vocab/")
    SCHEMA = Namespace("http://schema.org/")
    PREFIX = Namespace("http://w3id.org/eqp/")

    # Get data from table.tsv
    siteIDList, latList, lonList, tempList, humList, pressList, biomeList, featureList = get_data()

    # Get data from enum.tsv
    correspondence = get_enum()

    # Replace biome names with codes
    for i in range(0, len(biomeList)):
        biomeList[i] = correspondence[biomeList[i]].split(':')[1]

    # Create the graph
    graph = Graph()

    # Add namespaces to the graph
    graph.bind("sio", SIO)
    graph.bind("qudt", QUDT)
    graph.bind("pato", PATO)
    graph.bind("envo", ENVO)
    graph.bind("obo", OBO)
    graph.bind("geo", GEO)
    graph.bind("wgs", WGS)
    graph.bind("schema", SCHEMA)
    graph.bind("", PREFIX)
    graph.bind("egp", EGP)

    # Define the entities
    D1 = PREFIX["D1"]
    DR = PREFIX["DR"]
    S = PREFIX["S"]
    SR1 = PREFIX["1SR1"]
    SR1_GEO = PREFIX["1SR1_geo"]
    EQP = PREFIX["eqp"]
    BORG = PREFIX["borg"]
    KAUST = PREFIX["kaust"]
    ABRR = PREFIX["abrr"]

    # Define the Dataset
    graph.add((D1, RDF.type, SCHEMA["Dataset"]))
    graph.add((D1, RDFS.label, Literal(
        "Empty Quarter Metagenomics Dataset", lang="en")))
    graph.add((D1, RDFS.comment, Literal("", lang="en")))
    graph.add((D1, SCHEMA["identifier"], Literal(
        "EGP-D1")))
    graph.add((D1, SCHEMA["dateCreated"], Literal(
        "2023-04-04T13:00:00Z", datatype=SCHEMA["Date"])))

    # Add the triples to the graph

    for i in range(0, len(siteIDList)):
        siteID = siteIDList[i]
        lat = latList[i]
        lon = lonList[i]
        temp = tempList[i]
        hum = humList[i]
        press = pressList[i]
        biome = biomeList[i]
        feature = featureList[i]

        _pressure = uuid.uuid4()
        _temperature = uuid.uuid4()
        _humidity = uuid.uuid4()
        _pressure_value = uuid.uuid4()
        # Create unique IDs for each entity
        data_record_id = str(uuid.uuid4())
        location_id = str(uuid.uuid4())
        main_entity_id = str(uuid.uuid4())
        geo_id = str(uuid.uuid4())

        # Create the entities
        DR = PREFIX[data_record_id]
        S = PREFIX[location_id]
        SR1 = PREFIX[main_entity_id]
        SR1_GEO = PREFIX[geo_id]

        graph.add((DR, RDF.type, SCHEMA["DataRecord"]))
        graph.add((DR, SCHEMA["dateCreated"], Literal(
            "2023-04-04T13:00:00Z", datatype=SCHEMA["Date"])))
        graph.add((DR, SCHEMA["identifier"], Literal(
            "EGP-D1-S{}".format(int(siteID)))))
        graph.add((DR, SCHEMA["isPartOf"], D1))
        graph.add((DR, SCHEMA["mainEntity"], SR1))

        graph.add((S, RDF.type, GEO["Feature"]))
        graph.add((S, RDF.type, SCHEMA["Location"]))
        graph.add((S, RDF.type, PREFIX["Site"]))
        # push data
        graph.add((S, WGS.long, Literal(lon)))
        graph.add((S, WGS.lat, Literal(lat)))
        graph.add((S, EGP["atm_pressure"], Literal(
            press, datatype=QUDT["MilliBAR"])))
        graph.add((S, EGP["temperature"], Literal(
            temp, datatype=QUDT["DEG_C"])))
        graph.add((S, EGP["humidity"], Literal(hum, datatype=QUDT["PERCENT"])))

        pressure = URIRef(str(_pressure))
        graph.add((S, SIO.hasAttribute, pressure))
        graph.add((S, SIO.hasAttribute, pressure))
        graph.add((pressure, RDF.type, SIO.Measurement))
        # push data
        graph.add((pressure, SIO.hasValue, Literal(press)))
        graph.add((pressure, SIO.hasUnit, QUDT.MilliBAR))
        pressure_value = URIRef(str(_pressure_value))
        graph.add((pressure, SIO.isMeasurementValue, pressure_value))
        graph.add((pressure_value, RDF.type, PATO["0001025"]))

        temperature = URIRef(str(_temperature))
        graph.add((S, SIO.hasAttribute, temperature))
        graph.add((temperature, RDF.type, SIO.Temperature))
        # push data
        graph.add((temperature, SIO.hasValue, Literal(temp)))
        graph.add((temperature, SIO.hasUnit, QUDT.DEG_C))

        humidity = URIRef(str(_humidity))
        graph.add((S, SIO.hasAttribute, humidity))
        graph.add((humidity, RDF.type, SIO.Humidity))
        # push data
        graph.add((humidity, SIO.hasValue, Literal(hum)))
        graph.add((humidity, SIO.hasUnit, QUDT.PERCENT))

        graph.add((SR1, RDF.type, SCHEMA["Sample"]))
        graph.add((SR1, RDF.type, GEO["Feature"]))
        graph.add((SR1, RDF.type, OBO["OBI_0000747"]))
        # push data
        graph.add((SR1, RDFS.label, Literal(f"Sample {siteID} from surface")))
        graph.add((SR1, SCHEMA["identifier"],
                   Literal("{}Sr1".format(int(siteID)))))
        # push data
        graph.add((SR1, WGS.long, Literal(lon)))
        graph.add((SR1, WGS.lat, Literal(lat)))
        # ENVO
        graph.add((SR1, SIO["isLocatedIn"], ENVO[str(biome)]))
        graph.add((SR1, SIO["isAdjacentTo"], ENVO[str(biome)]))
        graph.add((SR1, SIO["isDerivedFrom"], ENVO["00005800"]))
        # push data
        graph.add((SR1, EGP["depth"], Literal("0")))
        graph.add((SR1_GEO, RDF.type, GEO["Geometry"]))
        # push data
        graph.add((SR1_GEO, GEO["asWKT"], Literal(
            f"Point(${lat} ${lon})", datatype=GEO["wktLiteral"])))
        graph.add((SR1, GEO["hasGeometry"], SR1_GEO))

        graph.add((SR1, EGP["collected-at"], S))

        graph.add((EQP, RDF.type, SIO["Project"]))
        graph.add((EQP, RDFS.label, Literal(
            "Empty Quarter Metagenome Sequencing Project")))

        graph.add((BORG, RDF.type, SIO["Group"]))
        graph.add((BORG, SIO.isLocatedIn, KAUST))

        graph.add((KAUST, RDF.type, SIO["University"]))
        graph.add((KAUST, RDFS.label, Literal(
            "King Abdullah University of Science and Technology", lang="en")))
        graph.add((KAUST, ABRR, Literal("KAUST")))

        # Define the relationships
        graph.add((SR1, SCHEMA["isPartOf"], D1))
        graph.add((EQP, SCHEMA["isPartOf"], D1))
        graph.add((D1, SCHEMA["hasPart"], EQP))
        graph.add((BORG, SIO.isLocatedIn, KAUST))
        graph.add((EQP, SIO.isPartOf, BORG))
    # write in turtle format to output file
    graph.serialize(destination='output1.ttl', format='turtle')


if __name__ == '__main__':
    main()
