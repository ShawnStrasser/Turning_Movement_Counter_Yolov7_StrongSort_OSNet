from itertools import islice
import numpy as np
import pandas as pd
import pickle
import math
from Intersect import INTERSECT
from collections import Counter


def TMC_class(raw_data, pro_data, processed_zone_detections, num_values, zone_def, zone_coords, interval=1,
              start_time=1600, ids_delete=[], ids_delete_2=[]):
    Count = [0] * 16
    missed_Count = [0] * 16
    movement = [0] * 4
    count_rng = len(Count) - 3
    output = processed_zone_detections
    lastFrame = int(pro_data[-1][-1][6] / interval)
    buildList = []
    buildZoneList = []

    #print(lastFrame)
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
                            #print(TMC_count[0], TMC_count[-1])
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
                    # TODO: when the last frame is reached - any ids that have not been classified will need to
                    #   saved to the next 15min bin.
                    if TMC_count[-1][-1] > lastFrame - 3:  # within the last 3 frames
                        break_out = True
                        break
                    else:
                        if TMC_count[0][0] in ids_delete_2:  # if the id is not in the potential ids to delete list
                            # TODO - grab the data from the other possible id to use in classifying
                            if TMC_count[0][0] not in buildList:  # Save each unique ID
                                for i in buildList:
                                    for ii in ids_delete:
                                        if i in ii and TMC_count[0][0] in ii:
                                            z1 = buildZoneList[buildList.index(i)][0][3]
                                            z2 = TMC_count[-1][3]
                                            Count = classify(Count, count_rng, z1, z2, zone_def, TMC_count)
                                buildList.append(TMC_count[0][0])
                                buildZoneList.append(TMC_count)
                            else:
                                pass
                        else:
                            #print("missed and not in List" + str(TMC_count[0]))
                            missed_Count = missed_Ray_method(pro_data, zone_def, TMC_count[0][0], Count)
                            break_out = True
                            break

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


def missed(Count, zone_def, raw_output, TMC_count, count_rng, zone_coords):
    # TODO: this classifies the vehicles with only 1 intersect captured by checking the distance
    #   of the first detection to the closest zone and then same thing with the last.
    #   UPGRADE this with an algoithm that checks direction -> so 'plot' or somehow check the
    #   direction and path of the movement and compare to the movements of the classified from above.
    #   least squares regression? - scipy
    #   ------------------------------------------------------------------------------------
    #   UPDATE: Dont check all of the zones - just the entering zones for the start points
    #   and the exiting zones for the end points. NOT GOING TO WORK IF ALL DEFINED ZONES ARE BOTH
    #   ENTER/EXIT
    movement = [0] * 4
    id_2_find = TMC_count[0][0]  # id pf the single detection

    raw_count = 0
    breakout = False
    # print(raw_output)
    for ids in raw_output:
        raw_count += 1
        for id in ids:
            if id_2_find in id and id.index(id_2_find) == 0:
                breakout = True
                break
        if breakout:
            break

    if breakout:  # if id_2_find was not found - dont run following
        # first and last detected coords
        raw_list = raw_output[raw_count - 1]
        # print(raw_list)
        enter_coords = raw_list[0]
        enter_coords = enter_coords[1:]
        exit_coords = raw_list[-1]
        exit_coords = exit_coords[1:]

        ent_distance = []
        ext_distance = []
        for coords in zone_coords:
            # zone midpoint coords
            center_x = (coords[0][0] + coords[1][0]) / 2
            center_y = (coords[0][1] + coords[1][1]) / 2
            center_coords = [center_x, center_y]
            # check distances
            distance = math.sqrt((center_coords[0] - enter_coords[0]) ** 2 + (center_coords[1] - enter_coords[1]) ** 2)
            ent_distance.append(distance)

            distance = math.sqrt((center_coords[0] - exit_coords[0]) ** 2 + (center_coords[1] - exit_coords[1]) ** 2)
            ext_distance.append(distance)

        # find minimum distance to the zones - this should be the enter/exit zone
        min_dist_ent = min(ent_distance)
        min_dist_ext = min(ext_distance)
        enter_zone = ent_distance.index(min_dist_ent) + 1
        exit_zone = ext_distance.index(min_dist_ext) + 1

        # classify the movement
        k = 0
        l = 0
        sub_break_out = False
        for rng in range(count_rng):  # loop through all 16 possible movement
            if (enter_zone == zone_def[l]) or (enter_zone == zone_def[l + 1]):
                for move in movement:  # loop through each 4 sub movements
                    if (exit_zone == zone_def[l + 2]) or (exit_zone == zone_def[l + 3]):
                        Count[k] += 1
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


def missed_Ray_method(raw_data, zone_def, id_2_find, Count):
    count_rng = len(Count) - 3
    ZoneList = []

    for TMC_count in raw_data:  # For each unique id
        if int(id_2_find) == TMC_count[0][0]:
            zoneFound = False
            z1 = None
            z1_x = None
            z2 = None
            z1_ave = []
            count = 0
            foundOutside = False
            # First check that the detection started outside the zone box: ie. there are 2 non zero values
            for i in range(len(TMC_count)):
                if TMC_count[i][3] != 0 and TMC_count[i][4] != 0:
                    z1_ave.append(TMC_count[i][3])

                    foundOutside = True

            if z1_ave:
                z1_ave = Counter(z1_ave)
                z1_ave = z1_ave.most_common(1)[0][0]

            if foundOutside:
                while count < len(TMC_count):  # loop through each detection in unique id
                    if TMC_count[count][3] != 0 and TMC_count[count][4] != 0 and not zoneFound:
                        #z1 = TMC_count[count][3]  # save the first non-zero zone detection as z1
                        #z1_x = TMC_count[count][3]
                        z1 = z1_ave
                        z1_x = z1_ave
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
            #print(ZoneList)
            Count = classify(Count, count_rng, z1, z2, zone_def, TMC_count)
        else:
            pass
    return Count


def missed_CP_method(Count, zone_def, raw_data, TMC_count, count_rng, pro_data, zone_coords):
    id_2_find = TMC_count[0][0]  # id pf the single detection

    # FIND THE DATA ASSOCIATED WITH THE ID_2_FIND
    raw_count_ID = 0
    # midpoint = []
    breakout = False
    for ids in raw_data:
        raw_count_ID += 1
        for id in ids:
            if id_2_find in id and id.index(id_2_find) == 0:
                breakout = True
                # FIND THE MIDPOINT
                x1r = raw_data[raw_count_ID - 1][0][1]
                x2r = raw_data[raw_count_ID - 1][-1][1]
                y1r = raw_data[raw_count_ID - 1][0][2]
                y2r = raw_data[raw_count_ID - 1][-1][2]
                if len(pro_data[raw_count_ID - 1]) == 1:
                    midpoint = [((x2r + x1r) / 2), ((y2r + y1r) / 2)]
                    #midpoint = [pro_data[raw_count_ID - 1][0][1], pro_data[raw_count_ID - 1][0][2]]
                    # slope = y2 - y1 / x2 - x1 (x2,y2) is the entering zone first
                    slope_y_enter = y1r - midpoint[1]
                    slope_x_enter = x1r - midpoint[0]
                    slope_y_exit = y2r - midpoint[1]
                    slope_x_exit = x2r - midpoint[0]
                elif len(pro_data[raw_count_ID - 1]) > 1:
                    midpoint = [((x2r + x1r) / 2), ((y2r + y1r) / 2)]
                    print(midpoint)
                    midpoint = NN(pro_data[raw_count_ID - 1], midpoint)
                    slope_y_enter = y1r - midpoint[1]
                    slope_x_enter = x1r - midpoint[0]
                    slope_y_exit = y2r - midpoint[1]
                    slope_x_exit = x2r - midpoint[0]
                else:
                    # IF THE MIDPOINT IS NOT WITHIN THE ZONE BOX - NEW IDEA???
                    pass
                    midpoint = [((raw_data[raw_count_ID - 1][-1][1] + raw_data[raw_count_ID - 1][0][1]) / 2),
                                ((raw_data[raw_count_ID - 1][-1][2] + raw_data[raw_count_ID - 1][0][2]) / 2)]

                EndPointX_enter = 20 * slope_x_enter + midpoint[0]
                EndPointY_enter = 20 * slope_y_enter + midpoint[1]
                EndPointX_exit = 20 * slope_x_exit + midpoint[0]
                EndPointY_exit = 20 * slope_y_exit + midpoint[1]

                EnterZone = 0
                ExitZone = 0
                zone_found, zone = INTERSECT(midpoint[0], midpoint[1], EndPointX_enter, EndPointY_enter, zone_coords)
                if zone_found:
                    EnterZone = zone
                zone_found, zone = INTERSECT(midpoint[0], midpoint[1], EndPointX_exit, EndPointY_exit, zone_coords)
                if zone_found:
                    ExitZone = zone

                if EnterZone == 0 and ExitZone == 0:
                    # Only 1 data point in the raw_data
                    break
                # CASE - DATA MIDPOINT LINES OUTSIDE THE ZONE BOX
                # TODO: data outside the zone box are most likly anomolies - not going to classify
                if EnterZone == 0:
                    break
                    num_intersections, intersection_list = INTERSECT(midpoint[0], midpoint[1], EndPointX_exit,
                                                                     EndPointY_exit, zone_coords, True)
                    EnterZone = intersection_list[0][2]
                    ExitZone = intersection_list[-1][2]
                if ExitZone == 0:
                    break
                    num_intersections, intersection_list = INTERSECT(midpoint[0], midpoint[1], EndPointX_enter,
                                                                     EndPointY_enter, zone_coords, True)
                    EnterZone = intersection_list[-1][2]
                    ExitZone = intersection_list[0][2]
                if EnterZone != 0 and ExitZone != 0:
                    Count = classify(Count, count_rng, EnterZone, ExitZone, zone_def, TMC_count)
                    break
                else:
                    break
        if breakout:
            break

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
                    if k == 14:
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

# TODO organize the raw data into all ids that have the same frmae number
#   then check the distance squared of each id to all the others - if then square distance is less than 25?
#   then add that those ids to a list of potential ids to delete
def id_change_frame(frame_data):
    pot_ids_delete = []
    pot_ids_delete_2 = []

    frame_data = frame_data[1:]  # remove the first blank element
    for frame in frame_data:
        for i in range(len(frame)):
            for j in range(len(frame)):
                if i != j:
                    p1 = [frame[i][1], frame[i][2]]
                    p2 = [frame[j][1], frame[j][2]]
                    sq_distance = ((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)
                    if sq_distance < 25:
                        id = frame[i][0]
                        id_check = False
                        if id not in pot_ids_delete_2:
                            pot_ids_delete_2.append(frame[i][0])
                        for k in pot_ids_delete:
                            if id in k:
                                id_check = True
                        if not id_check:
                            pot_ids_delete.append([frame[i][0], frame[j][0]])
    return pot_ids_delete, pot_ids_delete_2


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
        k = 0
        for point in range(len(id)):
            while i < len(id) -1:
                if k == 0:  # this should only run once
                    p2 = [id[i][1], id[i][2]]
                    k += 1
                else:
                    i += 1
                    p1 = [id[i][1], id[i][2]]
                    #distance = math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)
                    sq_distance = ((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)
                    if sq_distance < 40:
                        removed_element = processed_output[j].pop(i)
                        #print(removed_element, distance)
                        i -= 1
                        if len(processed_output[j]) == 0:  # if the list is empty
                            processed_output[j].pop()
                    else:
                        if i < len(id) - 1: # chek we arnt at the end of the list or get index error
                            #i += 1
                            p2 = [id[k][1], id[k][2]]
                            k += 1
                        else:
                            break
        j += 1
    return processed_output


def remove_outside_zone_box(data, w, h, zone_coords):
    j = 0
    for id in data:
        i = 0
        for point in id:
            while i < len(id) - 1:
                num_intersections = 0
                for k in range(4):
                    x = [point[1], w, point[1], 0]
                    y = [0, point[2], h, point[2]]
                    num_intersections = INTERSECT(point[1], point[2], x[k], y[k], zone_coords, True)
                    if num_intersections[0] > 0:
                        breakout = True
                        break
                if num_intersections[0] == 2:
                    removed_element = data[j].pop(i)
                else:
                    i += 1
        j += 1
    return data


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
                        if len(processed_static[j][i:]) > 1:  # if there are 2 detections following
                            new_processed_static.append(processed_static[j][i:])
                            processed_static[j] = processed_static[j][:i]
                            break
                        # TODO : remove the 3rd detection - this makes the count worse for now but it is correct.
                        elif len(processed_static[j][i:]) == 1:
                            print("id to find" + str(processed_static[j]))
                            processed_static[j] = processed_static[j][:i]  # Delete the last value
                            break
                    else:
                        i += 1
                        p2 = id[i][3]
        j += 1
    for i in range(len(new_processed_static)):
        processed_static.append(new_processed_static[i])
    return processed_static


def preprocessing(data, data_zone_detections, zone_coords, frame_data):
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
    #     if the the detections are say 3 - 1 - 1 - 3 : create a new 'id' to classify
    #   4. Remove Anomolies - do this before step 3. Remove the data points that are 'outliers'

    # TODO: need to get height and width of video automatically
    w = 1280
    h = 720

    processed_output, num_values = organize_list(data_zone_detections)

    #  1. IF THE VEHICLES ARE NOT MOVING OVER A DETECTION ZONE
    processed_static = remove_static_detections(processed_output)
    processed_static_raw_data = remove_static_detections(data)

    pot_ids_delete, pot_ids_delete_2 = id_change_frame(frame_data)
    #print(pot_ids_delete)

    # 2. REMOVE DATA FROM OUTSIDE THE ZONE BOX
    #processed_zone_box = remove_outside_zone_box(data, w, h, zone_coords)

    #  3. 3 - 1 - 3 : remove last 3
    processed_zone_detections = remove_bad_detections(processed_static)

    return processed_static_raw_data, processed_zone_detections, num_values, pot_ids_delete, pot_ids_delete_2


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
    zone_def = open("./TMC Testing/test27-nysdotv1.3/zone_pkl_dump.pkl", "rb")
    zone_def = pickle.load(zone_def)


    zone_coords = open("./TMC Testing/test27-nysdotv1.3/zone_coords_pkl_dump.pkl", "rb")
    zone_coords = pickle.load(zone_coords)

    frame_data = open("./TMC Testing/test27-nysdotv1.3/frame_data.pkl", "rb")
    frame_data = pickle.load(frame_data)

    # ZONE INTERSECTION DETECTIONS
    data = open("./TMC Testing/test27-nysdotv1.3/data_zones_test.pkl", "rb")
    data = pickle.load(data)
    data.sort(key=lambda p: p[0])
    df = pd.DataFrame(data)
    df.to_csv(r'data.csv')

    #   RAW DATA = ALL DETECTIONS WITH ZONE INTERSECTIONS
    raw_data = open("./TMC Testing/test27-nysdotv1.3/data_test.pkl", "rb")
    raw_data = pickle.load(raw_data)
    raw_data.sort(key=lambda p: p[0])
    #raw_data = raw_data[1:]  # first element is blank - remove it
    df = pd.DataFrame(raw_data)
    df.to_csv(r'raw_data.csv')

    pro_raw_data = raw_data.copy()
    processed_raw_data, processed_zone_detections, num_values, ids_delete, ids_delete_2 = preprocessing(pro_raw_data,
                                                                                                        data,
                                                                                                        zone_coords,
                                                                                                        frame_data)
    print(ids_delete)
    # RELOAD THE RAW DATA AND THE ZONE DETECTIONS
    raw_data = open("./TMC Testing/test27-nysdotv1.3/data_test.pkl", "rb")
    raw_data = pickle.load(raw_data)
    raw_data.sort(key=lambda p: p[0])
    #raw_data = raw_data[1:]  # first element is blank - remove it
    #processed_static_raw = remove_static_detections(raw_data)  # REMOVE THE STATIC VEHICLES FROM THE RAW DATA

    data = open("./TMC Testing/test27-nysdotv1.3/data_zones_test.pkl", "rb")
    data = pickle.load(data)
    data.sort(key=lambda p: p[0])
    data = organize_list(data)

    r, missed, missed_Count = TMC_class(raw_data, processed_raw_data, processed_zone_detections, num_values, zone_def,
                                        zone_coords, start_time=1600, interval=1, ids_delete=ids_delete,
                                        ids_delete_2=ids_delete_2)
    print(r, missed, missed_Count)
