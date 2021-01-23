var jsoneditor;

$(document).ready(function () {
    var raw_data = $("#data").data();
    var data = JSON.parse(raw_data);
    
    var jsoneditor = new JsonEditor($("#jsoneditor"), {mode: "tree"})

    jsoneditor.set(data)
});

function updateConfig() {
    const url = "http://127.0.0.1:5000/update/config";
    var data = jsoneditor.get();
    $.post(url, data, function (data, status) {
        console.log(`${status} - ${data}`);
    });
}