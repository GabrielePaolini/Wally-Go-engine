## Python port of Jonathan K Millen's Wally Go engine

This is an incomplete implementation of the Go engine called Wally.
Wally was developed and published in an [article for BYTE magazine](https://archive.org/details/byte-magazine-1981-04/) by Jonathan K Millen.
The game engine follows simple rules based on a series of pattern matching with different degrees of priority.
Wally always plays black, in accordance with the Go tradition of giving the black stones to the weaker player.

## How to use

The game is played on the command line and can be started by typing:

```
python wally.py
```
The game will ask you to enter the size of the squre game grid (a.k.a. goban), and then the game will start.
Stone coordinates are specified by means of a letter (row) and a number (column). 
To confirm the move just press Enter.
The game will continue until no legal moves are available.

## Missing features

- [ ] Scoring system.
- [ ] Pattern matching system on common configuration of stones.
