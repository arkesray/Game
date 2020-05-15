var socket;

function sendMsgEnter(e) {
    if( e.keyCode == 13 || e.key == 'enter' || e == 'click')
        {
            msg = document.getElementById("msg").value;
            if (msg != "") {
                document.getElementById("msg").value = null;
                socket.emit('inputMsg', msg);
            }
        }
}
function sendMsg() {
    msg = document.getElementById("msg").value;
    if (msg != "") {
        document.getElementById("msg").value = null;
        socket.emit('inputMsg', msg);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    socket = io();
    socket.on('connect', () => {
        socket.send({"info" : "connected"});
        console.log(key, pid);
    });

    socket.on('message', data => {
        const s = document.createElement('strong');
        s.innerHTML = data + "<br>" + "<br>";
        document.querySelector('#messages').append(s);
    });

    socket.on('chatMsg', data => {
        const p = document.createElement('p');
        p.innerHTML = "<strong>" + data[0] + " : " + "</strong>" + data[1];
        document.querySelector('#messages').append(p);
    });

    document.getElementById("msg").addEventListener("keypress", sendMsgEnter);
    document.getElementById("send-button").addEventListener("click", sendMsg);

    var readyButtons = document.getElementsByName("btn-Ready");
    var pb; //player-button (for ready)
    var pcs; //player-cards (for playing a move)
    readyButtons.forEach(item => {
        if (item.value !== pid) {
            item.disabled = true;
        }
        else{
            pb = item;
        }
    })

    pb.addEventListener("click", ()=>{
        console.log(pb.value +" is ready");
        socket.emit('player_ready', {"pid" : pb.value, "secret_key": key});        
    })

    
    socket.on('player_ready', data => {
        console.log(data + " is ready ack by server!");
        readyButtons.forEach(item => {
            if (item.value === data) {
                item.disabled = true;
                item.classList.add('btn-success');
                item.innerHTML = "You are Ready!";
                item.classList.remove('btn-warning');
            }
        })
    })

    socket.on('game_action', data => {
        if(data["action"] === "cards_served") {
            console.log("Let's fetch ours");
            socket.emit('request_cards', {"pid" : pb.value, "secret_key": key});
        }
        else if(data["action"] === "cards_fetch") {
            cards = data["cards"];
            document.querySelector("#game-cards-" + pb.value).innerHTML = "";
            for(var i=0; i<=12; i++) {
                const btn = document.createElement('button');
                btn.id = i;
                btn.value = cards[i][0] + "_" + cards[i][1];
                btn.name = pb.value + "-card";
                btn.innerHTML = cards[i][0][0] + "_" + cards[i][1];
                document.querySelector("#game-cards-" + pb.value).append(btn);
                
            }
            pcs = document.getElementsByName(pb.value + "-card");
            console.log(pcs);

            pcs.forEach(item => {
                item.addEventListener('click', () => {
                    socket.emit('player_move', item.value);
                });
            })
        }
        else if(data["action"] === "remove") {
            console.log(data);
            pcs.forEach(item => {
                if(item.value === data["card"][0] +"_" + data["card"][1]) {
                    item.disabled = true;
                }
            })
        }
        else if(data["action"] === "update_table") {
            console.log(data);
            const btn = document.createElement('button');
            btn.id = data["player"];
            btn.value = data["card"][0] + "_" + data["card"][1];
            btn.name = pb.value + "-card";
            btn.innerHTML = data["card"][0][0] + "_" + data["card"][1] + "<strong>("+data["player"]+")</strong>";
            document.querySelector("#game-cards-server").append(btn);
        }
        else if(data["action"] === "clear_table") {
            console.log(data);
            var gcs = document.querySelector("#game-cards-server");
            for(var i=0; i<4; i++) {
                gcs.removeChild(gcs.firstElementChild);
                console.log("removing child", gcs.childNodes);
            }
        }
        else if(data["action"] === "show_score") {
            console.log(data);
            document.querySelector("#game-info").innerHTML = "Game Over!!</br>";
        }
    })
});
