from itertools import islice
import numpy as np
import math
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
                    # TODO: when the last frame is reached - any ids that have not been classified will need to
                    #   saved to the next 15min bin.
                    if TMC_count[-1][-1] > lastFrame - 3:  # within the last 3 frames
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
                            missed_Count = missed_Ray_method(pro_data, zone_def, TMC_count[0][0], Count)
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
                    sq_distance = ((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)
                    if sq_distance < 40:
                        removed_element = processed_output[j].pop(i)
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
    # TODO: need to get height and width of video automatically
    w = 1280
    h = 720

    processed_output, num_values = organize_list(data_zone_detections)

    #  1. IF THE VEHICLES ARE NOT MOVING OVER A DETECTION ZONE
    processed_static = remove_static_detections(processed_output)
    processed_static_raw_data = remove_static_detections(data)

    pot_ids_delete, pot_ids_delete_2 = id_change_frame(frame_data)

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
