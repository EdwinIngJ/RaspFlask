$(document).ready(function () {

    var socket = io.connect('http://' + document.domain + ':' + location.port);

    socket.on('StatusUpdate', function (msg) {
        console.log("Received UpdateStatus");
        LastUpdatedmsg = "Last Updated: " + msg.last_updated
        $('#LastUpdated').text(LastUpdatedmsg);
        $('#Plant1Status').text("Plant 1: " +msg.Plant1)
        $('#Plant2Status').text("Plant 2: " +msg.Plant2)
        $('#Plant3Status').text("Plant 3: " +msg.Plant3)
        $('#Plant4Status').text("Plant 4: " +msg.Plant4)
        $('#TankStatus').text("Tank: " +msg.Tank)
        if (msg.MW == "OFF") {
            $('#MW').prop('checked', false);
        } else {
            $('#MW').prop('checked', true)
        }
        if (msg.AW == "OFF") {
            $('#AW').prop('checked', false);
        } else {
            $('#AW').prop('checked', true);
        }
    })
	

});

$("#AW").on('change', function () {
	var socket = io.connect('http://' + document.domain + ':' + location.port);
    if ($(this).is(':checked')) {
	socket.emit('client', {"data": "auto_checked"});

    }
    else {
	socket.emit('client', {"data": "auto_unchecked"});
    }
});

$("#MW").on('change', function () {
	var socket = io.connect('http://' + document.domain + ':' + location.port);
    if ($(this).is(':checked')) {
	socket.emit('client', {"data": "manual_checked"});
    }
    else {
      	socket.emit('client', {"data": "manual_unchecked"});
    }
});
