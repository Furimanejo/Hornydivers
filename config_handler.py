from copy import deepcopy
import json
import os

aspect_ratios = {
    0 : {
        "id" : "16:9",
        "sample_w": 1920,
        "sample_h": 1080,
    },
    #1: {
    #    "id" : "21:9",
    #    "sample_w": 2560,
    #    "sample_h": 1080,
    #},
    #2: {
    #    "id" : "16:10",
    #    "sample_w": 1680,
    #    "sample_h": 1050,
    #    "template_scaling": 1680/1920
    #},
}

config = {
    "monitor_number": 1,
    "aspect_ratio_index": 0,
    "show_overlay_mode": 0,
    "show_regions_mode": 0,
    "decay": 100,
    "points_per_missing_health": 50,
    "points_per_increasing_health": 50,
    "points_per_decreasing_health": 50,
    "regions": {
        "Health Bar": {
            "1920x1080": {
                "x": 108,
                "y": 996,
                "w": 190,
                "h": 8
            },
        },
        "Stim":{
            "1920x1080": {
                "x": 305,
                "y": 990,
                "w": 60,
                "h": 20
            },
        },
    },
    "detectables":{
        "Stim White": {"filename": "stim_white.png", "threshold": .8},
        "Stim Red": {"filename": "stim_red.png", "threshold": .5},
    },
}

def save_to_file():
    save_dict = deepcopy(config)

    del save_dict["regions"]
    del save_dict["detectables"]

    with open('config.json', 'w') as f:
        json.dump(save_dict,  f, indent= 4)

def load_from_file():
    if os.path.exists('config.json'):
        print("Loading config file...")
        with open('config.json', 'r') as f:
            load_dict = json.load(f)
            for key in load_dict.keys():
                config[key] = load_dict[key]