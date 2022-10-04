from data_backend import load, can_load
import random
from discord import Member
from message_processing import client
#from program_base import *


class CahPlayer:
    def __init__(self, discord_implement: Member, p_game, id: int, p_rando: bool = False):
        self.name = "Rando Calrissian" if p_rando else discord_implement.display_name
        self.game = p_game
        self.id = id
        self._points = 0
        self.cards = []
        self.discord_implement: Member = discord_implement
        self.isrando = p_rando

    def get_cards(self):
        return "\n".join(["{} - [{}]".format(i, c) for i, c in enumerate(self.cards)])

    def take(self, num: int):
        for c in self.game.take(num):
            self.cards.append(c)

    @property
    def points(self):
        return self._points

    @points.setter
    def points(self, value):
        self._points = value

    @classmethod
    def rando(cls, game, id):
        return CahPlayer(client.user, game, id, True)

    def __repr__(self):
        return "<Player {n}>".format(n=self.name)


class CahGame:
    def __init__(self):
        self.whites_tot: list[str] = []
        self.blacks_tot: list[str] = []
        self.packs: list[str] = []
        self.white_pass: list[str] = []
        self.black_card: list[str] = []
        self.white_poss: list[str] = []
        self.black_poss: list[str] = []

        self.player_list: list[CahPlayer] = []
        self.game_stat: int = 0
        # 0 is hosting
        # 1 is playing
        # 2 is choosing
        self.table: dict[CahPlayer, list[str]] = {}
        self.black_card: str = "FRNT __(1)__ BCK"
        self.cards_needed: int = 0

        self.tsar = None
        self.closed = True

    def open(self, rando: bool = False):
        self.__init__()
        self.player_list = [CahPlayer.rando(self, 0)] if rando else []
        self.closed = True

    def close(self):
        self.closed = True

    def add_libs(self, p_library_paths: list[str]):
        outp = []
        for path in p_library_paths:
            act_path = "cah_libraries/" + path
            if can_load(act_path):
                lib = load(act_path)
                outp.append(lib["__meta__"])
                self.whites_tot += lib.get("white", [])
                self.blacks_tot += lib.get("black", [])
                self.packs.append(path)
                print("Added library: " + path)
            else:
                print("No such library: " + path)

        self.white_poss = self.whites_tot[:]
        self.black_poss = self.blacks_tot[:]
        random.shuffle(self.white_poss)
        random.shuffle(self.black_poss)

        return outp

    def join(self, p_player: Member):
        """
        Called, when a player joins
        :param p_player: The discord member
        """
        if self.game_stat != 0:
            return
        if any([player.name == p_player.display_name for player in self.player_list]):
            return
        player = CahPlayer(p_player, self, len(self.player_list))
        if self.tsar is None:
            self.tsar = player
        self.player_list.append(player)
        return player

    def leave(self, p_player: Member):
        if not any([player.name == p_player.display_name for player in self.player_list]):
            return
        self.player_list = list(filter(lambda x: x.name != p_player.display_name, self.player_list))

    def lay_card(self, player_name: str, cards: list):
        """
        Player lays a white card
        :param player_name: The name of the player
        :param cards: The white cards
        """
        if len([p.name for p in self.player_list]) == 0:
            return "Player {} does not exist".format(player_name)
        player = self.get_player(player_name)
        self.table[player] = [player.cards[c] for c in cards]
        for c in self.table[player]:
            player.cards.remove(c)
        player.take(len(cards))
        return "Player {n} played".format(n=player_name)

    def take(self, number):
        return [self._white_card for _ in range(number)]

    def show(self):
        """
        Shows all the possible cards
        """
        res = ""
        j = 0
        for i, pl in enumerate(self.player_list):
            if pl != self.tsar:
                card_string = " {j}: -> [{card}]\n--------------------------\n\n"\
                    .format(j=j, card=fill_black(self.black_card, self.table[pl]))
                res += card_string
                j += 1
        self.game_stat = 2
        return res

    def get_laid_out(self):
        res = []
        for i, pl in enumerate(self.player_list):
            if pl != self.tsar:
                card_string = f" {i}: -> [{fill_black(self.black_card, self.table[pl])}]"
                res.append(card_string)
                i += 1
        return res

    def choose(self, player: int):
        """
        Chooses a player as best player
        :param player: The Player
        :returns: Text-output
        """
        active_player_list = self.player_list[:]
        active_player_list.remove(self.tsar)
        active_player_list[player].points += 1
        if not active_player_list[player].isrando:
            self.tsar = active_player_list[player]
        self.game_stat = 1
        return "You chose {}\n\n".format(active_player_list[player].discord_implement.mention) + self._new_round()

    def close_joining(self):
        """
        After this, the join-phase is over, and the game begins
        :returns text-output
        """
        for player in self.player_list:
            player.take(10)
        self.game_stat = 1
        return self._new_round()

    def get_player(self, name: str):
        return list(filter(lambda x: x.name == name, self.player_list))[0]

    def _new_round(self):
        """
        Starts a new round (new card)
        """
        self.black_card = self._black_card
        if "__(1)__" in self.black_card:
            self.cards_needed = 1
        if "__(2)__" in self.black_card:
            self.cards_needed = 2
        if "__(3)__" in self.black_card:
            self.cards_needed = 3
        self.table = {}

        for pl in self.player_list:
            if pl.isrando:
                play_list = []
                playing_possibilities = list(range(0, 10))
                for i in range(self.cards_needed):
                    card = random.choice(playing_possibilities)
                    play_list.append(card)
                    playing_possibilities.remove(card)

                self.lay_card("Rando Calrissian", play_list)

        random.shuffle(self.player_list)
        return "the new card is\n[{}]".format(self.black_card)

    def stats(self):
        return [(p.name, p.points) for p in self.player_list]

    def random(self):
        return fill_black(random.choice(self.blacks_tot), [random.choice(self.whites_tot) for _ in range(3)])

    @property
    def _white_card(self):
        if len(self.white_poss) == 0:
            self.white_poss = self.whites_tot[:]
            random.shuffle(self.white_poss)
        return self.white_poss.pop()

    @property
    def _black_card(self):
        if len(self.black_poss) == 0:
            self.black_poss = self.blacks_tot[:]
            random.shuffle(self.black_poss)
        return self.black_poss.pop()

    @property
    def player_num(self):
        """
        :return: The number of the players
        """
        return len(self.player_list)

    @property
    def all_played(self):
        return len(self.table) == self.player_num - 1


def fill_black(card, white_cards: list):
    """
    :param card: The black card
    :param white_cards: A list of 1 - 3 card white cards
    :returns The text of the black card filled in with the whites
   """
    res = card
    if "__(1)__" in res:
        res = res.replace("__(1)__", "**{}**".format(white_cards[0]))
    elif "__(1)___" in res:
        res = res.replace("__(1)___", "**{}**".format(white_cards[0]))
    if "__(2)__" in res:
        res = res.replace("__(2)__", "**{}**".format(white_cards[1]))
    elif "__(2)___" in res:
        res = res.replace("__(2)___", "**{}**".format(white_cards[1]))
    if "__(3)__" in res:
        res = res.replace("__(3)__", "**{}**".format(white_cards[2]))
    elif "__(3)___" in res:
        res = res.replace("__(3)___", "**{}**".format(white_cards[2]))
    return res
