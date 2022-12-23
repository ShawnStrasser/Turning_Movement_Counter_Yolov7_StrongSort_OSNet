from Intersect import INTERSECT
import pickle
from TMC_classification_Copy import TMC_class, preprocessing, organize_list
import cv2
import math
import numpy as np


class TmcCounter:
    def __init__(self, Zones, zone_def):
        self.data = [[[]]]
        self.data_store_in = []
        self.data_store_f = []
        self.data_zones = []
        self.index = 0
        self.breakout = False
        self.Zones = Zones
        self.count = [0] * len(Zones)
        self.zone_def = zone_def
        self.data_zones_ray_intersect = []

    def count_TMC(self, box, id, cls, im0, zone_colors):
        center_coordinates = (int(box[0]+(box[2]-box[0])/2), int(box[1]+(box[3]-box[1])/2))

        # SAVE ALL CENTER POINTS IN A LIST - 'DATA'
        first_intersection = 0
        second_intersection = 0
        i = 0
        for sub_list in self.data:
            i += 1
            for sub_list2 in sub_list:
                if id in sub_list2 and not self.breakout and sub_list2.index(id) == 0:
                    self.index = i  # subtract 2 since the first list of 'data' is empty
                    self.data_store_f[self.index - 2] = ([id, center_coordinates[0], center_coordinates[1]])

                    # ***************************************************************************************
                    slope_y = self.data_store_f[self.index - 2][2] - self.data_store_in[self.index - 2][2]
                    slope_x = self.data_store_f[self.index - 2][1] - self.data_store_in[self.index - 2][1]
                    EndPointX = 1500 * slope_x + self.data_store_in[self.index - 2][1]
                    EndPointY = 1500 * slope_y + self.data_store_in[self.index - 2][2]

                    num_intersections, intersection_list = INTERSECT(self.data_store_in[self.index - 2][1],
                                                                     self.data_store_in[self.index - 2][2],
                                                                     EndPointX, EndPointY, self.Zones, Pre=True)
                    if num_intersections != 0 and len(intersection_list) != 0:
                        distance_list = []
                        for intersect in intersection_list:
                            distance = math.sqrt((intersect[0] - self.data_store_in[self.index - 2][1]) ** 2 +
                                                 (intersect[1] - self.data_store_in[self.index - 2][2]) ** 2)
                            distance_list.append(distance)
                        if num_intersections == 1:
                            first_intersection = intersection_list[0][2]
                            second_intersection = 0
                        if num_intersections == 2:
                            first_intersection = intersection_list[distance_list.index(min(distance_list))][2]
                            second_intersection = intersection_list[distance_list.index(max(distance_list))][2]

                    self.data_zones_ray_intersect.append([id, center_coordinates[0], center_coordinates[1],
                                                          first_intersection, second_intersection, cls])
                    # ****************************************************************************************

                    sub_list.append([id, center_coordinates[0], center_coordinates[1], first_intersection,
                                     second_intersection, cls])
                    self.breakout = True
                else:
                    break
        if not self.breakout:
            self.data.append([[id, center_coordinates[0], center_coordinates[1], first_intersection,
                               second_intersection, cls]])
            self.data_store_in.append([id, center_coordinates[0], center_coordinates[1]])
            self.data_store_f.append([id, center_coordinates[0], center_coordinates[1]])

        # DETECT THE ZONES
        if self.index != 0:
            B, Zone_det = INTERSECT(self.data_store_in[self.index - 2][1], self.data_store_in[self.index - 2][2],
                                    self.data_store_f[self.index - 2][1], self.data_store_f[self.index - 2][2],
                                    self.Zones)
            if B:
                self.count[Zone_det - 1] += 1
                self.data_zones.append([id, center_coordinates[0], center_coordinates[1], Zone_det, cls])
                print('Zone detected is : ' + str(Zone_det))
                im0 = drawLine(im0, start_point=(int(self.Zones[Zone_det-1][0][0]), int(self.Zones[Zone_det-1][0][1])),
                               end_point=(int(self.Zones[Zone_det-1][1][0]), int(self.Zones[Zone_det-1][1][1])),
                               zone_num=Zone_det, thick=8)

            # Update the initial point
            self.data_store_in[self.index - 2] = self.data_store_f[self.index - 2]
            self.breakout = False

        # PLOT THE ZONES CREATED FROM FLASK APP
        zone_num = 0
        for zone in self.Zones:
            zone_num += 1
            im0 = drawLine(im0, start_point=(int(zone[0][0]), int(zone[0][1])), end_point=(int(zone[1][0]),
                           int(zone[1][1])), zone_num=zone_num, clr=tuple(zone_colors[zone_num - 1]),
                           count=self.count[zone_num - 1])

        return im0

    def create_bin(self, interval):
        # Sort the dat before passing to TMC_classification
        self.data_zones.sort(key=lambda p: p[0])  # sort only by first element in list
        self.data.sort(key=lambda p: p[0])  # sort only by first element in list
        self.data = self.data[1:]  # first element is blank - remove it
        with open("data_zones_test.pkl", "wb") as file:
            pickle.dump(self.data_zones, file)
        with open("data_test.pkl", "wb") as file:
            pickle.dump(self.data, file)
        with open("data_zones_ray_intersect.pkl", "wb") as file:
            pickle.dump(self.data_zones_ray_intersect, file)

        # COUNT THE TURN MOVEMENTS
        pro_raw_data = self.data.copy()
        processed_raw_data, processed_zone_detections, num_values = preprocessing(pro_raw_data, self.data_zones,
                                                                                  self.Zones)
        #processed_zone_detections, num_values = organize_list(self.data_zones)
        #r, missed, missed_Count = TMC_class(self.data, processed_raw_data, processed_zone_detections, num_values,
        #                                    self.zone_def, self.Zones, interval)
        r, missed, missed_Count = TMC_class(self.data, processed_raw_data, processed_zone_detections, num_values,
                                            self.zone_def, self.Zones, interval)
        x = interval * 15
        with open("Zones_{}.pkl".format(x), "wb") as file:
            pickle.dump(self.data_zones, file)

        return r, missed, missed_Count


def drawLine(im0_, start_point, end_point, clr=(102, 255, 102), thick=3, zone_num=1, count=0):
    # TODO - add count to the zone
    cv2.line(im0_, start_point, end_point, color=clr, thickness=thick)
    line_center_x = abs(start_point[0] + end_point[0]) / 2
    line_center_y = abs(start_point[1] + end_point[1]) / 2
    line_center = (int(line_center_x), int(line_center_y))
    count_line_center = [x - 25 for x in line_center]

    #angle = math.degrees(math.atan((end_point[1] - start_point[1])/(end_point[0] - start_point[0])))
    #axesLength = (50, 20)
    #startAngle = 0
    #endAngle = 360
    #cv2.ellipse(im0_, line_center, axesLength, angle, startAngle, endAngle, clr, -1)

    cv2.circle(im0_, line_center, 20, clr, -1)
    cv2.circle(im0_, count_line_center, 20, clr, -1)
    cv2.circle(im0_, start_point, 7, clr, -1)
    cv2.circle(im0_, end_point, 7, clr, -1)

    font = cv2.FONT_HERSHEY_SIMPLEX
    fontScale = 1
    text = 'Zone: ' + str(zone_num)
    text_count = str(count)
    textsize, base = cv2.getTextSize(text, font, 1, 2)
    textsize = textsize[0]
    txt_center = (int(line_center_x - (textsize / 2)), int(line_center_y - (textsize / 2) + base * 2))
    txt_count_center = [x - 25 for x in txt_center]

    cv2.putText(im0_, text, txt_center, font, fontScale, (255, 255, 255), 1, cv2.LINE_AA)
    #cv2.putText(im0_, text_count, txt_count_center, font, fontScale, (255, 255, 255), 1, cv2.LINE_AA)

    return im0_
