var jsoneditor;

$(document).ready(function () {
    jsoneditor = new JSONEditor(document.getElementById("jsoneditor"), { mode: "tree" })
    getConfig();
});

function updateConfig() {
    var data = jsoneditor.get();
    $.ajax({
        type: "POST",
        url: "http://127.0.0.1:5000/update/config",
        data: JSON.stringify(data),
        contentType: "application/json;charset=UTF-8"
    }).done(function (response) {
        console.log("Done");
    }).fail(function (response) {
        console.log("Failed to update config");
    })
}

function getConfig() {
    $.ajax({
        type: "GET",
        url: "http://127.0.0.1:5000/get/config",
        contentType: "application/json;charset=UTF-8",
        dataType: "json"
    }).done(function (response) {
        jsoneditor.set(response)
    }).fail(function (response) {
        console.log("Failed to get config");
    })
}

function getUpcomingPasses() {
    var pass_count = document.getElementById("pass_count").value;
    $.ajax({
        type: "GET",
        url: `http://127.0.0.1:5000/get/next/pass?pass_count=${pass_count}`,
        contentType: "application/json;charset=UTF-8",
        dataType: "json"
    }).done(function (response) {
        var upcoming_passes = document.getElementById("upcoming_passes");
        upcoming_passes.innerHTML = "";
        for (let i = 0; i < response.length; i++) {
            const element = response[i];

            var div = document.createElement("div");

            var title = document.createElement("h2");
            title.innerHTML = element["satellite"];
            div.appendChild(title);

            var start_time = document.createElement("p");
            start_time.innerHTML = "Start Time: " + new Date(element["aos"] * 1000).toString();
            div.appendChild(start_time);

            var end_time = document.createElement("p");
            end_time.innerHTML = "End Time: " + new Date(element["los"] * 1000).toString();
            div.appendChild(end_time);

            var max_elevation = document.createElement("p");
            max_elevation.innerHTML = "Max Elevation: " + element["max_elevation"];
            div.appendChild(max_elevation);

            var direction = document.createElement("p");
            direction.innerHTML = "Direction: " + element["direction"];
            div.appendChild(direction);

            upcoming_passes.appendChild(div);
        }
    }).fail(function (response) {
        console.log("Failed to get next passes");
    })
}