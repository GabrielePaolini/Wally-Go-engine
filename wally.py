###################################
#
#   WALLY by Jonathan K. Millen
#     (reconstruction by CMK)
#
###################################

from time import sleep
from random import randrange, choice
from math import ceil, sqrt

###################################
#
#          Piece encoding
#
###################################
#
# 0000 => 0    empty sqare
# 0001 => 1    black stone
# 0010 => 2    white stone
# 0100 => 4    stone marker
# 0111 => 7    offboard square
# 1000 => 8    liberty marker
#
# 0101 => 5    black stone marked
# 0110 => 6    white stone marked
#
###################################

# 9x9 GO ban as saved on the GBA
"""
board_9x9 = [
    7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7,
    7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7,
    7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7,
    7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7,
    7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7,
    7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7,
    7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7,
    7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7,
    7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7,
    7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7,
    7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7
]

# Boards LUT
BOARDS = {
    '9': board_9x9,
    '13': board_13x13,
    '19': board_19x19,
}
"""


class Board:
    def __init__(self, board_size, margin=2):
        # Stones
        self.EMPTY = 0
        self.BLACK = 1
        self.WHITE = 2
        self.MARKER = 4
        self.OFFBOARD = 7
        self.LIBERTY = 8
        # ASCII representation of stones
        self.pieces = '.#o  bw +'

        # Board size data
        self.BOARD_SIZE = board_size
        self.MARGIN = margin
        self.BOARD_RANGE = board_size + self.MARGIN
        self.board = self.create()

        # Count routine variables
        self.best_liberties = board_size * board_size
        self.best_move = None
        self.white_atari_move = []
        self.white_atari_liberties = []

    def create(self):
        # Create the top and bottom rows (full of 7s)
        top_bottom_row = [self.OFFBOARD] * self.BOARD_RANGE
        # Create the middle rows (7s on the sides, 0s in the middle)
        middle_row = [self.OFFBOARD] + [self.EMPTY] * \
            self.BOARD_SIZE + [self.OFFBOARD]
        # Create the full board
        board = [top_bottom_row] + \
            [middle_row for _ in range(self.BOARD_SIZE)] + [top_bottom_row]
        # Flatten the board to a single list
        flat_board = [item for sublist in board for item in sublist]
        return flat_board

    # RENDER SQUARE BOARD ON CONSOLE
    def render(self):
        # File markers
        files = [chr(ascii_code)
                     for ascii_code in range(97, 97 + self.BOARD_SIZE)]

        # first row of column coords
        print('\n' + '    ' + ' '.join(files), end='')
        for row in range(self.BOARD_RANGE):
            for col in range(self.BOARD_RANGE):
                if row > 0 and row < self.BOARD_RANGE - 1:
                    if col == 0:
                        cur_row = self.BOARD_RANGE - 1 - row
                        print('' + str(cur_row) if cur_row >=
                              10 else ' ' + str(cur_row), end='')
                    elif col == self.BOARD_RANGE - 1:
                        cur_row = self.BOARD_RANGE - 1 - row
                        print(' ' + str(cur_row), end='')

                square = row * self.BOARD_RANGE + col
                stone = self.board[square]
                print(self.pieces[stone] + ' ', end='')
            print()
        print('    ' + ' '.join(files) + '\n')  # last row of column coords

    def reset(self):
        self.board = self.create()
        self.best_liberties = self.BOARD_SIZE * self.BOARD_SIZE
        self.best_move = None

    def place_stone(self, square, color):
        self.board[square] = color

    def remove_stone(self, square):
        self.board[square] &= 8

    # count liberties, save stone group coords (COUNT sub on byte magazine 1981)
    def count(self, square, color):
        group = set()
        liberties = set()
        piece = self.board[square]
        if piece != self.OFFBOARD:
            # If there's a stone at square (i.e. square is not empty (0)
            # AND has the same color as input AND is not marked)
            if (piece & 3) and (piece & color) and (piece & self.MARKER) == 0:
                # save stone's coordinate
                #self.blocks.append(square)
                group.add(square)
                # mark the stone
                self.board[square] |= self.MARKER
                # look for neighbours recursively
                for delta in [-self.BOARD_RANGE, 1, self.BOARD_RANGE, -1]:
                    next_group, next_liberties = self.count(
                        square + delta, color)
                    group = group.union(next_group)
                    liberties = liberties.union(next_liberties)
            # if the square is empty
            elif piece == self.EMPTY:
                # mark liberty
                self.board[square] |= self.LIBERTY
                # save liberties
                #self.liberties.append(square)
                liberties.add(square)
        return group, liberties

    def restore(self):
        # For every square in the board
        for square in range(self.BOARD_RANGE * self.BOARD_RANGE):
            # restore piece if the square is on board
            if self.board[square] != self.OFFBOARD:
                # Unmark the stone
                self.board[square] &= 3

    def reset_best_attr(self):
        self.best_move = None
        self.best_liberties = self.BOARD_SIZE * self.BOARD_SIZE

    def clear_group(self, group):
        for captured in group:
            self.board[captured] = self.EMPTY


def check_input(input_string, board_size):
    outstate = 0
    # IF INPUT IS COORD, CHECK IF IT'S VALID
    if len(input_string) == 0:
        msg = "Input not provided."
    else:
        last_char = chr(97 + board_size)
        column = input_string[0].lower()
        msg = "Unknown error."
        if last_char < 'a' or last_char > 'z':
            msg = "Invalid last character. Must be between 'a' and 'z'."
        elif column < 'a' or column > last_char:
            msg = "Invalid column input, it must be between 'a' and '{}'".format(
                last_char)
        else:
            if input_string[1:].isdigit():
                row = int(input_string[1:])
                if row < 1 or row > board_size:
                    msg = "Invalid row, it must be between 1 and {}".format(
                        board_size)
                else:
                    outstate = 1  # Tutto ok
            else:
                msg = "Invalid row."
    if not outstate:
        print(msg)
    return outstate


def move2square(move, board_range):
    return (1 + int(move[1:])) * -board_range + ord(move[0]) % 97 + 1


def square2move(square, board_range):
    col = chr(97 + (square % board_range - 1))
    row = str(board_range - 1 - square//board_range)
    return col + row


def weffect(board):
    for square in range(board.BOARD_RANGE * board.BOARD_RANGE):
        if board.board[square] == board.BLACK:
            group, liberties = board.count(square, board.BLACK)
            board.restore()  # BUG: rimuovere o correggere restore
            current_block = [square2move(
                stone, board.BOARD_RANGE) for stone in group]
            print("Black blocks: ", current_block)
            print("Black liberties: ", len(liberties))
            if len(liberties) == 0:
                print("Gruppo nero senza libertà: {}".format(current_block))
                board.clear_group(group)
            else:
                # choose a liberty not on edge line
                off_edge_liberties = []
                for liberty in liberties:
                    if all(board.board[liberty + offset] != board.OFFBOARD for offset in [-board.BOARD_RANGE, 1, board.BOARD_RANGE, -1]):
                        off_edge_liberties.append(liberty)
                print("Off edge liberties: ", off_edge_liberties)
                if len(off_edge_liberties) >= 1:
                    random_liberty = choice(off_edge_liberties)
                    # if the group has 1 or 2 liberties
                    if len(liberties) < 3:
                        eval_liberty(random_liberty, liberties, board) 

def beffect(board):
    for square in range(board.BOARD_RANGE * board.BOARD_RANGE):
        if board.board[square] == board.WHITE:
            group, liberties = board.count(square, board.WHITE)
            board.restore()
            print("White blocks: ", [square2move(stone, board.BOARD_RANGE) for stone in group])
            print("White liberties: ", len(liberties))
            if len(liberties) == 1:
                board.best_move = next(iter(liberties))   
                #board.clear_group(group)
                # Appendo la mossa e libertà corrente per un 
                # confronto successivo con altri gruppi bianchi
                # in atari
                board.white_atari_move.append(board.best_move)                
                board.best_liberties = lookahead(board.best_move, board)
                board.white_atari_liberties.append(board.best_liberties)
                # Per evitare bug in cui più gruppi bianchi con una sola
                # libertà venissero cattuarati da mosse diverse e/o
                # venissero catturati per poi far piazzare una black stone
                # da un altra parte, esco dalla funzione non appena trovo
                # un gruppo bianco in pericolo
                #return
                
            elif len(liberties) >= 2:
                random_liberty = choice(list(liberties))
                eval_liberty(random_liberty, liberties, board)
    # Confronto atari
    if board.best_atari_move:
        best_liberty = max(board.white_atari_liberties)
        best_liberty_idx = board.white_atari_liberties.index(best_liberty)
        board.best_liberties = best_liberty
        board.best_move = board.white_atari_move[best_liberty_idx]
        
    # DEBUG
    """
    if board.best_move is None:
        print("Mossa casuale")
        board.best_move = choice(list(cur_liberties))
    """

def eval_liberty(square, liberties, board):
    # Lookahead previene mosse suicide
    if len(liberties) <= board.best_liberties and lookahead(square, board) >= 2:
        board.best_move = square
        board.best_liberties = len(liberties)

def lookahead(square, board):
    board.place_stone(square, board.BLACK)
    _, liberties = board.count(square, board.BLACK)
    board.remove_stone(square)
    board.restore()
    return len(liberties)

#def pats(board):
#    for square in range(board.BOARD_RANGE * board.BOARD_RANGE):
#        if board.board[square] == board.WHITE:
            

def place_handicap_stones(board):
    num_placed_stones = 0
    while num_placed_stones < ceil(sqrt(board.BOARD_SIZE)):
        square = (1 + randrange(1, board.BOARD_SIZE+1)) * -board.BOARD_RANGE + randrange(1, board.BOARD_SIZE+1)
        if not board.board[square] & 7:
            board.place_stone(square, board.BLACK)
            num_placed_stones += 1
        else:
            continue


def main():
    # Set board size
    while True:
        #input_board_size = input('Which board would you like to choose [{}]: '.format('/'.join(key for key in BOARDS.keys())))
        input_board_size = input('Which board would you like to choose: ')
        try:
            board_size = int(input_board_size)
            if board_size <= 0:
                raise ValueError
            board = Board(board_size)
            break
        except ValueError:
            print("Invalid board size!")

    # Place handicap stones (randomly)
    #place_handicap_stones(board)
    """
    board.place_stone(move2square('b5', board.BOARD_RANGE), board.BLACK)
    board.place_stone(move2square('c5', board.BOARD_RANGE), board.BLACK)
    board.place_stone(move2square('a4', board.BOARD_RANGE), board.BLACK)
    board.place_stone(move2square('d4', board.BOARD_RANGE), board.BLACK)
    board.place_stone(move2square('b3', board.BOARD_RANGE), board.BLACK)
    board.place_stone(move2square('b2', board.BOARD_RANGE), board.BLACK)
    board.place_stone(move2square('c2', board.BOARD_RANGE), board.BLACK)
    board.place_stone(move2square('d1', board.BOARD_RANGE), board.BLACK)

    board.place_stone(move2square('b4', board.BOARD_RANGE), board.WHITE)
    board.place_stone(move2square('c4', board.BOARD_RANGE), board.WHITE)
    board.place_stone(move2square('c3', board.BOARD_RANGE), board.WHITE)
    board.place_stone(move2square('d3', board.BOARD_RANGE), board.WHITE)
    board.place_stone(move2square('d2', board.BOARD_RANGE), board.WHITE)
    """
    
    #board.place_stone(move2square('b4', board.BOARD_RANGE), board.WHITE)
    board.place_stone(move2square('a4', board.BOARD_RANGE), board.WHITE)
    board.place_stone(move2square('d1', board.BOARD_RANGE), board.WHITE)
    board.place_stone(move2square('e1', board.BOARD_RANGE), board.WHITE)

    board.place_stone(move2square('a3', board.BOARD_RANGE), board.BLACK)
    board.place_stone(move2square('b4', board.BOARD_RANGE), board.BLACK)
    board.place_stone(move2square('c5', board.BOARD_RANGE), board.BLACK)
    board.place_stone(move2square('e2', board.BOARD_RANGE), board.BLACK)

    # Main loop
    while True:
        # Display the board
        board.render()
        # Check move from white
        move = input('Your move: ')
        # Check if the input is a valid command or a valid stone coordinate
        if move == 'quit': 
            print("Quitting game...")
            exit()
        elif move == 'reset':
            board.reset()
            place_handicap_stones(board)
        # Check if move is valid
        elif check_input(move, board_size):
            # Conversione necessaria perchè rappresento la board come un unico array.
            # In futuro potrei usare una rappresentazione tramite array di array.
            square = move2square(move, board.BOARD_RANGE)
            if board.board[square] & 7:
                print("Square already occupied.")
            else:
                board.place_stone(square, board.WHITE)
                weffect(board)
                board.render()
                beffect(board)
                print("Black move: ", square2move(board.best_move, board.BOARD_RANGE))
                board.place_stone(board.best_move, board.BLACK)
                board.reset_best_attr()

if __name__ == "__main__":
    main()

# TODO:
# 1) Wally non distingue due gruppi bianchi con 1 libertà rimanente. Cattura il primo che viene trovato
#    e non il più grande.
# 2) Quando un gruppo nero all'angolo ha una sola libertà, Wally tenta comunque di estendere inutilmente.
# 3) Le mosse suicide sono ancora permesse
# 4) Non sembra salvare gruppi con una sola libertà salvabili
# 5) ko non presente
