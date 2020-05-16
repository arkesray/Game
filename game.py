import random

class Card():
    def __init__(self, value, letter, name, suit):
        self.value = value
        self.letter = letter
        self.name = name
        self.suit = suit
    
    def __repr__(self):
        return " <{}> {} of {} <{}> ".format(self.letter, self.name, self.suit, self.letter)

class Player():
    def __init__(self, id, key):
        self.id = id
        self.cards = []
        self.myTurn = False
        self.score = 0
        self.status = 'offline'
        self.secret_key = key
    
    def __repr__(self):
        return "Player id {} is {}".format(self.id, self.status)

    def play(self):
        suit, CardLetter = input("Suit Card_Letter : ").split()
        c = getCardBySuitLetter(suit, CardLetter)
        while c not in self.cards:
            suit, CardLetter = input("Suit Card_Letter : ").split()
            c = getCardBySuitLetter(suit, CardLetter)
        self.cards.remove(c)
        return c

l = ['A','2','3','4','5','6','7','8','9','10','J','Q','K']
v = [14, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
n = ['ace','two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'jack', 'queen', 'king']

cards = []
for suit in ['spade', 'heart', 'club', 'diamond']:
    for i in range(13):
        cards.append(Card(v[i], l[i], n[i], suit))
#players = [Player(0), Player(1), Player(2), Player(3)]

def getPlayerById(id, players):
    for p in players:
        if p.id == id:
            return p
    return None

def getCardBySuitLetter(suit, letter, cards):
    letter = letter.upper()
    suit = suit.lower()
    if suit == 'spade':
        offset = -1
    elif suit == 'heart':
        offset = 12
    elif suit == 'club':
        offset = 25
    else:
        offset = 38

    if letter == 'A':
        index = 1
    elif letter == 'J':
        index = 11
    elif letter == 'Q':
        index = 12
    elif letter == 'K':
        index = 13
    else:
        try:
            index = int(letter)
        except:
            return None
    return cards[offset+index]


class Game():
    def __init__(self, players, cards):
        self.name = "Card Game"
        self.players = players
        self.cards = cards
        self.nextMove = self.players[0]
        self.playerMovesDone = [False, False, False, False]
        self.roundCards = []
        self.roundNumber = 0
        self.roundScore = {}

    def serveCards(self):
        self.roundNumber = 0
        randomlist = random.sample(range(52), 52)
        j = 0
        for i in range(len(self.players)):
            self.players[i].cards.clear()
            while j < (i+1)*13:
                self.players[i].cards.append(self.cards[randomlist[j]])
                j += 1
            #print(self.players[i].cards, len(self.players[i].cards))
        self.newRound()
        
    
    def newRound(self):
        self.playerMovesDone = [False, False, False, False]
        self.roundNumber += 1

    def isGameOver(self):
        if self.roundNumber >= 13:
            return True
        return False

    def calculate(self):
        allmoveDone = True
        for pmd in self.playerMovesDone:
            if pmd == False:
                allmoveDone = False
                break
        r = {"winner" : None, "next_move" : None, "game_over" : False, "scoreboard" : None}
        if allmoveDone:
            if len(self.roundCards) != 4:
                print("****---Game Error---****** : please restart")  
            winner = max(self.roundCards, key = lambda x: x[0].value)
            self.roundScore[self.roundNumber] = [self.roundCards[:], winner[1]]
            self.nextMove = getPlayerById(int(winner[1]), self.players)
            self.roundCards.clear()
            r["winner"] = winner[1]
            r["next_move"] = self.nextMove
            print(winner, "won")

            if self.isGameOver():
                r["game_over"] = True
                r["scoreboard"] = self.prepare_scoreboard()
                print("Game Over!", "No Scoreboard")
            else:
                self.newRound()
        return r

    def prepare_scoreboard(self):
        if len(self.roundScore.keys()) != 13:
            print("Something went Wrong")
        else:
            w_p = [[],[],[],[]]
            for k in self.roundScore:
                round_cards = []
                for card_player in self.roundScore[k][0]:
                    round_cards.append([card_player[0].suit, card_player[0].letter, "p"+str(card_player[1])])
                w_p[int(self.roundScore[k][1])].append([int(k), round_cards])
                getPlayerById(int(self.roundScore[k][1]), self.players).score += 1
            return w_p


    def play(self, pid, suit, cardLetter):
        pid = int(pid)
        if self.nextMove.id == pid:
            inputCard = getCardBySuitLetter(suit, cardLetter, self.cards)
            player = getPlayerById(pid, self.players)
            if inputCard in player.cards:
                print("Move accepted")
                self.playerMovesDone[pid] = True
                player.cards.remove(inputCard)
                self.roundCards.append([inputCard,pid])
                pid = (pid + 1) % 4
                self.nextMove = getPlayerById(pid, self.players)
                return True
            else:
                print("Error- Card not found in player")
        else:
            print("Error- Incorrecct Player playing")
        return False

"""
g = Game(players, cards)    
g.serveCards()
while True:

    g.play()
    #print(len(g.players[0].cards), g.players[0].cards)
    g.calculate()
"""