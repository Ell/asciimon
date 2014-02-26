pokestream = new ReconnectingWebSocket('ws://' + location.host + '/pokemon');

console.log('test');

pokestream.onmessage = function(message) {
    //console.log("got message");
    var args = message.data.split('\t');
    var data_el = document.getElementById('data');
    var text = data_el.textContent;
    var pos = 0;
    for (var i = 0; i < args.length; i += 2) {
        pos += +args[i];
        var data = args[i + 1];
        text = text.substring(0, pos) + data + text.substring(pos+data.length);
        pos += data.length;
    }
    data_el.textContent = text.substring(0, 18 * 21 - 1);
}
