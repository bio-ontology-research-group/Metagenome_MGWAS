from rdflib import Graph, Namespace, URIRef, Literal, XSD
from rdflib.namespace import RDF, RDFS
from rdflib.tools.rdf2dot import rdf2dot
import uuid
import pandas as pd


# get data from table.tsv, prepare and put it in a list
def get_data():
    # read the xlsx file
    data = pd.read_excel(
        'Empty Quarter Project site and samples.xlsx', sheet_name='sites')

    # data[gps] separate at lat and len
    data['lat'] = data['gps'].str.split(',').str[0]
    data['lon'] = data['gps'].str.split(',').str[1]

    # data['lat'] get number only
    data['lat'] = data['lat'].str.extract('(\d+.\d+)')
    data['lon'] = data['lon'].str.extract('(\d+.\d+)')

    # prepare data for the graph
    data = data.drop(['additional site notes'], axis=1)
    data = data.drop(['ph'], axis=1)
    data = data.drop(['id'], axis=1)
    data = data.drop(['salinity'], axis=1)
    data = data.drop(['gps'], axis=1)

    # clear data from exceptions in site
    data['site'] = pd.to_numeric(data['site'], errors='coerce')
    data = data.dropna(subset=['site'])
    data = data.reset_index(drop=True)

    # clear data from eceptions in lat and lon
    data['lat'] = pd.to_numeric(data['lat'], errors='coerce')
    data = data.dropna(subset=['lat'])
    data['lon'] = pd.to_numeric(data['lon'], errors='coerce')
    data = data.dropna(subset=['lon'])
    data = data.reset_index(drop=True)

    # convert date and time to ISO 8601
    data['date'] = data['date'].astype(
        str) + 'T' + data['time'].astype(str) + '+03:00'
    data = data.drop(['time'], axis=1)

    # named variables of properties
    siteIDList = list(data['site'])
    dateList = list(data['date'])
    latList = list(data['lat'])
    lonList = list(data['lon'])
    tempList = list(data['temperature'])
    humList = list(data['humidity'])
    pressList = list(data['pressure'])
    biomeList = list(data['biome'])
    featureList = list(data['feature'])

    return siteIDList, dateList, latList, lonList, tempList, humList, pressList, biomeList, featureList


# get correspondence table from enum.tsv and put it in a list
def get_enum():

    # read the TSV file
    data = pd.read_excel(
        'Empty Quarter Project site and samples.xlsx', sheet_name='enum')

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
    WGS = Namespace("http://www.w3.org/2003/01/geo/wgs84_pos#")
    GEO = Namespace("http://www.opengis.net/#geosparql")
    OBI = Namespace("http://purl.obolibrary.org/obo/OBI_")
    ENVO = Namespace("http://purl.obolibrary.org/obo/ENVO_")
    PATO = Namespace("http://purl.obolibrary.org/obo/PATO_")
    SIO = Namespace("http://semanticscience.org/resource/")
    QUDT = Namespace("http://qudt.org/vocab/unit/")
    EGP = Namespace("http://w3id.org/eqp/vocab/")
    DCT = Namespace("http://purl.org/dc/terms/")
    d = Namespace("http://w3id.org/eqp/EGP-D1/")
    PREFIX = Namespace("http://w3id.org/eqp/")
    SCHEMA = Namespace("http://schema.org/")

    # Get data from table.tsv
    siteIDList, dateList, latList, lonList, tempList, humList, pressList, biomeList, featureList = get_data()

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
    graph.bind("obo", OBI)
    graph.bind("geo", GEO)
    graph.bind("wgs", WGS)
    graph.bind("schema", SCHEMA)
    graph.bind("", PREFIX)
    graph.bind("d", d)
    graph.bind("dct", DCT)
    graph.bind("egp", EGP)

    # Define the entities
    DR = PREFIX["DR"]
    S = PREFIX["S"]
    SR1 = PREFIX["1SR1"]
    S1_GEO = PREFIX["1S_geometry"]
    EQP = PREFIX["eqp"]
    BORG = PREFIX["borg"]
    KAUST = PREFIX["kaust"]
    ABBR = PREFIX["abbr"]

    # Define the Dataset
    d = URIRef(d)
    graph.add((d, RDF.type, SCHEMA["Dataset"]))
    graph.add((d, RDF.type, SIO.Dataset))
    graph.add((d, RDFS.label, Literal(
        "Empty Quarter Metagenomics Dataset", lang="en")))
    graph.add((d, RDFS.comment, Literal("", lang="en")))
    graph.add((d, SCHEMA["identifier"], Literal(
        "EGP-D1")))
    graph.add((d, SCHEMA["dateCreated"], Literal(
        "2023-04-04T13:00:00Z", datatype=SCHEMA["Date"])))
    graph.add((d, DCT.publisher, PREFIX["borg"]))
    graph.add((d, DCT.contributor, URIRef(
        "http://orcid.org/0000-0003-4727-9435")))
    graph.add((d, DCT.conformsTo, URIRef(
        "https://www.w3.org/TR/hcls-dataset/")))
    graph.add((d, DCT.license, URIRef(
        "https://creativecommons.org/licenses/by/4.0/")))
    graph.add((d, DCT.language, URIRef("http://lexvo.org/id/iso639-3/en")))
    graph.add((d, DCT['format'], Literal("text/turtle")))

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
        date = dateList[i]

        _pressure = uuid.uuid4()
        _temperature = uuid.uuid4()
        _humidity = uuid.uuid4()
        _pressure_value = uuid.uuid4()
        _temperature_value = uuid.uuid4()
        _humidity_value = uuid.uuid4()

        data_record_id = str(uuid.uuid4())
        location_id = str(uuid.uuid4())
        main_entity_id = str(uuid.uuid4())
        geo_id = str(uuid.uuid4())

        DR = d + data_record_id
        S = d + location_id
        SR1 = d + main_entity_id
        S1_GEOMETRY = PREFIX[geo_id]

        # Create the data record
        graph.add((DR, RDF.type, SCHEMA["DataRecord"]))
        graph.add((DR, RDF.type, SIO["DataRecord"]))
        graph.add((DR, RDFS.label, Literal(
            "Record for Site {} of Empty Quarter Metagenomics Dataset".format(int(siteID)))))
        graph.add((DR, SCHEMA["dateCreated"], Literal(
            "2023-04-04T13:00:00Z", datatype=SCHEMA["Date"])))
        graph.add((DR, SCHEMA["identifier"], Literal(
            "EGP-D1-R{}".format(int(siteID)))))
        graph.add((DR, SCHEMA["mainEntity"], SR1))

        # Site
        graph.add((S, RDF.type, GEO["Feature"]))
        graph.add((S, RDFS.label, Literal(
            "Site {} in Empty Quarter Project".format(int(siteID)))))
        graph.add((S, SCHEMA["identifier"], Literal(
            "EGP-S{}".format(int(siteID)))))
        graph.add((S, RDF.type, SCHEMA["Location"]))
        graph.add((S, RDF.type, SIO["Site"]))
        graph.add((S, WGS.long, Literal(lon)))
        graph.add((S, WGS.lat, Literal(lat)))
        graph.add((S, EGP["atmospheric_pressure"], Literal(
            press, datatype=QUDT["MilliBAR"])))
        graph.add((S, EGP["temperature"], Literal(
            temp, datatype=QUDT["DEG_C"])))
        graph.add((S, EGP["humidity"], Literal(hum, datatype=QUDT["PERCENT"])))
        graph.add((S, SIO["isLocatedIn"], ENVO[str(biome)]))
        graph.add((S, SIO["isAdjacentTo"], ENVO[str(biome)]))
        graph.add((S, GEO["hasGeometry"], S1_GEOMETRY))

        # pressure
        pressure = URIRef(str(_pressure))
        graph.add((S, SIO.hasAttribute, pressure))
        graph.add((pressure, RDFS.label, Literal(
            "Atmospheric pressure measurement for Site {}".format(int(siteID)))))
        graph.add((pressure, RDF.type, SIO.Measurement))
        graph.add((pressure, SIO.hasValue, Literal(press)))
        graph.add((pressure, SIO.hasUnit, QUDT.MilliBAR))
        pressure_value = URIRef(str(_pressure_value))
        graph.add((pressure, SIO.isMeasurementValueOf, pressure_value))
        graph.add((pressure, SIO.measuredAt, Literal(
            date, datatype=XSD.dateTime)))
        graph.add((pressure_value, RDF.type, PATO["0001025"]))

        # temperature
        temperature = URIRef(str(_temperature))
        graph.add((S, SIO.hasAttribute, temperature))
        graph.add((temperature, RDFS.label, Literal(
            "Temperature measurement for Site {}".format(int(siteID)))))
        graph.add((temperature, RDF.type, SIO.Temperature))
        graph.add((temperature, SIO.hasValue, Literal(temp)))
        graph.add((temperature, SIO.hasUnit, QUDT.DEG_C))
        temperature_value = URIRef(str(_temperature_value))
        graph.add((temperature, SIO.isMeasurementValueOf, temperature_value))
        graph.add((temperature, SIO.measuredAt,
                  Literal(date, datatype=XSD.dateTime)))
        graph.add((temperature_value, RDF.type, PATO["0000146"]))

        # humidity
        humidity = URIRef(str(_humidity))
        graph.add((S, SIO.hasAttribute, humidity))
        graph.add((humidity, RDFS.label, Literal(
            "Humidity measurement for Site {}".format(int(siteID)))))
        graph.add((humidity, RDF.type, SIO.Humidity))
        graph.add((humidity, SIO.hasValue, Literal(hum)))
        graph.add((humidity, SIO.hasUnit, QUDT.PERCENT))
        humidity_value = URIRef(str(_humidity_value))
        graph.add((humidity, SIO.isMeasurementValueOf, humidity_value))
        graph.add((humidity, SIO.measuredAt, Literal(
            date, datatype=XSD.dateTime)))
        graph.add((humidity_value, RDF.type, PATO["0015009"]))

        # Create the geometry
        graph.add((S1_GEOMETRY, RDF.type, GEO["Geometry"]))
        graph.add((S1_GEOMETRY, GEO["asWKT"], Literal(
            f"Point(${lat} ${lon})", datatype=GEO["wktLiteral"])))

        # Sample
        graph.add((SR1, RDF.type, SCHEMA["Sample"]))
        graph.add((SR1, RDF.type, GEO["Feature"]))
        graph.add((SR1, RDF.type, SIO["Sample"]))
        graph.add((SR1, RDFS.label, Literal(
            "Sample {} from surface of Site {}".format(1, int(siteID)))))
        graph.add((SR1, SCHEMA["identifier"],
                   Literal("{}Sr1".format(int(siteID)))))
        graph.add((SR1, SIO["isDerivedFrom"], ENVO["00005800"]))  # sand
        graph.add((SR1, EGP["depth"], Literal("surface")))
        graph.add((SR1, EGP["replicate"], Literal("1")))
        graph.add((SR1, EGP["collected-at"], S))

        graph.add((BORG, RDF.type, SIO["Group"]))
        graph.add((BORG, RDFS.label, Literal("Bio-Ontology Research Group")))

        graph.add((KAUST, RDF.type, SIO["University"]))
        graph.add((KAUST, RDFS.label, Literal(
            "King Abdullah University of Science and Technology", lang="en")))
        graph.add((KAUST, ABBR, Literal("KAUST")))

        # Define the relationships
        graph.add((DR, SCHEMA["isPartOf"], d))
        graph.add((BORG, SIO["partOF"], KAUST))

    # dot file and png
    # with open('graph.dot', 'w') as f:
        # rdf2dot(graph,f)
    # write in turtle format to output file
    graph.serialize(destination='output1.ttl', format='turtle')


if __name__ == '__main__':
    main()
