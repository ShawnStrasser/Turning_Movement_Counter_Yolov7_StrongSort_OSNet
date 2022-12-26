let width = $("#video")[0].width;
let height = $("#video")[0].height;
//Set the canvas properties - need fabric.js
let canvas = new fabric.Canvas('canvas',{
    width: width,
    height: height,
    background: null,
});


//set the button id to a variable 'addingLineBtn'
let addingLineBtn = document.getElementById("adding-line-btn");


//Call the function 'activateAddingLine' When button is pressed
addingLineBtn.addEventListener('click', activateAddingLine);


//create random int
function getRandomInt(max) {
  return Math.floor(Math.random() * max);
}


//TODO: allow add click only once
function activateAddingLine(){
    //clear out the list if button is not disabled
    if (addingLineBtn.disabled === false){
        console.log('refresh list');
        //send_coords_toFlask(0, 0, 0, 0);
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
    log_coords(pointer.x, pointer.y, click_event);
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
    log_coords(pointer.x, pointer.y, click_event);
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
        textAlign: "center",
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

let csvContent = "data:text/csv;charset=utf-8,";
let StartZone = [];
let ZoneList = [];
let ZoneDef = Array(64).fill(0);

function log_coords(x, y, click_event){
    if (click_event == 1){
        StartZone = [x, y];
    };

    if (click_event == 2){
        ZoneList.push([StartZone,[x, y]]);
    };  
         
};


//let csvFileData = ZoneList;   
//create a user-defined function to download CSV file   
function  SaveData(id){
    console.log(id)
    if (id == 'save-image-btn'){
        data = ZoneList;
        fileName = 'data.csv'
    };
     //define the heading for each row of the data  
     var csv = '';  
        
     //merge the data with CSV  
     data.forEach(function(row) {  
             csv += row.join(',');  
             csv += "\n";  
            });  
 
    
    var hiddenElement = document.createElement('a');  
    hiddenElement.href = 'data:text/csv;charset=utf-8,' + encodeURI(csv);  
    hiddenElement.target = '_blank';  
    
    //provide the name for the CSV file to be downloaded  
    hiddenElement.download = fileName;  
    hiddenElement.click(); 
    
    SaveZones();
    //alert("Image Saved to static/img/image_clone.jpg");
}


$('select[class="drop_dwn"]').change(function(){
    let value = this.value;
    let ID = this.id;

    this.style.color = color_list[value - 1]

    indx = ID.split("_")[2] - 1
    ZoneDef[indx] = Number(value);
    console.log(ZoneDef)

});

function  SaveZones(){
    var data = ZoneDef
    var fileName = 'zone_def.csv'
     //define the heading for each row of the data  
     var csv = '';  
        
     //merge the data with CSV  
     data.forEach(function(row2) {  
             csv += row2.join(',');  
             csv += "\n";  
            });  
 
    
    var hiddenElement = document.createElement('a');  
    hiddenElement.href = 'data:text/csv;charset=utf-8,' + encodeURI(csv);  
    hiddenElement.target = '_blank';  
    
    //provide the name for the CSV file to be downloaded  
    hiddenElement.download = fileName;  
    hiddenElement.click(); 

    //alert("Image Saved to static/img/image_clone.jpg");
}