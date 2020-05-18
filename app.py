from flask import Flask, render_template, request, url_for, session, redirect
from flask_session import Session
from flask_socketio import SocketIO, send, emit
from functools import wraps

from game import Player, getPlayerById, cards, Game

app = Flask(__name__)
app.config.from_object('config')
Session(app)
socketio = SocketIO(app, manage_session=False)

chat_history = []
Reports = []
players = [Player(0, "key1"), Player(1, "keeq"), Player(2, "keqw"), Player(3, "kee")]
player_not_ready = [1,1,1,1]

G = Game(players, cards[:])

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/home")
        return f(*args, **kwargs)
    return decorated_function

def disconnect_user():
    global player_not_ready
    try:
        id, pid = session['user_id']
        getPlayerById(int(pid), players).status = 'offline'
        player_not_ready[int(pid)] = 1
        socketio.emit('player_not_ready', 'p'+pid, broadcast=True)
        text = 'Client {} disconnected. Player {} is offline'.format(id, pid)
        socketio.send(text, broadcast=True)  #should be True ByDefault
        chat_history.append(["", text])
        
        #if every Player is offline reset the game 
        all_offline = True
        for i in range(4):
            if getPlayerById(i, players).status == "online":
                all_offline = False
                break
        if all_offline:
            reset("")
    except:
        pass

    # forget any user_id
    session.clear()




# entry page with Login
@app.route('/')
@app.route('/home', methods = ["GET", "POST"])
def home():
    if request.method == "POST":
        name = request.form.get('name')
        pid = request.form.get('submit-btn')
        if pid == "50":
            Reports.append(request.form.get('issueBox')+" by " + name)
            return redirect(url_for('home'))
        session['user_id'] = (name, pid)
        return redirect(url_for('game'))
    
    if 'user_id' in session:
        disconnect_user()
        return redirect(url_for('home'))
    
    return render_template('home.html', Reports = Reports)

# logout user
@app.route("/logout")
def logout():
    """Log user out."""
    print("disconnected from session")
    disconnect_user()
    """
    for key in list(session):
        if key != '_permanent':
            session.pop(key)
    session['this'] = 'will be added'
    """
    return redirect(url_for("home"))

# main game page
@app.route('/game', methods = ["GET", "POST"])
@login_required
def game():
    if request.method == "POST":
        return redirect(url_for('logout'))
        
    id, pid = session['user_id']
    key = getPlayerById(int(pid), players).secret_key
    return render_template('game.html', chat_history=chat_history, pid='p'+pid, secret_key=key)


# socket -HomePage
@socketio.on('connect', namespace='/home')
def home_connect():
    print("user joined home page")

@socketio.on('update', namespace='/home')
def home_update(data):
    players_info = []
    for p in players:
        players_info.append(p.status)
    emit('update', players_info, broadcast=True)

@socketio.on('disconnect', namespace='/home')
def home_disconnect():
    print("user left home page")

# socket -msg
@socketio.on('message')
def message(data):
    print(data)
        
# socket -chat
@socketio.on('inputMsg')
@login_required
def inputMsg(data):

    id = session['user_id'][0]
    print(data)
    chat_history.append([id, data])
    emit('chatMsg', [id, data], broadcast=True)

# socket -connect event
@socketio.on('connect')
@login_required
def connect():

    id, pid = session['user_id']
    data = "=> {} is connected as Player {} <=".format(id, pid)
    chat_history.append(["", data])
    getPlayerById(int(pid), players).status = 'online'
    emit('request_update', "", namespace='/home', broadcast=True)
    send(data, broadcast=True)
    for i in range(len(player_not_ready)):
        if player_not_ready[i] == 0:
            emit('player_ready', 'p'+str(i), broadcast=True)


# socket -disconnect event
@socketio.on('disconnect')
def test_disconnect():
    print("disconnected from socket")
    disconnect_user()

# socket -game events

# socket -game reset
@socketio.on('reset')
@login_required
def reset(data):
    global G
    global players
    global player_not_ready
    
    for i in range(4):
        emit('player_not_ready', 'p'+str(i), broadcast=True)

    emit('game_action',{"action" : "reload"}, broadcast=True)
    socketio.sleep(1)
    players = [Player(0, "key1"), Player(1, "keeq"), Player(2, "keqw"), Player(3, "kee")]
    G = Game(players, cards[:])
    player_not_ready = [1,1,1,1]


# socket -player_ready
@socketio.on('player_ready')
@login_required
def player_ready(p):
    global player_not_ready
    global G
    global players
    id, pid = session['user_id']
    key = getPlayerById(int(pid), players).secret_key
    if pid == p['pid'][1:] and key == p['secret_key']:
        print(p['pid'], "is ready")
        if player_not_ready[int(pid)] != 0:
            player_not_ready[int(pid)] = 0
            emit('message', p['pid'] + " is ready!", broadcast=True)
        else:
            emit('message', p['pid'] + " was ready!", broadcast=True)
        
        emit('player_ready', p['pid'], broadcast=True)
        if sum(player_not_ready) == 0:
            print("all ready")
            emit('message', "all players are ready", broadcast=True)
            emit('message', "Starting game", broadcast=True)
            G = Game(players, cards[:])
            G.serveCards()
            emit('game_action', {"action" : "cards_served"}, broadcast=True)
    else:
        print("Incorrect Player or secret key!")

# socket -req_cards
@socketio.on('request_cards')
@login_required
def send_cards(p):
    
    id, pid = session['user_id']
    player = getPlayerById(int(pid), players)
    key = player.secret_key
    d = { str(i) : [player.cards[i].suit, player.cards[i].letter] for i in range(len(player.cards)) }

    if pid == p['pid'][1:] and key == p['secret_key']:
        print("received cards request from", id, pid)
        emit('game_action', {"action" : "cards_fetch", "cards" : d})
    

# socket -player_move
@socketio.on('player_move')
@login_required
def player_move(data):
    global player_not_ready
    id, pid = session['user_id']
    suit, cardLetter = data.split("_")
    print(pid, suit, cardLetter)
    # if valid move
    # emit move accepted, emit move, emit card remove, change nextMove and wait
    # else emit incorrect move
    if G.play(pid, suit, cardLetter):
        emit('game_action', {"info" : "move accepted", "action" : "remove", "card" : [suit, cardLetter]})
        emit('game_action', {"action" : "update_table", "card" : [suit, cardLetter], "player" : pid}, broadcast=True)
    else:
        emit('message', "move rejected")
    
    res = G.calculate()
    if res["winner"] != None:
        emit('message', "Player " + str(res["next_move"].id) + " wins!", broadcast=True)
        socketio.sleep(2)
        emit('game_action', {"action" : "clear_table", "winner" : res["winner"]}, broadcast=True)
        if res["game_over"]:
            player_scores = [G.players[i].score for i in range(4)]
            emit('game_action', {"action" : "show_score", "score": res["scoreboard"], "player_scores" : player_scores}, broadcast=True)
            player_not_ready = [1,1,1,1]

 
if __name__ == '__main__':
    #socketio.run(app, host="0.0.0.0", debug=True)
    app.run()