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
        self.liberties = []
        self.blocks = []
        self.best_liberties = board_size * board_size
        self.best_move = None

    def create(self):
        # Create the top and bottom rows (full of 7s)
        top_bottom_row = [self.OFFBOARD] * self.BOARD_RANGE
        # Create the middle rows (7s on the sides, 0s in the middle)
        middle_row = [self.OFFBOARD] + [self.EMPTY] * self.BOARD_SIZE + [self.OFFBOARD]
        # Create the full board
        board = [top_bottom_row] + [middle_row for _ in range(self.BOARD_SIZE)] + [top_bottom_row]
        # Flatten the board to a single list
        flat_board = [item for sublist in board for item in sublist]
        return flat_board

    # RENDER SQUARE BOARD ON CONSOLE
    def render(self):
        # File markers
        files = [chr(ascii_code) for ascii_code in range(97, 97 + self.BOARD_SIZE)]

        for row in range(self.BOARD_RANGE):
            for col in range(self.BOARD_RANGE):
                if col == 0 and row > 0 and row < self.BOARD_RANGE - 1:
                    cur_row = self.BOARD_RANGE - 1 - row
                    print(cur_row, end='' if cur_row>=10 else ' ')

                square = row * self.BOARD_RANGE + col
                stone = self.board[square]
                print(self.pieces[stone] + ' ', end='')
            print()
        print('    ' + ' '.join(files) + '\n') # last row of column coords
    
    def reset(self):
        self.board = self.create() 
        self.liberties = []
        self.blocks = []

    def place_stone(self, square, color):
        #if not(piece == self.EMPTY or piece == self.LIBERTY):
        if (self.board[square] & 7):
            print("Square already occupied.")
            return 0
        else:
            self.board[square] = color
            return 1
        
    def remove_stone(self, square):
        self.board[square] &= 8
        
    # count liberties, save stone group coords (COUNT sub on byte magazine 1981)
    def count(self, square, color):
        piece = self.board[square]
        if piece == self.OFFBOARD:
            return
        # If there's a stone at square (i.e. square is not empty (0) 
        # AND has the same color as input AND is not marked)
        if piece and piece & color and (piece & self.MARKER) == 0:
            # save stone's coordinate
            self.blocks.append(square)
            # mark the stone
            self.board[square] |= self.MARKER
            # look for neighbours recursively
            self.count(square - self.BOARD_RANGE, color)    # N
            self.count(square + 1, color)                   # E
            self.count(square + self.BOARD_RANGE, color)    # S
            self.count(square - 1, color)                   # W
        # if the square is empty
        elif piece == self.EMPTY:
            # mark liberty
            self.board[square] |= self.LIBERTY
            # save liberties
            self.liberties.append(square)

    def restore(self):
        self.liberties = []
        self.blocks = []
        # unmark stones
        for square in range(self.BOARD_RANGE * self.BOARD_RANGE):
            # restore piece if the square is on board
            if self.board[square] != self.OFFBOARD: 
                self.board[square] &= 3

    def clear_block(self):
        for captured in self.blocks: 
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
            msg = "Invalid column input, it must be between 'a' and '{}'".format(last_char)
        else:
            if input_string[1:].isdigit():
                row = int(input_string[1:])
                if row < 1 or row > board_size:
                    msg = "Invalid row, it must be between 1 and {}".format(board_size)
                else:
                    outstate = 1 # Tutto ok
            else:
                msg = "Invalid row."
    if not outstate:
        print(msg)
    return outstate


def move2square(move, board_range):
    return (1 + int(move[1:])) * -board_range + ord(move[0]) % 97 + 1


def place_stone(square, player_turn, board):
    # Check if square is occupied before placing the stone
    if board.place_stone(square, player_turn):  
        #board.count(square, player_turn) # DEBUG MODE
        #print("Number of liberties: ", len(board.liberties))
        return 1
    return 0


def weffect(board):
    for square in range(board.BOARD_RANGE * board.BOARD_RANGE):
        if board.board[square] == board.BLACK:
            board.count(square, board.BLACK)
            if not board.liberties:
                board.clear_block()
            else:
                # choose a liberty not on edge line
                off_edge_liberties = []
                print("Blocks: ", board.blocks)
                print("Board liberties: ", len(board.liberties))
                for liberty in board.liberties:
                    if all(board.board[liberty + offset] != board.OFFBOARD for offset in [-board.BOARD_RANGE, 1, board.BOARD_RANGE, -1]):
                        off_edge_liberties.append(liberty)
                print("Off edge liberties: ", len(off_edge_liberties))
                if off_edge_liberties:
                    random_liberty = choice(off_edge_liberties)
                    # if the group has 1 or 2 liberties
                    if len(board.liberties) < 3:
                        eval_liberty(random_liberty, board) 

def eval_liberty(square, board):
    if len(board.liberties) <= board.best_liberties and lookahead(square, board) >= 2:
        board.best_move = square
        board.best_liberties = len(board.liberties)

def lookahead(square, board):
    place_stone(square, board.BLACK, board)
    board.count(square, board.BLACK)
    board.remove_stone(square)
    return len(board.liberties)


def place_handicap_stones(board):
    for _ in range(ceil(sqrt(board.BOARD_SIZE))):
        square = (1 + randrange(1, board.BOARD_SIZE+1)) * -board.BOARD_RANGE + randrange(1, board.BOARD_SIZE+1)
        place_stone(square, board.BLACK, board)


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
    #player_turn = board.WHITE
    player_turn = board.BLACK # DEBUG

    while True:
        # Display the board
        board.render()
        # Check move
        if player_turn == board.WHITE: # DEBUG
            sleep(0.1)
            move = chr(97 + randrange(board.BOARD_SIZE)) + str(randrange(1, board.BOARD_SIZE+1))
            print("Wally's move: ", move)
        else:
            move = input('Your move: ')
            # Check if the input is a valid command or a valid stone coordinate
            if move == 'quit': 
                print("Quitting game...")
                exit()
            elif move == 'reset':
                board.reset()
                place_handicap_stones(board)
                continue
            # Check if move is valid
            elif not check_input(move, board_size):
                continue

        square = move2square(move, board.BOARD_RANGE)
        if place_stone(square, player_turn, board):
            weffect(board)
            board.restore()
            player_turn = player_turn#3 - player_turn # DEBUG

if __name__ == "__main__":
    main()