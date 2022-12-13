let width = $("#video")[0].width;
let height = $("#video")[0].height;
//Set the canvas properties - need fabric.js
let canvas = new fabric.Canvas('canvas',{
    width: width,
    height: height,
    background: null,
});

//create object from image from html id
let imgElement = $("#my-image")[0];

fabric.Image.fromObject(imgElement,(img)=>{
    canvas.backgroundImage = img
    canvas.renderAll()
});

//set the button id to a variable 'addingLineBtn'
let addingLineBtn = $("#adding-line-btn")[0];

//Call the function 'activateAddingLine' When button is pressed
addingLineBtn.addEventListener('click', activateAddingLine);

let imageSaver = $("#save-image-btn");
imageSaver.addEventListener('click', SaveImage, false);

//create random int
function getRandomInt(max) {
  return Math.floor(Math.random() * max);
}


//TODO: allow add click only once
function activateAddingLine(){
    //clear out the list if button is not disabled
    if (addingLineBtn.disabled === false){
        console.log('refresh list');
        send_coords_toFlask(0, 0, 0, 0);
    }
    
    //add a disable class when button is click so it cant be clicked a second time
    $('.btn').addClass('disabled');

    //Add event listeners
    canvas.on('mouse:down', startAddingLine);
    canvas.on('mouse:move', startDrawingLine);
    canvas.on('mouse:up', stopDrawingLine);

    canvas.selection = false;
}


let line;
let mouseDown = false;
let click_event;
let count = 0;
let color;
let color_str;
let pad = 20;
let color_list = [];
let color_dict = [];

function startAddingLine(o){
    mouseDown = true;
    click_event = 1;
    let  pointer = canvas.getPointer(o.e);

    color = [getRandomInt(255), getRandomInt(255), getRandomInt(255)]; 
    color_str = `rgb(${color[0]},${color[1]},${color[2]})`;
    color_list.push(color_str);

    console.log(color_list);

    //color_list.append(color_str);
    line = new fabric.Line([pointer.x, pointer.y, pointer.x, pointer.y], {
        stroke: color_str,
        strokeWidth: 5,
    });

    let circle = new fabric.Circle({
        radius: 10,
        fill: color_str,
        left: pointer.x - 10,
        top: pointer.y - 10,
        selectable: false
    });

    canvas.add(line);
    canvas.add(circle);
    canvas.requestRenderAll();
    send_coords_toFlask(pointer.x, pointer.y, click_event);
}

function startDrawingLine(o){
    if (mouseDown === true){
        let  pointer = canvas.getPointer(o.e);

        line.set({
            x2: pointer.x,
            y2: pointer.y
        });

        canvas.requestRenderAll();
    }

}

function stopDrawingLine(o){
    count = count + 1;

    //Create dictionay of colors : zones {key : value}
    color_dict.push({'color': color_str,
                    'zone' : count}
                    );
    console.log(color_dict);

    let  pointer = canvas.getPointer(o.e);
    click_event = 2;
    mouseDown = false;
    send_coords_toFlask(pointer.x, pointer.y, click_event);
    line_center_x = (line.x1 + line.x2) / 2 - 20;
    line_center_y = (line.y1 + line.y2) / 2 - 20;

    let circle = new fabric.Circle({
        radius: 20,
        fill: color_str,
        left: line_center_x,
        top: line_center_y,
        selectable: false
    });
    let circle2 = new fabric.Circle({
        radius: 10,
        fill: color_str,
        left: pointer.x - 10,
        top: pointer.y - 10,
        selectable: false
    });

    let zone_num = count.toString();
    let text = new fabric.Text(zone_num, { 
        left: line_center_x + 13, 
        top: line_center_y + 5,
        stroke: 'white',
        fontSize: 30,
        fill: 'white'
        });
    canvas.add(circle2);
    canvas.add(circle);
    canvas.add(text);
    canvas.renderAll();

    //Create a DropDownList element.
    let ddID = document.getElementsByClassName("drop_dwn");
    //let ddID = document.getElementById("drop_down");
    //Add the Options to the DropDownList.

    for (var i = 0; i < ddID.length; i++) {
        let option = document.createElement("OPTION");
        //Set Customer Name in Text part.
        option.innerHTML = "Zone " + zone_num;
        //Set CustomerId in Value part.
        option.value = count;
        option.style.color = color_str;

        //Add the Option element to DropDownList.
        ddID[i].options.add(option);
    }

}


function send_coords_toFlask(x, y, click_event, id){
    dict = {x, y, click_event};

    const s = JSON.stringify(dict);
    const request = new XMLHttpRequest();

    $.ajax({
            url:"/Receive_coords",
            type:"POST",
            contentType: "application/json",
            data: JSON.stringify(s)
        });

}

function  SaveImage(){
    //check if zones filled out
    let z1 = document.getElementById('drop_down_1');
    let z2 = document.getElementById('drop_down_17');
    let z3 = document.getElementById('drop_down_33');
    let z4 = document.getElementById('drop_down_49');

    if (z1.value == 0 && z2.value == 0 && z3.value == 0 && z4.value == 0){
        alert("Must define the zones first");
    }
    else{
        console.log("Image Saved");

        const s = JSON.stringify(color_dict);
        const request = new XMLHttpRequest();

        $.ajax({
                url:"/SaveImage",
                type:"POST",
                contentType: "application/json",
                data: JSON.stringify(s)
                });

        alert("Image Saved to static/img/image_clone.jpg");
    }  

}


$('select[class="drop_dwn"]').change(function(){
    let value = this.value;
    let ID = this.id;

    this.style.color = color_list[value - 1]

    let dict = {value, ID};
    let s = JSON.stringify(dict);

    let request = new XMLHttpRequest();
     $.ajax({
            url:"/record_Zone",
            type:"POST",
            contentType: "application/json",
            data: JSON.stringify(s)
            });


    if (this.id == "drop_down_1"){
        //Autofill the next 3
        for (let i = 5; i < 14; i+=4) {
            let elm = document.getElementById(`drop_down_${i}`);
            console.log(elm);
            elm.selectedIndex = this.value;
            elm.style.color = color_list[value - 1]

            value = elm.value;
            ID = elm.id;
            dict = {value, ID};
            s = JSON.stringify(dict);
            request = new XMLHttpRequest();
            $.ajax({
                url:"/record_Zone",
                type:"POST",
                contentType: "application/json",
                data: JSON.stringify(s)
                });
        }
    }

        if (this.id == "drop_down_17"){
        //Autofill the next 3
        for (let i = 21; i < 30; i+=4) {
            let elm = document.getElementById(`drop_down_${i}`);
            console.log(elm);
            elm.selectedIndex = this.value;
            elm.style.color = color_list[value - 1]

            value = elm.value;
            ID = elm.id;
            dict = {value, ID};
            s = JSON.stringify(dict);
            request = new XMLHttpRequest();
            $.ajax({
                url:"/record_Zone",
                type:"POST",
                contentType: "application/json",
                data: JSON.stringify(s)
                });
        }

     }

     if (this.id == "drop_down_33"){
        //Autofill the next 3
        for (let i = 37; i < 46; i+=4) {
            let elm = document.getElementById(`drop_down_${i}`);
            console.log(elm);
            elm.selectedIndex = this.value;
            elm.style.color = color_list[value - 1]

            value = elm.value;
            ID = elm.id;
            dict = {value, ID};
            s = JSON.stringify(dict);
            request = new XMLHttpRequest();
            $.ajax({
                url:"/record_Zone",
                type:"POST",
                contentType: "application/json",
                data: JSON.stringify(s)
                });
        }

     }

    if (this.id == "drop_down_49"){
            //Autofill the next 3
            for (let i = 53; i < 62; i+=4) {
                let elm = document.getElementById(`drop_down_${i}`);
                console.log(elm);
                elm.selectedIndex = this.value;
                elm.style.color = color_list[value - 1]

                value = elm.value;
                ID = elm.id;
                dict = {value, ID};
                s = JSON.stringify(dict);
                request = new XMLHttpRequest();
                $.ajax({
                    url:"/record_Zone",
                    type:"POST",
                    contentType: "application/json",
                    data: JSON.stringify(s)
                    });
            }

         }


});
