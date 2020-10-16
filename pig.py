import sys, random, argparse, time
from queue import Queue

class Players(object):
    #Game players track
    def __init__(self, players):
        self._players = players
        self._current_player = players.get()

    def get_current_player(self):
        return self._current_player

    def get_next_player(self):
        self._players.put(self._current_player)
        self._current_player = self._players.get()
        return self._current_player

    def get_players(self):
        players_list = list(self._players.queue)
        players_list.append(self._current_player)
        return players_list


class Player(object):
    #Players score, name and rolls
    def __init__(self, name):
        self._name = name.strip()
        self._total_score = 0
        self._current_score = 0
        self._total_rolls = 0
        self._last_roll = 0

    def get_name(self):
        return self._name

    def get_total_score(self):
        return self._total_score

    def get_current_score(self):
        return self._current_score

    def get_total_rolls(self):
        return self._total_rolls

    def get_last_roll(self):
        return self._last_roll

    def update_total_rolls(self):
        self._total_rolls += 1

    def update_turn_score(self, score):
        self._current_score += score

    def update_last_roll(self, roll):
        self._last_roll = roll

    def reset_turn_stats(self):
        self._current_score = 0

    def commit_score(self):
        self._total_score += self._current_score

    def request_action(self):
        return input("Please enter 'r' to roll or 'h' to hold. Your Choice? ")


class ComputerPlayer(Player):
    def request_action(self):
        action = "r" if self._current_score < min(25, (100 - (self._total_score + self._current_score))) else "h"
        return action


class PlayerFactory:
    def get_player(self, player_name, player_type):
        if player_type == "human":
            return Player(player_name)
        if player_type == "computer":
            return ComputerPlayer(player_name)


class Die(object):
    #The Die
    def __init__(self):
        random.seed(0)

    def roll(self):
        return random.randint(1, 6)

class Game(object):
    #Game itself
    def __init__(self, players):
        self._players = Players(players)
        self._die = Die()
        self._active_turn = True
        self._end_game = False

    def start(self):
        self._turn()

    def _accounce_winner(self):
        winner = sorted(((player.get_name(), player.get_last_roll(), player.get_total_score())
                       for player in self._players.get_players()), key=lambda player: (player[2]), reverse=True)[0]

        print("\n{} Won the Game! Rolled a {}. Total score is {}".format(winner[0], winner[1], winner[2]))

    def _game_over(self):
        ranking = ((player.get_name(), player.get_total_score(), player.get_total_rolls())
                       for player in self._players.get_players())

        print("\nPig Results:\n")
        for player in sorted(ranking, key=lambda player: (player[1]),reverse=True):
            print("{} Scored {} points, rolled {} times".format(player[0], player[1], player[2]))

    def _play(self, player):
        action = player.request_action()
        if action == "r":
            roll = self._die.roll()
            player.update_total_rolls()
            player.update_last_roll(roll)
            if roll == 1:
                player.reset_turn_stats()
                player.commit_score()
                print("{} rolled a {}, lost all points of the turn. Turn score is 0. Total score: {}.".format(
                        player.get_name(), roll, player.get_total_score()))
                self._active_turn = False
            else:
                player.update_turn_score(roll)
                if (player.get_current_score() + player.get_total_score()) >= 100:
                    player.commit_score()
                    player.reset_turn_stats()
                    self._end_game, self._active_turn = True, False
                else:
                    print("{} rolled a {}. Turn score is {}. Total score is {}".format(player.get_name(),
                            roll,
                            player.get_current_score(),
                            player.get_current_score() + player.get_total_score() ) )
        elif action == "h":
            player.commit_score()
            print("{}, you held. Your score for this turn is {}. Your total score is {}.".format(
                player.get_name(), player.get_current_score(), player.get_total_score()))
            player.reset_turn_stats()
            self._active_turn = False
        else:
            print("Invalid action.")

    def _turn(self, next_player=False):
        player = self._players.get_current_player(
        ) if not next_player else self._players.get_next_player()

        self._active_turn = True

        print("\n{}'s turn. Current score is {}".format(player.get_name(), player.get_total_score()))

        while self._active_turn and not self._end_game:
            self._play(player)

        if not self._end_game:
            self._turn(True)
        else:
            self._accounce_winner()
            self._game_over()


class TimedGame(Game):
    def start(self):
        self._end_time = time.time() + 60
        self._turn()

    def _accounce_winner(self):

        if self._end_time < time.time():
            winner = sorted(((player.get_name(), player.get_last_roll(), player.get_total_score())
                       for player in self._players.get_players()),key=lambda player: (player[2]),reverse=True)[0]

            print("\n{} Won! with the highest score: {}".format(winner[0], winner[2]))
        else:
            super()._accounce_winner()

    def _play(self, player, time_left):
        print("Time left for the game: {} seconds".format(time_left))
        super()._play(player)

    def _turn(self, next_player=False):
        player = self._players.get_current_player() if not next_player else self._players.get_next_player()

        self._active_turn = True

        print("\n{}'s turn. Current score is {}".format(player.get_name(), player.get_total_score()))

        while self._active_turn and not self._end_game and time.time() < self._end_time:
            self._play(player, round(self._end_time - time.time(), 0))

        if time.time() >= self._end_time:
            self._end_game = True
            self._active_turn = False

        if not self._end_game:
            self._turn(True)
        else:
            self._accounce_winner()
            self._game_over()

class TimedGameProxy(Game):
    def __init__(self, players):
        self._players = players
        self._game = None

    def start(self, timed):
        if timed:
            self._game = TimedGame(self._players)
        else:
            self._game = Game(self._players)
       
        self._game.start()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--player1', help='Player 1 type, computer or human.',type=str)
    parser.add_argument('--player2', help='Player 2 type, computer or human.',type=str )
    parser.add_argument('--timed', action='store_true', help='Player with most points after one minute, wins!')
    args = parser.parse_args()

    if not args.player1 and not args.player2:
        print("Required arguments: --player1 and --player2. Valid types: computer or human.")
        sys.exit()

    if not args.player1.lower() == "computer" and not args.player1.lower() == "human":
        print("Not a valid type for player1. Valid types: computer or human.")
        sys.exit()

    if not args.player2.lower() == "computer" and not args.player2.lower() == "human":
        print("Not a valid type for player2. Valid types: computer or human.")
        sys.exit()

    players = Queue()

    player1_name = "Computer [Player 1]" if args.player1.lower() == "computer" else input("Player 1's name? ")

    player2_name = "Computer [Player 2]" if args.player2.lower() == "computer" else input("Player 2's name? ")

    players.put(PlayerFactory().get_player(player1_name, args.player1.lower()))
    players.put(PlayerFactory().get_player(player2_name, args.player2.lower()))

    TimedGameProxy(players).start(args.timed)

    sys.exit()


if __name__ == '__main__':
    main()
