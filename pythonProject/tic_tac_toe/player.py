from dataclasses import dataclass


@dataclass(frozen=True)
class Player:
    name = str
    sigh = str

if __name__ == "__main__":
    player1 = Player
    player1.name = "segun"
    print(player1.name)