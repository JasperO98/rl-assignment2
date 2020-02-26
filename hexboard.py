import cv2 as cv
from math import sin, radians
import numpy as np
from hexcolour import HexColour


class HexBoard:
    def __init__(self, size):
        self.moves = []
        self.board = {}
        self.size = size

    def turn(self):
        return HexColour.BLUE if len(self.moves) % 2 else HexColour.RED

    def dijkstra(self, colour, render=False):
        nodes = {}
        for i in range(self.size):
            for j in range(self.size):
                if not self.is_colour((i, j), colour.invert()):
                    if (colour == HexColour.RED and i == 0) or (colour == HexColour.BLUE and j == 0):
                        nodes[i, j] = 0 if self.is_colour((i, j), colour) else 1
                    else:
                        nodes[i, j] = np.inf

        while True:
            if len(nodes) == 0:
                return np.inf

            move, weight = min(nodes.items(), key=lambda item: item[1])
            del nodes[move]

            if render:
                self.render(0, {**nodes, move: str(weight) + 'P'})

            if (colour == HexColour.RED and move[0] == self.size - 1) or \
                    (colour == HexColour.BLUE and move[1] == self.size - 1):
                return weight

            for neighbour in self.neighbourhood(move):
                if neighbour in nodes:
                    nodes[neighbour] = min(nodes[neighbour], weight + (0 if self.is_colour(neighbour, colour) else 1))

    def neighbourhood(self, coords):
        for diff in ((1, 0), (0, 1), (1, -1), (-1, 1), (0, -1), (-1, 0)):
            neighbour = (coords[0] + diff[0], coords[1] + diff[1])
            if self.exists(neighbour):
                yield neighbour

    def is_game_over(self):
        return len(self.board) == self.size ** 2 or self.check_win(HexColour.RED) or self.check_win(HexColour.BLUE)

    def check_win(self, colour):
        return self.dijkstra(colour) == 0

    def do_move(self, coords):
        self.board[coords] = self.turn()
        self.moves.append(coords)

    def do_moves(self, coords):
        for coord in coords:
            self.do_move(coord)

    def undo_move(self):
        del self.board[self.moves.pop()]

    def is_empty(self, coords):
        return coords not in self.board

    def is_colour(self, coords, colour):
        return not self.is_empty(coords) and self.board[coords] == colour

    def exists(self, coords):
        for coord in coords:
            if coord < 0 or coord > self.size - 1:
                return False
        return True

    def possible_moves(self):
        for i in range(self.size):
            for j in range(self.size):
                if self.is_empty((i, j)):
                    yield i, j

    def render(self, timeout, mask=None):
        # calculate all relevant lengths
        hex_long = int(round(
            2000 / (self.size * 3 - 1)
        ))
        hex_short = int(round(
            hex_long * sin(radians(30)) / sin(radians(60))
        ))
        hex_diag = int(round(
            hex_long * sin(radians(90)) / sin(radians(60))
        ))

        # create canvas
        canvas = cv.imread('background.jpg')
        canvas = cv.resize(canvas, (
            hex_long * (self.size * 3 - 1) + 12,
            hex_diag * self.size + hex_short * (self.size + 1) + 12,
        ))

        # render hexes
        for i in range(self.size):
            for j in range(self.size):
                h = i * (hex_diag + hex_short) + 6
                w = i * hex_long + j * hex_long * 2 + 6

                color = (255, 255, 255)
                if self.is_colour((i, j), HexColour.RED):
                    color = (0, 0, 255)
                if self.is_colour((i, j), HexColour.BLUE):
                    color = (255, 0, 0)

                points = np.array((
                    (w, h + hex_short),
                    (w + hex_long, h),
                    (w + hex_long * 2, h + hex_short),
                    (w + hex_long * 2, h + hex_short + hex_diag),
                    (w + hex_long, h + hex_diag + hex_short * 2),
                    (w, h + hex_short + hex_diag),
                ))

                if mask:
                    text = str(mask[i, j]) if (i, j) in mask else ''
                else:
                    text = str(i) + chr(ord('a') + j)

                cv.fillPoly(canvas, [points], color)
                cv.polylines(canvas, [points], True, (0, 0, 0), 12)
                cv.putText(
                    canvas,
                    text,
                    (w + int(hex_long / 1.75), h + hex_short + int(hex_diag / 1.5)),
                    cv.FONT_HERSHEY_SIMPLEX,
                    16 / self.size,
                    (0, 0, 0),
                    16,
                )
                cv.putText(
                    canvas,
                    text,
                    (w + int(hex_long / 1.75), h + hex_short + int(hex_diag / 1.5)),
                    cv.FONT_HERSHEY_SIMPLEX,
                    16 / self.size,
                    (255, 255, 255),
                    4,
                )

        # render borders
        points = [(6, hex_short + 6)]
        for i in range(self.size):
            points.append((i * hex_long * 2 + 6 + hex_long, 6))
            points.append(((i + 1) * hex_long * 2 + 6, hex_short + 6))
        points = np.array(points)

        cv.polylines(canvas, [points], False, (0, 0, 255), 12)
        points[:, 0] = canvas.shape[1] - points[:, 0]
        points[:, 1] = canvas.shape[0] - points[:, 1]
        cv.polylines(canvas, [points], False, (0, 0, 255), 12)

        points = []
        for i in range(self.size):
            points.append((6 + i * hex_long, 6 + hex_short + (hex_short + hex_diag) * i))
            points.append((6 + i * hex_long, 6 + hex_short + hex_diag + (hex_short + hex_diag) * i))
        points = np.array(points)

        cv.polylines(canvas, [points], False, (255, 0, 0), 12)
        points[:, 0] = canvas.shape[1] - points[:, 0]
        points[:, 1] = canvas.shape[0] - points[:, 1]
        cv.polylines(canvas, [points], False, (255, 0, 0), 12)

        # apply anti aliasing
        canvas = cv.resize(src=canvas, dsize=None, fx=0.25, fy=0.25, interpolation=cv.INTER_AREA)

        # show canvas
        cv.imshow('HEX', canvas)
        cv.waitKey(timeout)
