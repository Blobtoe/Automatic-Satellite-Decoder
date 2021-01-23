var jsoneditor;

$(document).ready(function () {
    var raw_data = $("#data").attr("data").replaceAll("'", '"')
    var data = JSON.parse(raw_data);
    
    var jsoneditor = new JSONEditor(document.getElementById("jsoneditor"), {mode: "tree"})

    jsoneditor.set(data["config"])
});

function updateConfig() {
    const url = "http://127.0.0.1:5000/update/config";
    var data = jsoneditor.get();
    $.post(url, data, function (data, status) {
        console.log(`${status} - ${data}`);
    });
}