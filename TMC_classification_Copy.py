from itertools import islice
import numpy as np
import pandas as pd
import pickle
import math
from Intersect import INTERSECT


def TMC_class(raw_data, pro_data, processed_zone_detections, num_values, zone_def, zone_coords, interval=0,
              start_time=1600):
    Count = [0] * 16
    missed_Count = [0] * 16
    movement = [0] * 4
    count_rng = len(Count) - 3
    output = processed_zone_detections
    for TMC_count in output:  # loop through each group of detections
        j = 0
        i = 0
        break_out = False
        for zone in range(count_rng):  # loop through all 16 possible movement
            if (TMC_count[0][3] == zone_def[i]) or (TMC_count[0][3] == zone_def[i + 1]):
                if (TMC_count[0][1] != TMC_count[-1][1]) and (TMC_count[0][2] != TMC_count[-1][2]):  # Check if there is only 1 zone detection
                    for move in movement:  # loop through each 4 sub movements
                        if TMC_count[-1][3] == zone_def[i + 2] or TMC_count[-1][3] == zone_def[i + 3]:
                            Count[j] += 1
                            if j == 3:
                                print("id to find = " + str(TMC_count))
                            # if found break out of both for loops
                            break_out = True
                            break
                        else:
                            # TODO : ***if for some reason the second detection was not defined this will
                            #    throw an error since i keeps incrementing*** Turn the second else into a function
                            #   called def misssed() - handle this error and the next with this function
                            break_out = True
                        i += 4
                        j += 1
                else:
                    missed_Count = missed_Ray_method(pro_data, zone_def, TMC_count[0][0], Count)
                    break_out = True

            if break_out:
                break
            i += 4
            j += 1

    Missed = num_values - sum(Count)
    i = 0
    Count_str = []
    for s in Count:
        Count_str.append(str(s))
        i += 1

    with open("Output.txt", "r") as Output:
        markdown_list = Output.readlines()
    #print(lines)

    #markdown_list = [["TIME", "NBR", "NBT", "NBL", "NBU", "SBR", "SBT", "SBL", "SBU", "EBR", "EBT", "EBL", "EBU", "WBR",
    #                  "WBT", "WBL", "WBU"], Count_str]
    mkdown = make_markdown_table(markdown_list, interval, start_time, Count_str)
    file1 = open("Output.txt", "w")
    file1.write(mkdown)
    file1.close()
    return Count, Missed, missed_Count


def missed_Ray_method(raw_data, zone_def, id_2_find, Count):
    count_rng = len(Count) - 3
    ZoneList = []
    for TMC_count in raw_data:  # For each unique id
        if int(id_2_find) == TMC_count[0][0]:
            zoneFound = False
            z1 = None
            z1_x = None
            z2 = None
            count = 0
            while count < len(TMC_count):  # loop through each detection in unique id
                if TMC_count[count][3] != 0 and not zoneFound:
                    z1 = TMC_count[count][3]  # save the first non-zero zone detection as z1
                    z1_x = TMC_count[count][3]
                    count += 1
                    zoneFound = True
                elif TMC_count[count][3] != 0 and zoneFound:
                    if z1_x == TMC_count[count][3]:  # CHECK AGAINST Z1_X IN ORDER TO GET THE LAST CHANGE IN THE LIST
                        count += 1
                    else:
                        z1_x = TMC_count[count][3]
                        z2 = TMC_count[count][3]
                        count += 1
                else:
                    count += 1
            if z1 != None and z2 == None:  # Check if possible U turn
                pass
            ZoneList.append([TMC_count[0][0], z1, z2])
            Count = classify(Count, count_rng, z1, z2, zone_def, TMC_count)
        else:
            pass
    return Count


def NN(pro_data, midpoint_line):
    distance_list = []
    for data in pro_data:
        distance = math.sqrt((data[1] - midpoint_line[0]) ** 2 + (data[2] - midpoint_line[1]) ** 2)
        distance_list.append(distance)
    idx = distance_list.index(min(distance_list))
    midpoint_data = [pro_data[idx][1], pro_data[idx][2]]

    return midpoint_data


def classify(Count, count_rng, EnterZone, ExitZone, zone_def, TMC_count):
    # classify the movement
    k = 0
    l = 0
    movement = [0] * 4
    sub_break_out = False
    for rng in range(count_rng):  # loop through all 16 possible movement
        if (EnterZone == zone_def[l]) or (EnterZone == zone_def[l + 1]):
            for move in movement:  # loop through each 4 sub movements
                if (ExitZone == zone_def[l + 2]) or (ExitZone == zone_def[l + 3]):
                    Count[k] += 1
                    if k == 3:
                        print("id to find =" + str(TMC_count))
                    # if found break out of both for loops
                    sub_break_out = True
                    break
                else:
                    # TODO : ***if for some reason the second detection was not defined this will
                    #    throw an error since l keeps incrementing*** Turn the second else into a function
                    #   called def misssed() - handle this error and the next with this function
                    sub_break_out = True
                l += 4
                k += 1
        if sub_break_out:
            break
        l += 4
        k += 1
    return Count


def organize_list(data):
    z = []

    # list of IDs
    for zone in data:
        z.append(zone[0])

    num_values = len(np.unique(np.array(z)))

    splits = []
    split = []
    i = 0
    for zone in data:
        val = z[i]
        i += 1
        if val not in split:
            count = z.count(val)
            splits.append(count)
            split.append(z[i - 1])

    # split the zone list
    input = iter(data)
    output = [list(islice(input, elem)) for elem in splits]  # islice(iterable, start, stop, step)
    return output, num_values


def remove_static_detections(processed_output):
    p2 = []
    j = 0
    for id in processed_output:  # For each unique id
        i = 0
        for point in range(len(id)):
            while i < len(id):
                if i == 0:
                    p2 = [id[i][1], id[i][2]]
                    i += 1
                else:
                    p1 = [id[i][1], id[i][2]]
                    distance = math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)
                    if distance < 5:
                        removed_element = processed_output[j].pop(i)
                        i -= 1
                        if len(processed_output[j]) == 0:  # if the list is empty
                            processed_output[j].pop()
                    else:
                        if i < len(id) - 1:
                            i += 1
                            p2 = [id[i][1], id[i][2]]
                        else:
                            break
        j += 1
    return processed_output


def remove_bad_detections(processed_static):
    j = 0
    new_processed_static = []
    for id in processed_static:  # For each unique id
        i = 0
        for point in range(len(id)):
            while i < len(id) - 1:
                if i == 0:
                    p2 = id[i][3]
                    i += 1
                else:
                    if p2 != id[i][3]:
                        i += 1
                        if processed_static[j][i:]:
                            new_processed_static.append(processed_static[j][i:])
                            processed_static[j] = processed_static[j][:i]
                            break
                    else:
                        i += 1
                        p2 = id[i][3]
        j += 1
    for i in range(len(new_processed_static)):
        processed_static.append(new_processed_static[i])
    return processed_static


def preprocessing(data, data_zone_detections, zone_coords):
    # TODO: 1. Remove the points that are duplicates. Vehicle detections that are not moving.
    #          Process the zone detection and eliminate data that indicates zero movement. The issue
    #          is that if a vehicle is sitting on a detection zone and the exit does not get picked up
    #          the algorithm will think its a U-turn.
    #   2. Remove the raw data points that are outside of the 'Zone Box'.  'Ray Casting method.'
    #     Draw a line up/down/left/right until an intersection/s have been made.  If 1 intersection
    #     then the point is inside the Box, if 2 intersections made then the point is outside the
    #     box and can be deleted.
    #   3. Check if the length zone detection list is greater than 2. If the last value is the same as the first
    #     and the zone detections change say 3 - 1 - 3 : remove the last 3
    #   4. Remove Anomolies - do this before step 3. Remove the data points that are 'outliers'

    # TODO: need to get height and width of video automatically
    w = 1280
    h = 720

    processed_output, num_values = organize_list(data_zone_detections)

    #  1. IF THE VEHICLES ARE NOT MOVING OVER A DETECTION ZONE
    processed_static = remove_static_detections(processed_output)
    processed_static_raw_data = remove_static_detections(data)

    #  3. 3 - 1 - 3 : remove last 3
    processed_zone_detections = remove_bad_detections(processed_static)

    return processed_static_raw_data, processed_zone_detections, num_values


def make_markdown_table(array, interval, start_time, Count_str):
    # TODO: fix this
    """ the same input as above """

    nl = "\n"

    markdown = nl
    #markdown += f"| {' | '.join(array[0])} |"

    #markdown += nl
    #markdown += f"| {' | '.join(['---']*len(array[0]))} |"

    #markdown += nl
    markdown += f"| {start_time + interval * 15} "
    markdown += nl
    #for t in range(interval):
    for entry in Count_str:
        #markdown += f"| {' | '.join(entry)} |{nl}"
        markdown += f"| {' | '.join(entry)} "

    return markdown


if __name__ == '__main__':
    # Load pickle file containing the zone definitions
    zone_def = open("./TMC Testing/test22-nysdotv1.1_newAlgo/zone_pkl_dump.pkl", "rb")
    zone_def = pickle.load(zone_def)


    zone_coords = open("./TMC Testing/test22-nysdotv1.1_newAlgo/zone_coords_pkl_dump.pkl", "rb")
    zone_coords = pickle.load(zone_coords)

    # ZONE INTERSECTION DETECTIONS
    data = open("./TMC Testing/test22-nysdotv1.1_newAlgo/data_zones_test.pkl", "rb")
    data = pickle.load(data)
    data.sort(key=lambda p: p[0])
    df = pd.DataFrame(data)
    df.to_csv(r'data.csv')

    #   RAW DATA = ALL DETECTIONS WITH ZONE INTERSECTIONS
    raw_data = open("./TMC Testing/test22-nysdotv1.1_newAlgo/data_test.pkl", "rb")
    raw_data = pickle.load(raw_data)
    raw_data.sort(key=lambda p: p[0])
    #raw_data = raw_data[1:]  # first element is blank - remove it
    df = pd.DataFrame(raw_data)
    df.to_csv(r'raw_data.csv')

    pro_raw_data = raw_data.copy()
    processed_raw_data, processed_zone_detections, num_values = preprocessing(pro_raw_data, data, zone_coords)

    # RELOAD THE RAW DATA AND THE ZONE DETECTIONS
    raw_data = open("./TMC Testing/test22-nysdotv1.1_newAlgo/data_test.pkl", "rb")
    raw_data = pickle.load(raw_data)
    raw_data.sort(key=lambda p: p[0])
    #raw_data = raw_data[1:]  # first element is blank - remove it
    #processed_static_raw = remove_static_detections(raw_data)  # REMOVE THE STATIC VEHICLES FROM THE RAW DATA

    data = open("./TMC Testing/test22-nysdotv1.1_newAlgo/data_zones_test.pkl", "rb")
    data = pickle.load(data)
    data.sort(key=lambda p: p[0])
    data = organize_list(data)

    # No pre processing
    #r, missed, missed_Count = TMC_class(raw_data, raw_data, processed_zone_detections, num_values, zone_def,
    #                                    zone_coords, interval=2)

    r, missed, missed_Count = TMC_class(raw_data, processed_raw_data, processed_zone_detections, num_values, zone_def,
                                       zone_coords, interval=2)
    print(r, missed, missed_Count)
