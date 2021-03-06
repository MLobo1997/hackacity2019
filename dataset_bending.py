import pprint
import requests
import json
import os
import gmplot
from statistics import mean
import pandas as pd

# from dataset_bending import get_all_datasets, get_dataset_info, get_dataset_data, get_dataset_data_full, try_to_display_dataset, display_dataset_polygon, display_dataset_points, get_dataframe_alojamentos


def create_polygons(coordinates, gmap=None, display=False):
    lon, lat = tuple(map(list,zip(*coordinates)))
    gmap = gmplot.GoogleMapPlotter(min(lat), mean(lon), 16) if not gmap else gmap
    gmap.apikey = "AIzaSyA2B83Ome4_S-EXUe5zLTrkaGeZv-Ndft4"
    gmap.polygon(lat, lon, color = 'cornflowerblue') 
    if display: os.system("temp.html")
    return gmap

def display_plot(gmap, filename="temp.html"):
    gmap.draw(filename)
    os.system(filename)

def display_dataset_polygon(dataset):
    gmap = None
    for datapoint in dataset:
        gmap = create_polygons(datapoint["coordinates"][0], gmap)
    display_plot(gmap)

def create_points(coordinates, gmap=None, display=False):
    lon, lat = tuple(coordinates)
    gmap = gmplot.GoogleMapPlotter(lat, lon, 16) if not gmap else gmap
    gmap.apikey = "AIzaSyA2B83Ome4_S-EXUe5zLTrkaGeZv-Ndft4"
    gmap.scatter([lat], [lon], '#FF0000', size = 25, marker = False) 
    if display: os.system("temp.html")
    return gmap

def display_dataset_points(dataset):
    gmap = None
    for datapoint in dataset:
        gmap = create_points(datapoint["coordinates"], gmap)
    display_plot(gmap)

def try_to_display_dataset(dataset_name):
    url = next(get_dataset_info(dataset_name))
    # print(url)
    dataset = get_dataset_data_full(url)
    # coordinates are len 2, polygons are not
    if len(dataset[0]["coordinates"]) == 2: display_dataset_points(dataset)
    else: display_dataset_polygon(dataset)

# List all datasets
def get_all_datasets():
    url = "https://opendata.urbanplatform.portodigital.pt/api/3/action/package_list"
    r = requests.get(url)
    return r.json()["result"]

# ### Get Information for custom dataset, by name
# If `url_only` is true, returns location of data, else a tuple of `(dataset-resource, FORMAT, URL)`


def get_dataset_info(dataset, url_only=True):
    # returns a generator for (dataset-resource, FORMAT, URL) or just the URL
    url = "https://opendata.urbanplatform.portodigital.pt/api/3/action/package_show?id=%s" % dataset
    j = requests.get(url).json()
    if not j["success"]:
        print(j["error"])
        return
    for resource in j['result']['resources']:
        if url_only:
            yield resource["url"]
        else:
            yield (resource["name"], resource["format"], resource["url"])

# Get data from url
#  * Set the query params
#  * Specify how to parse result
#  * function to handle request result and return generator of datapoints


DEFAULT_REQ_PARAMS = {'where': "1=1", 'returnGeometry': 'true', 'orderByFields': 'objectid ASC', 'outSR': '4326'}


def remove_useless_from_dict(dic):
    return {k: v if (v and v != " ") else None for k, v in dic.items()}


def parse_features_geojson(x):
    features = x["properties"]
    features["coordinates"] = x["geometry"]["coordinates"]
    return remove_useless_from_dict(features)


def parse_features_json(x): return remove_useless_from_dict(x["attributes"])

def get_dataset_data(dataset_url, req_params={"f":"json"}, f="geojson", fields="*", offset=0):
    if "fiware" in dataset_url:
#         pprint(requests.get(dataset_url).json()[0])
        def get_att(x): 
            x.update({"lon": x["location"]["value"]["coordinates"][0], "lat":x["location"]["value"]["coordinates"][1]})
            return x
        return map(get_att, requests.get(dataset_url).json())
    else:
        # default format could be json, but this gives x, y and not lat, lon
        params = DEFAULT_REQ_PARAMS; params.update(req_params); params["f"] = f; params["outFields"]=fields; params["resultOffset"]=offset
        data = requests.get(dataset_url + "/query", params=params).json()
        get_attributes = parse_features_geojson if f=="geojson" else parse_features_json
        return map(parse_features_geojson, data["features"])

def get_dataset_data_full(dataset_url):
    dataset = []
    request_dataset = []
    while len(request_dataset) == 1000 or dataset==[]:
        request_dataset = list(get_dataset_data(dataset_url, offset=len(dataset)))
        dataset+=request_dataset
        if not len(request_dataset): break
    return dataset


def get_dataframe_alojamentos():
    url = next(get_dataset_info("alojamento-local"))
    alojamentos = get_dataset_data_full(url)
    df = pd.DataFrame(columns=["id", "data_levan", "nome", "ano_registo", "type", "address", "freg", "n_reg", "lat", "lon"])
    print(alojamentos[0])
    for i, a in enumerate(alojamentos):
         df.loc[i] = [a["objectid"], a["data_levan"], a["nome_aloj"],
                      a["ano_reg"], a["modalidade"],
                      "%s, %s Porto, Portugal" % (a["morada"], a["cod_postal"]),
                      a["cod_freg"], a["n_reg"],
                      a["coordinates"][1], a["coordinates"][0]]
    return df