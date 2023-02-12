from itertools import islice
import numpy as np
import pandas as pd
import pickle
import math
from collections import Counter
import matplotlib.pyplot as plt


class TmcClassification:
    def __init__(self, processed_raw_data, processed_zone_detections, num_values, zone_def, ids_delete=[],
                 ids_delete_2=[], ids_last_frame=[], interval=1):
        self.processed_raw_data = processed_raw_data
        self.processed_zone_detections = processed_zone_detections
        self.num_values = num_values
        self.zone_def = zone_def
        self.ids_delete = ids_delete
        self.ids_delete_2 = ids_delete_2
        self.ids_last_frame = ids_last_frame
        self.interval = interval
        self.Count = [0] * 16
        self.Missed = []
        self.missed_Count = [0] * 16
        self.CarryOverDetections = []
        self.buildZoneList = []
        self.start_time = 1600

    def TMC_count(self):
        movement = [0] * 4
        count_rng = len(self.Count) - 3
        buildList = []
        plt_colors = ['c', 'g', 'm', 'y']  # NB, SB, EB, WB

        for TMC_count in self.processed_zone_detections:  # loop through each group of detections
            j = 0
            i = 0
            break_out = False

            for z in self.CarryOverDetections:
                if TMC_count[0][0] == z[0]:
                    TMC_count.insert(0, z)

            for zone in range(count_rng):  # loop through all 16 possible movement
                if (TMC_count[0][3] == self.zone_def[i]) or (TMC_count[0][3] == self.zone_def[i + 1]):
                    if (TMC_count[0][1] != TMC_count[-1][1]) and (TMC_count[0][2] != TMC_count[-1][2]):  # Check if there is only 1 zone detection
                        if i == 52 or i == 56:
                            movement = [0]*3
                        for move in movement:  # loop through each 4 sub movements
                            if TMC_count[-1][3] == self.zone_def[i + 2] or TMC_count[-1][3] == self.zone_def[i + 3]:
                                self.Count[j] += 1

                                if j <= 3:
                                    clr = plt_colors[0]
                                elif (j <= 7) and (j > 3):
                                    clr = plt_colors[1]
                                elif (j <= 11) and (j > 7):
                                    clr = plt_colors[2]
                                else:
                                    clr = plt_colors[3]

                                make_plot(self.processed_raw_data, TMC_count[0][0], clr=clr, alpha=0.2)

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
                        MatchFound = False

                        if TMC_count[-1][0] in self.ids_last_frame:
                            self.CarryOverDetections.append(TMC_count[0])
                            break
                        else:
                            if TMC_count[0][0] in self.ids_delete_2:  # if the id is in the potential ids to delete list
                                if TMC_count[0][0] not in buildList:  # Save each unique ID
                                    for i in buildList:
                                        for ii in self.ids_delete:
                                            if i in ii and TMC_count[0][0] in ii:
                                                z1 = self.buildZoneList[buildList.index(i)][0][3]
                                                z2 = TMC_count[-1][3]
                                                MatchFound = True
                                    buildList.append(TMC_count[0][0])
                                    self.buildZoneList.append(TMC_count)
                                else:
                                    pass
                                if MatchFound:
                                    make_plot(self.processed_raw_data, TMC_count[0][0])
                                    self.Count = classify(self.Count, count_rng, z1, z2, self.zone_def, TMC_count)
                                    break
                                else:
                                    break
                            else:
                                make_plot(self.processed_raw_data, TMC_count[0][0])
                                self.missed_Count = missed_Ray_method(self.processed_raw_data, self.zone_def,
                                                                      TMC_count[0][0], self.Count)
                                break

                if break_out:
                    break
                i += 4
                j += 1
        #plt.show()
        plt.savefig('Output_graph.jpg')

        self.Missed = self.num_values - sum(self.Count)
        i = 0
        Count_str = []
        for s in self.Count:
            Count_str.append(str(s))
            i += 1

        with open("Output.txt", "r") as Output:
            markdown_list = Output.readlines()

        #markdown_list = [["TIME", "NBR", "NBT", "NBL", "NBU", "SBR", "SBT", "SBL", "SBU", "EBR", "EBT", "EBL", "EBU", "WBR",
        #                  "WBT", "WBL", "WBU"], Count_str]
        mkdown = make_markdown_table(markdown_list, self.interval, self.start_time, Count_str)
        file1 = open("Output.txt", "w")
        file1.write(mkdown)
        file1.close()


def make_plot(processed_raw_data, TMC_count, clr='k', alpha=1):
    break_loop = False
    Index = 0
    for ii in processed_raw_data:
        for k in ii:
            if k[0] == TMC_count:
                break_loop = True
                break
        Index += 1
        if break_loop:
            break
    x = []
    y = []
    for ii in processed_raw_data[Index - 1]:
        x.append(ii[1])
        y.append(ii[2])
    plt.scatter(x, y, color=clr, alpha=alpha)


class Preprocessing:
    def __init__(self, pro_raw_data, data_zones, frame_data):
        self.frame_data = frame_data

        processed_output, self.num_values = organize_list(data_zones)
        processed_static = remove_static_detections(processed_output)

        self.processed_static_raw_data = remove_static_detections(pro_raw_data)
        self.pot_ids_delete, self.pot_ids_delete_2, self.ids_last_frame = id_change_frame(self.frame_data)
        self.processed_zone_detections = remove_bad_detections(processed_static)


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
                while i < len(id) - 1:
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
                            if i < len(id) - 1:  # chek we arnt at the end of the list or get index error
                                p2 = [id[k][1], id[k][2]]
                                k += 1
                            else:
                                break
            j += 1
        return processed_output


def id_change_frame(frame_data):
        pot_ids_delete = []
        pot_ids_delete_2 = []
        ids_last_frame = []
        last_frame = frame_data[-1][-1][3]

        frame_data = frame_data[1:]  # remove the first blank element
        for frame in frame_data:
            for i in range(len(frame)):
                for j in range(len(frame)):
                    # create list o fids in the last frame
                    if frame[j][3] == last_frame and frame[j][0] not in ids_last_frame:
                        ids_last_frame.append(frame[j][0])
                    # create a list of ids that could of possibly been reused
                    if i != j:
                        p1 = [frame[i][1], frame[i][2]]
                        p2 = [frame[j][1], frame[j][2]]
                        sq_distance = ((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)
                        if sq_distance < 625:
                            id = frame[i][0]
                            id_check = False
                            if id not in pot_ids_delete_2:
                                pot_ids_delete_2.append(frame[i][0])
                            for k in pot_ids_delete:
                                if id in k:
                                    id_check = True
                            if not id_check:
                                pot_ids_delete.append([frame[i][0], frame[j][0]])
        return pot_ids_delete, pot_ids_delete_2, ids_last_frame


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
                print(TMC_count[0][0], z1_ave)

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
    with open("./!ZoneMethod Testing/test20/zone_pkl_dump.pkl", "rb") as file:
        zone_def = pickle.load(file)

    with open("./!ZoneMethod Testing/test20/zone_coords_pkl_dump.pkl", "rb") as file:
        zone_coords = pickle.load(file)

    with open("./!ZoneMethod Testing/test20/frame_data.pkl", "rb") as file:
        frame_data = pickle.load(file)

    # ZONE INTERSECTION DETECTIONS
    data = open("./!ZoneMethod Testing/test20/data_zones_test.pkl", "rb")
    data = pickle.load(data)
    data.sort(key=lambda p: p[0])
    df = pd.DataFrame(data)
    df.to_csv(r'data.csv')

    #   RAW DATA = ALL DETECTIONS WITH ZONE INTERSECTIONS
    raw_data = open("./!ZoneMethod Testing/test20/data_test.pkl", "rb")
    raw_data = pickle.load(raw_data)
    raw_data.sort(key=lambda p: p[0])
    df = pd.DataFrame(raw_data)
    df.to_csv(r'raw_data.csv')

    pro_raw_data = raw_data.copy()

    ProcessedData = Preprocessing(pro_raw_data, data, frame_data)
    print(ProcessedData.processed_zone_detections)
    print(ProcessedData.pot_ids_delete)

    # RELOAD THE RAW DATA AND THE ZONE DETECTIONS
    raw_data = open("./!ZoneMethod Testing/test20/data_test.pkl", "rb")
    raw_data = pickle.load(raw_data)
    raw_data.sort(key=lambda p: p[0])

    data = open("./!ZoneMethod Testing/test20/data_zones_test.pkl", "rb")
    data = pickle.load(data)
    data.sort(key=lambda p: p[0])
    data = organize_list(data)

    TMC_Counter = TmcClassification(ProcessedData.processed_static_raw_data, ProcessedData.processed_zone_detections,
                                    ProcessedData.num_values, zone_def, interval=1,
                                    ids_delete=ProcessedData.pot_ids_delete,
                                    ids_delete_2=ProcessedData.pot_ids_delete_2,
                                    ids_last_frame=ProcessedData.ids_last_frame)
    TMC_Counter.TMC_count()
    print(TMC_Counter.Count, TMC_Counter.missed_Count, TMC_Counter.CarryOverDetections)
