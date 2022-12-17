import cv2
from flask import Flask, render_template, Response, request
import json
import pickle
import  tkinter as tk
from tkinter import filedialog

app = Flask(__name__)
zone_pass = []
zone__pass = []
mask = []

root = tk.Tk()
root.withdraw()
file_path = filedialog.askopenfilename(initialdir='./static')

vid = cv2.VideoCapture(file_path)
height = vid.get(cv2.CAP_PROP_FRAME_HEIGHT)
width = vid.get(cv2.CAP_PROP_FRAME_WIDTH)

file_path = file_path.split('static')
file_path = file_path[1][1:]


@app.route('/')
def index():
    return render_template('index copy.html',width=width, height=height, FileName=file_path)


@app.route('/help')
def help():
    return render_template('help.html')


@app.route('/Recieve_coords', methods=['POST'])
def Recieve_coords():
    output = request.get_json()
    result = json.loads(output)
    x = result['x']
    y = result['y']
    event = result['click_event']

    if int(event) == 0:
        zone__pass.clear()
    if int(event) == 1:
        zone_pass.append([x, y])
        print(zone_pass)
    if int(event) == 2:
        zone__pass.append([zone_pass[-1], [x, y]])
        print(zone__pass)
    if int(event) == 3:
        mask.append([x, y])
        print(mask)

    if int(event) != 0:
        with open("zone_coords_pkl_dump.pkl", "wb") as file:
            pickle.dump(zone__pass, file)

    return ('/')


@app.route('/SaveImage', methods=['POST'])
def SaveImage():
    output = request.get_json()
    result = json.loads(output)

    source = './static/img/image.jpg'
    clone = cv2.imread(str(source))
    font = cv2.FONT_HERSHEY_SIMPLEX
    fontScale = 1

    print(zone__pass)
    i = 1
    j = 0
    colors = []
    for zone in zone__pass:
        color = result[j]['color']
        color = color.split('b')
        color = color[1]
        color = color[:-1]
        color = color[1:].split(',')
        color = (int(color[2]),int(color[1]),int(color[0]))
        print(color, type(color))
        colors.append(color)

        cv2.line(clone, (int(zone[0][0]), int(zone[0][1])),  (int(zone[1][0]), int(zone[1][1])),
                 color, 3)
        line_center_x = abs(zone[0][0] + zone[1][0]) / 2
        line_center_y = abs(zone[0][1] + zone[1][1]) / 2
        line_center = (int(line_center_x), int(line_center_y))

        cv2.circle(clone, line_center, 20, color, -1)
        cv2.circle(clone, (int(zone[0][0]), int(zone[0][1])), 7, color, -1)
        cv2.circle(clone, (int(zone[1][0]), int(zone[1][1])), 7, color, -1)

        text = str(i)
        textsize, base = cv2.getTextSize(text, font, 1, 2)
        textsize = textsize[0]
        txt_center = (int(line_center_x - (textsize / 2)), int(line_center_y - (textsize / 2) + base * 2))

        cv2.putText(clone, text, txt_center, font, fontScale, (255, 255, 255), 2, cv2.LINE_AA)
        i += 1
        j += 1

    with open("colors_pkl_dump.pkl", "wb") as file:
        pickle.dump(colors, file)
    with open("mask.pkl", "wb") as file:
        pickle.dump(mask, file)

    print(colors)

    cv2.imwrite('./static/img/image_clone.jpg', clone)
    print("Imaged Saved")

    return ('/')


zones = [0] * 64
@app.route('/record_Zone', methods=['POST'])
def record_Zone():
    output = request.get_json()
    result = json.loads(output)

    val = result['value']
    drop_down = result['ID']

    print(drop_down)
    idx = drop_down.split('_')
    idx = int(idx[2]) - 1
    zones[idx] = int(val)

    with open("zone_pkl_dump.pkl", "wb") as file:
        pickle.dump(zones, file)

    print(zones)

    return ('/')


if __name__ == '__main__':
    app.run(debug=True)
