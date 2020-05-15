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
    id, pid = session['user_id']
    getPlayerById(int(pid), players).status = 'offline'
    text = 'Client {} disconnected. Player {} is offline'.format(id, pid)
    chat_history.append(["", text])
    print(text)
    socketio.send(text, broadcast=True)  #should be True ByDefault
    
    # forget any user_id
    session.clear()
    # redirect user to login form
    return redirect(url_for("home"))



# entry page with Login
@app.route('/')
@app.route('/home', methods = ["GET", "POST"])
def home():
    if request.method == "POST":
        name = request.form.get('name')
        pid = request.form.get('submit-btn')
        session['user_id'] = (name, pid)
        return redirect(url_for('game'))
    
    if 'user_id' in session:
        #test_disconnect()
        return redirect(url_for('home'))
    
    offline_players = []
    for p in players:
        if p.status == 'offline':
            offline_players.append(p)
    return render_template('home.html', offline_players=offline_players)

# logout user
@app.route("/logout")
def logout():
    """Log user out."""
    print("disconnected from session")
    #disconnect_user()
    """
    for key in list(session):
        if key != '_permanent':
            session.pop(key)
    session['this'] = 'will be added'
    """

# main game page
@app.route('/game')
@login_required
def game():
    id, pid = session['user_id']
    key = getPlayerById(int(pid), players).secret_key
    return render_template('game.html', chat_history=chat_history, pid='p'+pid, secret_key=key)


# socket -msg
@socketio.on('message')
def message(data):
    print(data)
        
# socket -chat
@socketio.on('inputMsg')
def inputMsg(data):

    id = session['user_id'][0]
    print(data)
    chat_history.append([id, data])
    emit('chatMsg', [id, data], broadcast=True)

# socket -connect event
@socketio.on('connect')
def connect():
    if 'user_id' not in session:
        #raise ConnectionRefusedError('unauthorized!')
        
        return redirect(url_for('home'))
    else:
        id, pid = session['user_id']
        data = "=> {} is connected as Player {} <=".format(id, pid)
        chat_history.append(["", data])
        getPlayerById(int(pid), players).status = 'online'
        send(data, broadcast=True)

""" 
# socket -disconnect event
@socketio.on('disconnect')
def test_disconnect():
    print("disconnected from socket")
    disconnect_user()
"""
# socket -game events

# socket -player_ready
@socketio.on('player_ready')
def player_ready(p):
    id, pid = session['user_id']
    key = getPlayerById(int(pid), players).secret_key

    if pid == p['pid'][1:] and key == p['secret_key']:

        print(p['pid'], "is ready")
        
        if player_not_ready[int(pid)] != 0:
            player_not_ready[int(pid)] = 0
            emit('message', p['pid'] + " is ready!", broadcast=True)
        else:
            emit('message', p['pid'] + " was ready!", broadcast=True)
        
        for i in range(len(player_not_ready)):
            if player_not_ready[i] == 0:
                emit('player_ready', 'p'+str(i), broadcast=True)
        
        if sum(player_not_ready) == 0:
            print("all ready")
            emit('message', "all players are ready", broadcast=True)
            emit('message', "Starting game", broadcast=True)
            
            G.serveCards()
            emit('game_action', {"action" : "cards_served"}, broadcast=True)
    else:
        print("Incorrect Player or secret key!")

# socket -req_cards
@socketio.on('request_cards')
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
def player_move(data):
    id, pid = session['user_id']
    suit, cardLetter = data.split("_")
    print(pid, suit, cardLetter)
    # if valid move
    # emit move accepted, emit move, emit card remove, change nextMove and wait
    # else emit incorrect move
    if G.play(pid, suit, cardLetter):
        emit('game_action', {"info" : "move accepted", "action" : "remove", "card" : [suit, cardLetter]})
        emit('game_action', {"action" : "update_table", "card" : [suit, cardLetter], "player" : pid}, broadcast=True)
        print(G.players[int(pid)].cards)
    else:
        emit('message', "move rejected")
    
    res = G.calculate()
    if res["winner"] != None:
        emit('message', "Player " + str(res["next_move"].id) + " wins!", broadcast=True)
        socketio.sleep(2)
        emit('game_action', {"action" : "clear_table", "winner" : res["winner"]}, broadcast=True)
        if res["game_over"]:
            emit('game_action', {"action" : "show_score", "score": res["scoreboard"]}, broadcast=True)
            G.serveCards()
            socketio.sleep(5)
            emit('game_action', {"action" : "cards_served"}, broadcast=True)
            
    #check if all_players_moveDone players
    #       calculate winner, (if game over) : show_winner else change nextMove and wait
    
    #       clearround cards (clear table on server)
    #       newround ->(does this auto)     # clear playerMoveDone 

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", debug=True)