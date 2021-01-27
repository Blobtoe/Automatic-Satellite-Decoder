var jsoneditor;

$(document).ready(function () {
    jsoneditor = new JSONEditor(document.getElementById("jsoneditor"), { mode: "tree" })
    getConfig();
});

function updateConfig() {
    var data = jsoneditor.get();
    $.ajax({
        type: "POST",
        url: "http://satellitestation.ddns.net:5000/update/config",
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
        url: "http://satellitestation.ddns.net:5000/get/config",
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
        url: `http://satellitestation.ddns.net:5000/get/next/pass?pass_count=${pass_count}`,
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
            start_time.innerHTML = `Start Time: ${new Date(element['aos'] * 1000).toString()} (in about ${deltaTime(new Date(element['aos'] * 1000), new Date())})`
            div.appendChild(start_time);

            var end_time = document.createElement("p");
            end_time.innerHTML = `End Time: ${new Date(element['los'] * 1000).toString()} (in about ${deltaTime(new Date(element['los'] * 1000), new Date())})`
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

function deltaTime(time1, time2) {
    var milliseconds = time1 - time2;
    var days = Math.floor(milliseconds / 86400000);
    var hours = Math.floor((milliseconds - (days * 86400000)) / 3600000);
    var minutes = Math.floor(((milliseconds - (days * 86400000)) - (hours * 3600000)) / 60000);
    var seconds = Math.floor((((milliseconds - (days * 86400000)) - (hours * 3600000)) - (minutes * 60000)) / 1000);
    return `${days} day${days == 1 ? "" : "s"}, ${hours} hour${hours == 1 ? "" : "s"}, ${minutes} minute${minutes == 1 ? "" : "s"} and ${seconds} second${seconds == 1 ? "" : "s"}`;
}