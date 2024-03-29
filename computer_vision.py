import os
import time
import mss
import numpy as np
import cv2 as cv

from config_handler import config, aspect_ratios

class ComputerVision():
    def __init__(self) -> None:
        self.last_update = 0
        self.min_update_period = 0.1
        self.detection_ping = 0
        self.score_over_time = 0
        self.score_instant = 0
        self.current_health = -1

        self.filters = {

        }

        self.debug_image = None
        self.detection_rect = {}
        self.resolution_scaling_factor = 1
        self.resolution_changed = False
        self.detect_resolution()
    
    def detect_resolution(self):
        monitor_number = config["monitor_number"]
        
        monitor_rect = {}
        with mss.mss() as sct:
            monitor_rect = sct.monitors[monitor_number]
        
        sample_width = aspect_ratios[config["aspect_ratio_index"]]["sample_w"]
        sample_height = aspect_ratios[config["aspect_ratio_index"]]["sample_h"]
        
        game_rect = monitor_rect
        scale = 1
        monitor_aspect_ratio = monitor_rect["width"] / monitor_rect["height"]
        if monitor_aspect_ratio >= sample_width / sample_height:
            # scale to fit height, like fitting a 16:9 window on a 21:9 screen
            scale = monitor_rect["height"] / sample_height
            desired_width = int(sample_width * scale)
            black_bar_width = int((monitor_rect["width"] - desired_width) / 2)
            game_rect["width"] = desired_width
            game_rect["left"] += black_bar_width
        else:
            # scale to fit width, like fitting a 16:9 window on a 16:10 screen
            scale = monitor_rect["width"] / sample_width
            desired_height = int(sample_height * scale)
            black_bar_height = int((monitor_rect["height"] - desired_height) / 2)
            game_rect["height"] = desired_height
            game_rect["top"] += black_bar_height

        if self.detection_rect == game_rect:
            return False
        else:
            print("Setting detection rect: " + str(game_rect))
            self.detection_rect = game_rect
            self.resolution_scaling_factor = scale
            self.detectables_setup()
            return True

    def detectables_setup(self):
        for region in config["regions"]:
            i = config["aspect_ratio_index"]
            resolution = str(aspect_ratios[i]["sample_w"]) + "x" + str(aspect_ratios[i]["sample_h"])
            rect = config["regions"][region].get(resolution)
            if rect == None:
                print("Region \"" + region + "\" not defined for current aspect ratio")
                rect = config["regions"][region].get("1920x1080")

            config["regions"][region]["ScaledRect"] = self.scale_rect(rect)
            config["regions"][region]["Matches"] = []

        for item in config["detectables"]:
            self.load_and_scale_template(config["detectables"][item])
            if item in self.filters:
                config["detectables"][item]["template"] = self.filters[item](config["detectables"][item]["template"])
    
    def get_current_score(self):
        return self.score_over_time + self.score_instant
    
    def set_score(self, value):
        self.score_over_time = value;
        
    def update(self):
        t0 = time.time()
        if t0 - self.last_update < self.min_update_period:
            return False
        delta_time = min(1, t0 - self.last_update)
        self.last_update = t0

        self.resolution_changed = self.detect_resolution()

        previous_health = self.current_health
        self.update_detections()

        self.score_instant = 0

        if self.current_health != -1:
            self.score_instant += (100 - self.current_health) * config["points_per_missing_health"] / 100
            if previous_health != -1:
                health_delta = self.current_health - previous_health
                if health_delta < 0:
                    self.score_over_time -= health_delta * config["points_per_decreasing_health"] / 100
                else:
                    self.score_over_time += health_delta * config["points_per_increasing_health"] / 100

        self.score_over_time -= delta_time * config["decay"] / 60
        self.score_over_time = max(0, self.score_over_time)
        self.score_over_time = min(100, self.score_over_time)

        t1 = time.time()
        a = .1
        self.detection_ping = (1-a) * self.detection_ping + a * (t1-t0)
        return True

    def update_detections(self):
        for r in config["regions"]:
            config["regions"][r]["Matches"] = []
        for d in config["detectables"]:
            config["detectables"][d]["Count"] = 0

        self.grab_frame_cropped_to_regions(["Health Bar", "Stim"])
        self.match_detectables_on_region("Stim", ["Stim White", "Stim Red"])

        if config["regions"]["Stim"]["Matches"]:
            self.current_health = self.calculate_healthbar_percentage()
        else:
            self.current_health = -1

    def grab_frame_cropped_to_regions(self, regionNames):
        top = self.detection_rect["height"]
        left = self.detection_rect["width"]
        bottom = 0
        right = 0

        # Find rect that encompasses all regions
        for region in regionNames:
            rect = config["regions"][region]["ScaledRect"]
            top = min(top, rect["y"])
            bottom = max(bottom, rect["y"]+rect["h"])
            left = min(left, rect["x"])
            right = max(right, rect["x"]+rect["w"])

        self.frame_offset = (top, left)

        top += self.detection_rect["top"]
        bottom += self.detection_rect["top"]
        left += self.detection_rect["left"]
        right += self.detection_rect["left"]

        with mss.mss() as sct:
            self.frame = np.array(sct.grab((left, top, right, bottom)))[:,:,:3]
    
    def calculate_healthbar_percentage(self):
        rect = config["regions"]["Health Bar"]["ScaledRect"]
        frame = self.get_cropped_frame_copy(rect)
        
        # white color range in BGR
        lower = np.array([210, 210, 210])
        upper = np.array([255, 255, 255])
        mask = cv.inRange(frame, lower, upper)
        count = np.count_nonzero(mask)

        if count <= 0:
            # red color range in BGR
            lower = np.array([50, 50, 200])
            upper = np.array([120, 120, 255])
            mask = cv.inRange(frame, lower, upper)
            count = np.count_nonzero(mask)

        percentage = int(100*count/mask.size)
        if percentage >= 98:
            percentage = 100
        config["regions"]["Health Bar"]["Matches"].append("Health: " + str(percentage))
        return percentage
    
    def match_detectables_on_region(self, regionKey, detectableKeys):
        if len(detectableKeys) == 0:
            return

        region_rect = config["regions"][regionKey]["ScaledRect"]
        crop = self.get_cropped_frame_copy(region_rect)

        filtered_crops = {}
        for d in detectableKeys:
            filt = self.filters.get(d)
            if filt is not None and filt not in filtered_crops:
                filtered_crops[filt] = filt(crop.copy())

        for d in detectableKeys:
            if d in self.filters:
                selected_crop = filtered_crops[self.filters[d]]
            else:
                selected_crop = crop

            max_matches = config["regions"][regionKey].get("MaxMatches", 1)
            if len(config["regions"][regionKey]["Matches"]) >= max_matches:
                break

            r_shape = selected_crop.shape
            t_shape = config["detectables"][d]["template"].shape
            if t_shape[0] > r_shape[0] or t_shape[1] > r_shape[1]:
                print("Template {0}({1}) is bigger than region {2}".format(d, t_shape, r_shape))
                return

            match_max_value = self.match_template(selected_crop, config["detectables"][d]["template"])
            
            if match_max_value > config["detectables"][d]["threshold"]:
                config["detectables"][d]["Count"] += 1
                config["regions"][regionKey]["Matches"].append(d)
            
    def match_template(self, frame, template):
        result = cv.matchTemplate(frame, template, cv.TM_CCOEFF_NORMED)
        minVal, maxVal, minLoc, maxLoc = cv.minMaxLoc(result)
        return maxVal

    def get_cropped_frame_copy(self, rect):
        top = rect["y"] - self.frame_offset[0]
        bottom = rect["y"] + rect["h"] - self.frame_offset[0]
        left = rect["x"] - self.frame_offset[1]
        right = rect["x"] + rect["w"] - self.frame_offset[1]
        return self.frame[top:bottom, left:right].copy()

    def scale_rect(self, rect):
        scaled_rect = {
            "x": int (rect["x"] * self.resolution_scaling_factor),
            "y": int (rect["y"] * self.resolution_scaling_factor),
            "w": int (rect["w"] * self.resolution_scaling_factor),
            "h": int (rect["h"] * self.resolution_scaling_factor)
        }
        return scaled_rect
    
    def load_and_scale_template(self, item):
        path = os.path.join(os.path.abspath("."), "templates", item["filename"])
        base_template = cv.imread(path)

        template_scaling = aspect_ratios[config["aspect_ratio_index"]].get("template_scaling", 1)
        height = int(base_template.shape[0] * self.resolution_scaling_factor * template_scaling)
        width =  int(base_template.shape[1] * self.resolution_scaling_factor * template_scaling)
        scaled = cv.resize(base_template.copy(), (width, height))

        item["original_image"] = base_template
        item["template"] = scaled
