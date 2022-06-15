# Copyright 2022 Paul W. Graham 

import copy
import json
import tkinter
import tkinter.font
import tkinter.ttk
import tkinter.filedialog
import tkinter.messagebox

class Observer:
    def update(self, observerable, change = None):
        raise NotImplementedError()

class Observerable:
    def __init__(self):
        self._observers = set()

    def register_observer(self, observer):
        self._observers.add(observer)

    def remove_observer(self, observer):
        if observer in _observers:
            self._observers.remove(observer)

    def notify(self, changes = None, caller = None):
        for observer in self._observers:
            observer.update(changes, caller = None)

class MapModelError(Exception):
    def __init__(self, message):
        super().__init__(message)

class BadBrushError(MapModelError):
    def __init__(self, message):
        super().__init__(message)

class InvalidCompressionTypeError(MapModelError):
    def __init__(self, message):
        super().__init__(message)

class InvalidScreenSizeError(MapModelError):
    def __init__(self, message):
        super().__init__(message)

class InvalidMapSizeError(MapModelError):
    def __init__(self, message):
        super().__init__(message)

class LineEndpointError(MapModelError):
    def __init__(self, message):
        super().__init__(message)

class MapModelError(Exception):
    def __init__(self, message):
        super().__init__(message)

class MapValidationError(MapModelError):
    def __init__(self, message):
        super().__init__(message)

class OutsideOfMapBoundsError(MapModelError):
    def __init__(self, message):
        super().__init__(message)

class RectangleEndpointError(MapModelError):
    def __init__(self, message):
        super().__init__(message)

class MapModel(Observerable):
    ASCII_BRUSHES = ' !"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    ASCII_BRUSHES_SET = frozenset(ASCII_BRUSHES)
    COMPRESSION_TYPES = ("RowRLE")
    SAVE_VERSION = "0.0.2"

    def __init__(self, width, height, brush):
        super().__init__()

        self._map = [[]]
        self._resize_map(width, height, brush)

    def __str__(self):
        return self.to_string()

    def _cell_inside_map(self, x, y):
        x_inside, y_inside = self._coordinates_inside_map(x, y)
        return x_inside and y_inside

    def _convert_cells(
                                self,
                                screen_width,
                                screen_height,
                                screen_x,
                                screen_y,
                                cells,
                                addition):

        if screen_width < 0:
            raise InvalidScreenSizeError("screen_width must be greater than 0.")

        if screen_height < 0:
            raise InvalidScreenSizeError("screen_height must be greater than 0.")

        left_bound, top_bound, _, _ = self.screen_bounds(
                                            screen_width,
                                            screen_height,
                                            screen_x,
                                            screen_y, False)
        converted_cells = []
        if addition:
            for cell in cells:
                converted_cells.append(   ( cell[0] + left_bound,
                                            cell[1] + top_bound,
                                            cell[2]))
        else:
            for cell in cells:
                converted_cells.append(   ( cell[0] - left_bound,
                                            cell[1] - top_bound,
                                            cell[2]))

        return tuple(converted_cells)

    def _convert_coordinates(
                                self,
                                screen_width,
                                screen_height,
                                screen_x,
                                screen_y,
                                coordinates,
                                addition):

        if screen_width < 0:
            raise InvalidScreenSizeError("screen_width must be greater than 0.")

        if screen_height < 0:
            raise InvalidScreenSizeError("screen_height must be greater than 0.")

        left_bound, top_bound, _, _ = self.screen_bounds(
                                            screen_width,
                                            screen_height,
                                            screen_x,
                                            screen_y, False)
        converted_coordinates = []
        if addition:
            for coordinate in coordinates:
                converted_coordinates.append(   (coordinate[0] + left_bound,
                                                coordinate[1] + top_bound))
        else:
            for coordinate in coordinates:
                converted_coordinates.append(   (coordinate[0] - left_bound,
                                                coordinate[1] - top_bound))

        return tuple(converted_coordinates)

    def _coordinates_inside_map(self, x = 0, y = 0):
        return not (x < 0 or x >= len(self._map[0])), not (y < 0 or y >= len(self._map))

    def _resize_map(self, width, height, brush):
        if width < 1:
            raise InvalidMapSizeError("width must be greater than 1.")

        if height < 1:
            raise InvalidMapSizeError("height must be greater than 1.")

        if len(self._map[0]) < width:
            filler_list = [brush] * (width - len(self._map[0]))
            for row in self._map:
                row.extend(filler_list)
        elif len(self._map[0]) > width:
            for row_index in range(len(self._map)):
                 self._map[row_index] = self._map[row_index][:width]

        if len(self._map) < height:
            filler_row = [brush] * width
            filler_rows = [filler_row[:] for _ in range(height - len(self._map))]
            self._map.extend(filler_rows)
        elif len(self._map) > height:
            self._map = self._map[:height]

    def _screens(self, map_dimension, screen_dimension):
        full_screens, partial = divmod(map_dimension, screen_dimension)
        if partial:
            full_screens += 1
        return full_screens

    def _set_cell(self, x, y, brush):
        x_inside, y_inside = self._coordinates_inside_map(x, y)
        if not x_inside:
            raise OutsideOfMapBoundsError("x coordinate outside of map bounds.")

        if not y_inside:
            raise OutsideOfMapBoundsError("y coordinate outside of map bounds.")

        self._map[y][x] = copy.deepcopy(brush)

    def _set_cells(self, cells):
        for draw_request in cells:
            self._set_cell(*draw_request)

    def cell(self, x, y):
        x_inside, y_inside = self._coordinates_inside_map(x, y)
        if not x_inside:
            raise OutsideOfMapBoundsError("x coordinate outside of map bounds.")

        if not y_inside:
            raise OutsideOfMapBoundsError("y coordinate outside of map bounds.")

        return (x, y, self._map[y][x])

    def cells(self, requested_cells):
        return tuple([self.cell(*request) for request in requested_cells])

    def column(self, x):
        if x < 0 or x >= len(self._map[0]):
            raise OutsideOfMapBoundsError("x coordinate outside of map bounds.")

        return tuple([(x, y, row[x]) for y, row in enumerate(self._map)])

    def column_as_string(self, x):
        if x < 0 or x >= len(self._map[0]):
            raise OutsideOfMapBoundsError("x coordinate outside of map bounds.")

        return ''.join([row[x] for row in self._map])

    def convert_cells_from_map_to_screen(
        self,
        screen_width,
        screen_height,
        screen_x,
        screen_y,
        cells):

        return self._convert_cells(
                                    screen_width,
                                    screen_height,
                                    screen_x,
                                    screen_y,
                                    cells,
                                    False)

    def convert_cells_from_screen_to_map(
        self,
        screen_width,
        screen_height,
        screen_x,
        screen_y,
        cells):

        return self._convert_cells(
                                    screen_width,
                                    screen_height,
                                    screen_x,
                                    screen_y,
                                    cells,
                                    True)

    def convert_coordinates_from_map_to_screen(
        self,
        screen_width,
        screen_height,
        screen_x,
        screen_y,
        coordinates):

        return self._convert_coordinates(
                                            screen_width,
                                            screen_height,
                                            screen_x,
                                            screen_y,
                                            coordinates, False)

    def convert_coordinates_from_screen_to_map(
        self,
        screen_width,
        screen_height,
        screen_x,
        screen_y,
        coordinates):

        return self._convert_coordinates(
                                            screen_width,
                                            screen_height,
                                            screen_x,
                                            screen_y,
                                            coordinates, True)

    def coordinates_inside_quadrate(self, x_one, y_one, x_two, y_two, coordinates_to_consider = None):
        coordinates_inside = []
        small_x, big_x = sorted((x_one, x_two))
        small_y, big_y = sorted((y_one, y_two))
        if coordinates_to_consider is not None:
            for cell in coordinates_to_consider:
                if (small_x <= cell[0] <= big_x) and (small_y <= cell[1] <= big_y):
                    coordinates_inside.append((cell[0], cell[1]))
        else:
            small_x = max(small_x, 0)
            big_x = min(big_x, self.width() - 1)
            small_y = max(small_y, 0)
            big_y = min(big_y, self.height() - 1)
            for y in range(small_y, big_y + 1):
                for x in range(small_x, big_x + 1):
                    coordinates_inside.append((x, y))

        return tuple(coordinates_inside)

    def extract_valid_coordinates(self, coordinates, coordinates_to_consider = None):
        if coordinates_to_consider is not None:
            coordinates_set = {(cell[0], cell[1]) for cell in coordinates}
            coordinates_to_consider_set = {(cell[0], cell[1]) for cell in coordinates_to_consider}
            coordinates = tuple(coordinates_set.intersection(coordinates_to_consider_set))
        return self.coordinates_inside_quadrate(0, 0, self.width() - 1, self.height() - 1, coordinates)

    def flood_fill(self, x, y, brush, eight_way = False, coordinates_to_consider = None):
        x_inside, y_inside = self._coordinates_inside_map(x, y)
        if not x_inside:
            raise OutsideOfMapBoundsError("x coordinate outside of map bounds.")

        if not y_inside:
            raise OutsideOfMapBoundsError("y coordinate outside of map bounds.")

        _, _, target_brush = self.cell(x, y)
        cells = []
        seen = set()
        seeds = []
        if coordinates_to_consider is not None:
            coordinates_to_consider_set = {(cell[0], cell[1]) for cell in coordinates_to_consider}
            good_target = lambda w, h:  self._cell_inside_map(w, h) and \
                                        self.cell(w, h)[2] == target_brush and \
                                        (w, h) not in seen and \
                                        (w, h) in coordinates_to_consider_set
            if (x, y) in coordinates_to_consider_set:
                seeds.append((x, y, target_brush))
        else:
            seeds.append((x, y, target_brush))
            good_target = lambda w, h: self._cell_inside_map(w, h) and self.cell(w, h)[2] == target_brush and (w, h) not in seen

        while seeds:
            seed = seeds.pop()
            left_x = seed[0]
            right_x = seed[0]
            y = seed[1]
            while good_target(left_x - 1, y):
                left_x = left_x - 1
                cells.append((left_x, y, brush))
                seen.add((left_x, y))

            while good_target(right_x, y):
                cells.append((right_x, y, brush))
                seen.add((right_x, y))
                right_x = right_x + 1

            right_x = right_x - 1
            for a in (y + 1, y - 1):
                for x in range(left_x, right_x + 1):
                    seeded = False
                    if not good_target(x, a):
                        seeded = False
                    elif not seeded:
                        seeds.append(self.cell(x, a))
                        seeded = True

            if eight_way:
                if good_target(left_x - 1, y - 1):
                    seeds.append(self.cell(left_x - 1, y - 1))

                if good_target(left_x - 1, y + 1):
                    seeds.append(self.cell(left_x - 1, y + 1))

                if good_target(right_x + 1, y - 1):
                    seeds.append(self.cell(right_x + 1, y - 1))

                if good_target(right_x + 1, y + 1):
                    seeds.append(self.cell(right_x + 1, y + 1))

        return tuple(cells)

    def height(self):
        return len(self._map)

    def line(self, x_one, y_one, x_two, y_two, brush, coordinates_to_consider = None):
        if (x_one, y_one) == (x_two, y_two):
            raise LineEndpointError("Line endpoints can not be the same point.")

        line_cells = []

        # vertical line
        if x_one == x_two:
            small_y, big_y = sorted([y_one, y_two])

            for y in range(small_y, big_y + 1):
                line_cells.append((x_one, y, brush))
        # horizontal line
        elif y_one == y_two:
            small_x, big_x = sorted([x_one, x_two])

            for x in range(small_x, big_x + 1):
                line_cells.append((x, y_one, brush))
        else:
            # Bresenham algorithm
            if abs(y_two - y_one) < abs(x_two - x_one):
                if x_one > x_two:
                    start_x = x_two
                    start_y = y_two
                    end_x = x_one
                    end_y = y_one
                else:
                    start_x = x_one
                    start_y = y_one
                    end_x = x_two
                    end_y = y_two

                change_in_x = end_x - start_x
                change_in_y = end_y - start_y
                y_increment = 1
                if change_in_y < 0:
                    y_increment = -1
                    change_in_y = -change_in_y

                difference_between_points = (2 * change_in_y) - change_in_x
                y = start_y

                for x in range(start_x, end_x + 1):
                    line_cells.append((x, y, brush))
                    if difference_between_points > 0:
                        y = y + y_increment
                        difference_between_points = difference_between_points + (2 * (change_in_y - change_in_x))
                    else:
                        difference_between_points = difference_between_points + 2 * change_in_y
            else:
                if y_one > y_two:
                    start_x = x_two
                    start_y = y_two
                    end_x = x_one
                    end_y = y_one
                else:
                    start_x = x_one
                    start_y = y_one
                    end_x = x_two
                    end_y = y_two

                change_in_x = end_x - start_x
                change_in_y = end_y - start_y
                x_increment = 1
                if change_in_x < 0:
                    x_increment = -1
                    change_in_x = -change_in_x
                difference_between_points = (2 * change_in_x) - change_in_y
                x = start_x

                for y in range(start_y, end_y + 1):
                    line_cells.append((x, y, brush))
                    if difference_between_points > 0:
                        x = x + x_increment
                        difference_between_points = difference_between_points + (2 * (change_in_x - change_in_y))
                    else:
                        difference_between_points = difference_between_points + 2 * change_in_x

        if coordinates_to_consider is not None:
            coordinates_to_consider_set = {(cell[0], cell[1]) for cell in coordinates_to_consider}
            line_cells = [cell for cell in line_cells if (cell[0], cell[1]) in coordinates_to_consider_set]

        return tuple(line_cells)

    def load_from_filename(self, filename):
        with open(filename) as output:
            self.load_from_filepointer(output)

    def load_from_filepointer(self, filepointer):
        json_map = json.load(filepointer)
        if 'version' not in json_map:
            raise MapValidationError("Missing Version Number")

        if json_map['version'] != self.SAVE_VERSION:
            raise MapValidationError("Incompatible Version Number")

        if 'height' not in json_map:
            raise MapValidationError("Missing Height")

        if 'width' not in json_map:
            raise MapValidationError("Missing Width")

        if 'cells' not in json_map:
            raise MapValidationError("Missing Cells")

        if 'compression' not in json_map:
            raise MapValidationError("Missing Compression")

        cells = []
        if json_map['compression'] is None:
            for y, row in enumerate(json_map['cells']):
                for x, brush in enumerate(row):
                    cells.append((x, y, brush))
        elif json_map['compression'] == "RowRLE":
            for y, row in enumerate(json_map['cells']):
                x = 0
                for run in row:
                    for _ in range(run[1]):
                        cells.append((x, y, run[0]))
                        x += 1
        else:
            quoted_list_of_compression_types = ['"' + ct + '"' for ct in compression_types]
            raise InvalidCompressionTypeError(f"Compression type must be None or one of the following: {', '.join(quoted_list_of_compression_types)}")

        self.resize_map(json_map['width'], json_map['height'], ' ')
        self.set_cells(cells)

    def map_as_array(self):
        return tuple([tuple(row) for row in self._map])

    def map_as_cells(self):
        cells = []
        for y, row in enumerate(self._map):
            for x, cell in enumerate(row):
                cells.append((x, y, cell))
        return tuple(cells)

    def map_as_string(self, newline = '\n'):
        cells = []
        for row in self._map:
            for brush in row:
                cells.append(brush)
            cells.append(newline)

        return ''.join(cells)

    def rectangle(self, x_one, y_one, x_two, y_two, brush, filled = True, coordinates_to_consider = None):
        if (x_one, y_one) == (x_two, y_two):
            raise RectangleEndpointError("Rectangle endpoints can not be the same point.")

        x_inside, y_inside = self._coordinates_inside_map(x_one, y_one)

        if not x_inside:
            raise OutsideOfMapBoundsError("x_one coordinate outside of map bounds.")

        if not y_inside:
            raise OutsideOfMapBoundsError("y_one coordinate outside of map bounds.")

        x_inside, y_inside = self._coordinates_inside_map(x_two, y_two)

        if not x_inside:
            raise OutsideOfMapBoundsError("x_two coordinate outside of map bounds.")

        if not y_inside:
            raise OutsideOfMapBoundsError("y_two coordinate outside of map bounds.")


        small_x, big_x = sorted([x_one, x_two])
        small_y, big_y = sorted([y_one, y_two])

        rectangle_cells = []
        if filled:
            for y in range(small_y, big_y + 1):
                for x in range(small_x, big_x + 1):
                    rectangle_cells.append((x, y, brush))
        elif small_x == big_x or small_y == big_y:
            rectangle_cells.extend(self.line(small_x, small_y, big_x, big_y, brush))
        else:
            rectangle_cells.extend(self.line(small_x, small_y, big_x, small_y, brush))
            rectangle_cells.extend(self.line(big_x, small_y, big_x, big_y, brush))
            rectangle_cells.extend(self.line(big_x, big_y, small_x, big_y, brush))
            rectangle_cells.extend(self.line(small_x, big_y, small_x, small_y, brush))

        if coordinates_to_consider is not None:
            coordinates_to_consider_set = {(cell[0], cell[1]) for cell in coordinates_to_consider}
            rectangle_cells = [cell for cell in rectangle_cells if (cell[0], cell[1]) in coordinates_to_consider_set]

        return tuple(rectangle_cells)

    def resize_map(self, x, y, brush):
        changes = {}
        changes['type'] = 'map_resize'
        changes['old_size'] = (self.width(), self.height())
        changes['new_size'] = (x, y)
        self._resize_map(x, y, brush)
        self.notify(changes)

    def row(self, y):
        _, y_inside = self._coordinates_inside_map(y = y)
        if not y_inside:
            raise OutsideOfMapBoundsError("y coordinate outside of map bounds.")

        return tuple((x, y, cell) for x, cell in enumerate(self._map[y]))

    def row_as_string(self, y):
        _, y_inside = self._coordinates_inside_map(y = y)
        if not y_inside:
            raise OutsideOfMapBoundsError("y coordinate outside of map bounds.")

        return ''.join(self._map[y])

    def save_with_filename(self, filename, compression = None):
        with open(filename, "w") as output:
            self.save_with_filepointer(output, compression)

    def save_with_filepointer(self, filepointer, compression = None):

        if compression is not None:
            if compression not in self.COMPRESSION_TYPES:
                quoted_list_of_compression_types = ['"' + ct + '"' for ct in self.COMPRESSION_TYPES]
                raise InvalidCompressionTypeError(f"Compression type must be None or one of the following: {', '.join(quoted_list_of_compression_types)}")

        map = {}
        map["version"] = self.SAVE_VERSION
        map["width"] = self.width()
        map["height"] = self.height()
        map["compression"] = compression
        map['version'] = self.SAVE_VERSION

        if map["compression"] == "RowRLE":
            runs = []
            for row in self.map_as_array():
                row_run = []
                start_of_run = 0
                end_of_run = 0
                current_brush = row[0]
                next_index = end_of_run + 1

                while next_index < map["width"]:
                    if row[next_index] == current_brush:
                        end_of_run = next_index
                    else:
                        row_run.append((   current_brush,
                                            end_of_run - start_of_run + 1))
                        start_of_run = next_index
                        end_of_run = next_index
                        current_brush = row[next_index]

                    next_index += 1
                row_run.append((   current_brush,
                                    end_of_run - start_of_run + 1))
                runs.append(row_run)

            map["cells"] = runs
        else:
            map["cells"] = self.map_as_array()


        json.dump(map, filepointer)

    def screen_as_map_cells( self,
                screen_width,
                screen_height,
                screen_x,
                screen_y):
        coordinates = self.screen_as_map_coordinates(   screen_width,
                                                        screen_height,
                                                        screen_x,
                                                        screen_y)
        return self.cells(coordinates)

    def screen_as_map_coordinates(
                                    self,
                                    screen_width,
                                    screen_height,
                                    screen_x,
                                    screen_y):

        if screen_width < 0:
            raise InvalidScreenSizeError("screen_width must be greater than 0.")

        if screen_height < 0:
            raise InvalidScreenSizeError("screen_height must be greater than 0.")

        left_bound, top_bound, right_bound, bottom_bound = self.screen_bounds(
                                                            screen_width,
                                                            screen_height,
                                                            screen_x,
                                                            screen_y, False)

        coordinates = self.coordinates_inside_quadrate(
                                                    left_bound,
                                                    top_bound,
                                                    right_bound,
                                                    bottom_bound)

        return coordinates

    def screen_as_screen_cells( self,
                screen_width,
                screen_height,
                screen_x,
                screen_y):
        map_cells = self.cells(self.screen_as_map_coordinates(
                                                            screen_width,
                                                            screen_height,
                                                            screen_x,
                                                            screen_y))
        return self.convert_cells_from_map_to_screen(
                                                        screen_width,
                                                        screen_height,
                                                        screen_x,
                                                        screen_y,
                                                        map_cells)

    def screen_as_screen_coordinates( self,
                screen_width,
                screen_height,
                screen_x,
                screen_y):
        coordinates = self.screen_as_map_coordinates(   screen_width,
                                                        screen_height,
                                                        screen_x,
                                                        screen_y)
        return self.convert_coordinates_from_map_to_screen( screen_width,
                                                            screen_height,
                                                            screen_x,
                                                            screen_y,
                                                            coordinates)

    def screen_bounds(
                        self,
                        screen_width,
                        screen_height,
                        screen_x,
                        screen_y, clipped_to_map = True):

        left_bound = screen_x * screen_width
        top_bound = screen_y * screen_height

        right_bound = left_bound + screen_width - 1
        bottom_bound = top_bound + screen_height - 1

        if clipped_to_map:
            left_bound = max(left_bound, 0)
            right_bound = min(right_bound, self.width() - 1)

            top_bound = max(top_bound, 0)
            bottom_bound = min(bottom_bound, self.height() - 1)

        return (left_bound, top_bound, right_bound, bottom_bound)

    def screen_height(
        self,
        screen_height,
        screen_y,
        clipped_to_map = True):

        _, top_bound, _, bottom_bound = self.screen_bounds( 1,
                                                            screen_height,
                                                            0,
                                                            screen_y,
                                                            clipped_to_map)
        return (bottom_bound - top_bound) + 1

    def screen_width(
        self,
        screen_width,
        screen_x,
        clipped_to_map = True):

        left_bound, _, right_bound, _ = self.screen_bounds( screen_width,
                                                            1,
                                                            screen_x,
                                                            0,
                                                            clipped_to_map)
        return (right_bound - left_bound) + 1

    def screen_xy_that_contains_map_coordinate( self,
                                                screen_width,
                                                screen_height,
                                                map_coordinate):
        x = map_coordinate[0] // screen_width
        y = map_coordinate[1] // screen_height

        return (x, y)

    def screens_high(self, screen_height):
        if screen_height < 0:
            raise InvalidScreenSizeError("screen_height must be greater than 0.")

        return self._screens(self.height(), screen_height)

    def screens_wide(self, screen_width):
        if screen_width < 0:
            raise InvalidScreenSizeError("screen_width must be greater than 0.")

        return self._screens(self.width(), screen_width)

    def set_cell(self, x, y, brush):
        self._set_cell(x, y, brush)
        changes = {}
        changes['type'] = 'cells'
        changes['cells'] = ((x,y,brush),)
        self.notify(changes)

    def set_cells(self, cells):
        self._set_cells(cells)
        changes = {}
        changes['type'] = 'cells'
        changes['cells'] = tuple([tuple(cell) for cell in cells])

        self.notify(changes)

    def to_string(self, row_divider = '\n'):
        map_list = []
        for row in self._map:
            for cell in row:
                map_list.append(cell)
            map_list.append(row_divider)
        return ''.join(map_list)

    def width(self):
        return len(self._map[0])

class Command:
    def execute(self):
        raise NotImplementedError()

    def undo(self):
        raise NotImplementedError()

class WriteCellsCommand(Command):
    def __init__(self, map, cells_to_write):
        super().__init__()
        self._map = map
        self._cells_to_write = cells_to_write
        self._undo_cells = None

    def execute(self):
        self._undo_cells = self._map.cells([cell[:2] for cell in self._cells_to_write])
        self._map.set_cells(self._cells_to_write)

    def undo(self):
        if self._undo_cells is not None:
            self._map.set_cells(self._undo_cells)

class MapValidationError(Exception):
    def __init__(self, message):
        super().__init__(message)

class MapController(Observerable):
    def __init__(self, map, brushes, brush_hotkeys = {}, tool_hotkeys = {}):
        super().__init__()

        self._map = map
        self._brush_hotkeys = brush_hotkeys
        self._tool_hotkeys = tool_hotkeys

        self._default_tools = ('Paint', 'Line', 'Fill (4-way)', 'Fill (8-way)', 'Square', 'Box')
        self._open_types = (("JSON files", "*.json"), ("All files", "*.*"))
        self._save_types = (("JSON files", "*.json"), ("All files", "*.*"))
        self._default_open_extension = ".json"
        self._default_save_extension = ".json"

        self._default_tool_index = 0
        self._default_brush_index = 0
        self._default_new_map_fill_brush_index = 0

        self._default_palette = brushes

        self._mouse_drag = False
        self._tool_canceled = False

        self._tools = None

        self._last_action_before_save = None
        self._saved_with_empty_undo_stack = False
        self._modified = True
        self._undo_stack = []
        self._redo_stack = []
        self._save_filename = None

        self._current_brush_index = self._default_brush_index
        self._previous_brush_index = None
        self._current_tool_index = self._default_tool_index
        self._previous_tool_index = None
        self._current_status = ""
        self._current_cell_indicators = tuple()

        self._save_enabled = False
        self._redo_available = False
        self._undo_available = False

        self._default_screen = (10, 10, 0, 0)
        self._screen = (None,) * 4
        self._screen_enabled = False

        self._view = MapView(self._map, self)
        self._set_save_modified(self._modified)
        self._set_save_enabled(self._save_enabled)
        self._set_palette(self._default_palette)
        self._set_toolbar(self._default_tools)
        self._set_brush(self._default_brush_index)
        self._set_tool(self._default_tool_index)
        self._set_previous_tool(self._current_tool_index)
        self._set_screen(*self._default_screen)
        self._set_redo_available(self._redo_available)
        self._set_undo_available(self._undo_available)

        # force a map resize notification so that the view will redraw
        self._map.resize_map(self._map.width(), self._map.height(), None)
        self._view.start()

    def _clear_cell_indicators(self):
        self._set_cell_indicators(tuple())

    def _clear_undo_redo(self):
        self._undo_stack = []
        self._redo_stack = []
        self._last_action_before_save = None
        self._saved_with_empty_undo_stack = True
        self._set_redo_available(False)
        self._set_undo_available(False)


    def _invoke_command(self, command):
        self._undo_stack.append(command)
        self._redo_stack = []
        command.execute()
        self._set_save_modified(True)
        self._set_redo_available(False)
        self._set_undo_available(True)

    def _save_file(self, filename):
        try:
            with open(filename, "w") as output_file:
                self._map.save_with_filepointer(output_file, compression = "RowRLE")
            self._set_save_filename(filename)
            self._set_save_modified(False)

            if self._undo_stack:
                self._last_action_before_save = self._undo_stack[-1]
                self._saved_with_empty_undo_stack = False
            else:
                self._saved_with_empty_undo_stack = True
        except OSError as e:
            self._view.display_save_file_error()

    def _set_brush(self, brush_index):
        if self._current_brush_index != brush_index:
            self._set_previous_brush(self._current_brush_index)

        self._current_brush_index = brush_index

        changes = {'type' : 'brush_selection', 'brush_selection' : brush_index}
        self.notify(changes)

    def _set_cell_indicators(self, cells):
        self._current_cell_indicators = cells
        changes = { 'type' : 'cell_indicators',
                    'cell_indicators' : tuple(self._current_cell_indicators)}
        self.notify(changes)

    def _set_palette(self, palette):
        self._palette = palette
        changes = {'type' : 'palette', 'palette' :  self._palette}
        self.notify(changes)

    def _set_previous_brush(self, brush):
        self._previous_brush_index = brush

    def _set_previous_tool(self, tool):
        self._previous_tool_index = tool

    def _set_redo_available(self, redo_available):
        self._redo_available = redo_available
        changes = { 'type':'redo_available',
                    'redo_available' : self._redo_available}
        self.notify(changes)

    def _set_save_enabled(self, enabled):
        self._save_enabled = enabled
        changes = { 'type' : 'save_enabled',
                    'save_enabled' : self._save_enabled}
        self.notify(changes)

    def _set_save_filename(self, name):
        self._save_filename = name
        changes = { 'type' : 'filename',
                    'filename' : self._save_filename}
        self.notify(changes)

    def _set_save_modified(self, state):
        self._modified = state
        changes = { 'type' : 'file_modified',
                    'file_modified' : self._modified}
        self.notify(changes)

        if self._modified and self._save_filename is not None:
            self._set_save_enabled(True)
        else:
            self._set_save_enabled(False)

    def _set_screen(self, screen_width, screen_height, x, y):
        self._set_screen_dimensions(screen_width, screen_height)
        self._set_selected_screen(x, y)

    def _set_screen_dimensions(self, screen_width, screen_height):
            self._screen = (
                            screen_width,
                            screen_height,
                            self._screen[2],
                            self._screen[3]
                        )
            changes = {     'type' : 'screen_resize',
                            'screen_resize' :  (screen_width, screen_height)}
            self.notify(changes)

    def _set_previous_tool(self, tool_index):
        self._previous_tool_index = tool_index

    def _set_selected_screen(self, x, y):
            self._screen = (
                            self._screen[0],
                            self._screen[1],
                            x,
                            y
                        )
            changes = {     'type' : 'selected_screen',
                            'selected_screen' :  (x, y)}
            self.notify(changes)

    def _set_status(self, status):
        self._current_status = status
        changes = {'type' : 'status', 'status' : self._current_status}
        self.notify(changes)

    def _set_tool(self, tool_index):
        if self._current_tool_index != tool_index:
            self._set_previous_tool(self._current_tool_index)

        self._current_tool_index = tool_index
        self._operation_start_cell = None
        changes = {'type' : 'tool_selection', 'tool_selection' : self._current_tool_index}
        self.notify(changes)

    def _set_toolbar(self, tools):
        self._tools = tools
        changes = {'type' : 'toolbar', 'toolbar' : self._tools}
        self.notify(changes)

    def _set_undo_available(self, undo_available):
        self._undo_available = undo_available
        changes = { 'type':'undo_available',
                    'undo_available' : self._undo_available}
        self.notify(changes)

    def brush_hotkey(self, hotkey):
        if hotkey in brush_hotkeys:
            next_brush_index = 0
            if self._current_brush_index in brush_hotkeys[hotkey]:
                next_brush_index = brush_hotkeys[hotkey].index(self._current_brush_index) + 1
                if next_brush_index >= len(brush_hotkeys[hotkey]):
                    next_brush_index = 0
            self._set_brush(brush_hotkeys[hotkey][next_brush_index])

    def cell_mouse_one_down(self, cell):
        self._mouse_drag = True
        self._operation_start_cell = None
        self._clear_cell_indicators()
        self._set_status(f" ")
        cells = None
        if self._screen_enabled:
            cell = self._map.convert_coordinates_from_screen_to_map(*self._screen, (cell,))[0]
            coordinates_to_consider = self._map.screen_as_map_cells(*self._screen)
            screen_containing_cell = (self._screen[2], self._screen[3])
        else:
            coordinates_to_consider = None
            screen_containing_cell = self._map.screen_xy_that_contains_map_coordinate(
                                                                self._screen[0],
                                                                self._screen[1],
                                                                cell)

        if self._current_brush_index is not None and self._current_tool_index is not None:
            brush = self._palette[self._current_brush_index]
            if self._tools[self._current_tool_index] == 'Paint':
                self._set_status(f"Paint: {str(cell)} Screen: {screen_containing_cell}")
                self._invoke_command(WriteCellsCommand(self._map, ((*cell, brush),)))
            elif self._tools[self._current_tool_index] == 'Line':
                if self._operation_start_cell is None:
                    self._operation_start_cell = cell
            elif self._tools[self._current_tool_index] == 'Square':
                if self._operation_start_cell is None:
                    self._operation_start_cell = cell
            elif self._tools[self._current_tool_index] == 'Box':
                if self._operation_start_cell is None:
                    self._operation_start_cell = cell
            elif self._tools[self._current_tool_index] == 'Fill (4-way)':
                cells = self._map.flood_fill(*cell, brush, False, coordinates_to_consider)
                self._set_status(f"Fill (4-way): {str(cell)} #Cells: {len(cells)}")
            elif self._tools[self._current_tool_index] == 'Fill (8-way)':
                cells = self._map.flood_fill(*cell, brush, True, coordinates_to_consider)
                self._set_status(f"Fill (8-way): {str(cell)} #Cells: {len(cells)}")

            if cells is not None:
                self._set_cell_indicators(cells)

    def cell_mouse_one_motion(self, cell):
        self._clear_cell_indicators()
        coordinates_to_consider = None
        cells = None
        if self._screen_enabled:
            cell = self._map.convert_coordinates_from_screen_to_map(*self._screen, (cell,))[0]
            coordinates_to_consider = self._map.screen_as_map_cells(*self._screen)
            screen_containing_cell = (self._screen[2], self._screen[3])
        else:
            coordinates_to_consider = None
            screen_containing_cell = self._map.screen_xy_that_contains_map_coordinate(
                                                                self._screen[0],
                                                                self._screen[1],
                                                                cell)
        if not self._tool_canceled:
            self._set_status(f" ")
            if self._current_brush_index is not None and self._current_tool_index is not None:
                brush = self._palette[self._current_brush_index]
                if self._tools[self._current_tool_index] == 'Paint':
                    if self._mouse_drag:
                        self._set_status(f"Paint: {str(cell)} Screen: {screen_containing_cell}")
                        self._invoke_command(WriteCellsCommand(self._map, ((*cell, brush),)))
                elif self._tools[self._current_tool_index] == 'Line':
                    if self._operation_start_cell is not None and self._operation_start_cell != cell:
                        self._set_status(f"Line: {self._operation_start_cell}  {str(cell)}")
                        cells = self._map.line(*self._operation_start_cell, *cell, brush, coordinates_to_consider)
                elif self._tools[self._current_tool_index] == 'Square':
                    if self._operation_start_cell is not None and self._operation_start_cell != cell:
                        self._set_status(f"Square: {self._operation_start_cell}  {str(cell)}")
                        cells = self._map.rectangle(*self._operation_start_cell, *cell, brush, False, coordinates_to_consider)
                elif self._tools[self._current_tool_index] == 'Box':
                    if self._operation_start_cell is not None and self._operation_start_cell != cell:
                        cells = self._map.rectangle(*self._operation_start_cell, *cell, brush, True, coordinates_to_consider)
                        self._set_status(f"Box: {self._operation_start_cell}  {str(cell)} #Cells: {len(cells)}")
                elif self._tools[self._current_tool_index] == 'Fill (4-way)':
                    cells = self._map.flood_fill(*cell, brush, False, coordinates_to_consider)
                    self._set_status(f"Fill (4-way): {str(cell)} #Cells: {len(cells)}")
                elif self._tools[self._current_tool_index] == 'Fill (8-way)':
                    cells = self._map.flood_fill(*cell, brush, True, coordinates_to_consider)
                    self._set_status(f"Fill (8-way): {str(cell)} #Cells: {len(cells)}")

                if cells is not None:
                    self._set_cell_indicators(cells)

        else:
            self._set_status(f"Cell: {str(cell)}")

    def cell_mouse_one_up(self, cell):
        self._clear_cell_indicators()
        coordinates_to_consider = None
        if self._screen_enabled:
            cell = self._map.convert_coordinates_from_screen_to_map(*self._screen, (cell,))[0]
            coordinates_to_consider = self._map.screen_as_map_cells(*self._screen)
        self._set_status(f" ")
        self._mouse_drag = False
        if self._current_brush_index is not None and self._current_tool_index is not None and not self._tool_canceled:
            brush = self._palette[self._current_brush_index]
            if self._tools[self._current_tool_index] == 'Line':
                if self._operation_start_cell is not None and self._operation_start_cell != cell:
                    cells = self._map.line(*self._operation_start_cell, *cell, brush, coordinates_to_consider)
                    self._operation_start_cell = None
                    self._invoke_command(WriteCellsCommand(self._map, cells))
            elif self._tools[self._current_tool_index] == 'Square':
                if self._operation_start_cell is not None and self._operation_start_cell != cell:
                    cells = self._map.rectangle(*self._operation_start_cell, *cell, brush, False, coordinates_to_consider)
                    self._operation_start_cell = None
                    self._invoke_command(WriteCellsCommand(self._map, cells))
            elif self._tools[self._current_tool_index] == 'Box':
                if self._operation_start_cell is not None and self._operation_start_cell != cell:
                    cells = self._map.rectangle(*self._operation_start_cell, *cell, brush, True, coordinates_to_consider)
                    self._operation_start_cell = None
                    self._invoke_command(WriteCellsCommand(self._map, cells))
            elif self._tools[self._current_tool_index] == 'Fill (4-way)':
                cells = self._map.flood_fill(*cell, brush, False, coordinates_to_consider)
                self._invoke_command(WriteCellsCommand(self._map, cells))
            elif self._tools[self._current_tool_index] == 'Fill (8-way)':
                cells = self._map.flood_fill(*cell, brush, True, coordinates_to_consider)
                self._invoke_command(WriteCellsCommand(self._map, cells))
        self._operation_start_cell = None
        self._tool_canceled = False
        self._set_status(" ")

    def cell_mouse_three_down(self, cell):
        if self._mouse_drag:
            self._tool_canceled = True
            self._clear_cell_indicators()
        else:
            self.set_tool(self._default_tool_index)
            if self._screen_enabled:
                cell = self._map.convert_coordinates_from_screen_to_map(
                                                                *self._screen,
                                                                (cell,))[0]
                screen_containing_cell = (self._screen[2], self._screen[3])
            else:
                screen_containing_cell = self._map.screen_xy_that_contains_map_coordinate(
                                                                    self._screen[0],
                                                                    self._screen[1],
                                                                    cell)

            self._set_status(f"Cell: {str(cell)} Screen: {screen_containing_cell}")

    def cell_mouse_three_motion(self, cell):
        if not self._mouse_drag:
            if self._screen_enabled:
                cell = self._map.convert_coordinates_from_screen_to_map(
                                                                *self._screen,
                                                                (cell,))[0]
                screen_containing_cell = (self._screen[2], self._screen[3])
            else:
                screen_containing_cell = self._map.screen_xy_that_contains_map_coordinate(
                                                                    self._screen[0],
                                                                    self._screen[1],
                                                                    cell)

            self._set_status(f"Cell: {str(cell)} Screen: {screen_containing_cell}")

    def cell_mouse_three_up(self, cell):
        self._set_status(f" ")

    def disable_screen(self):
        self._screen_enabled = False
        changes = {'type' : 'screen_enabled', 'screen_enabled' : self._screen_enabled}
        self.notify(changes)
        self._set_status(f"")

    def enable_screen(self):
        self._screen_enabled = True
        changes = {'type' : 'screen_enabled', 'screen_enabled' : self._screen_enabled}
        self.notify(changes)
        self._set_status(f"Screen: {(self._screen[2], self._screen[3])}")

    def new_file(self):
        if not self._modified or self._view.prompt_confirm_file_new():
            new_map_dimensions = self._view.prompt_for_new_file(self._map.width(), self._map.height())
            if new_map_dimensions:
                self._set_save_filename(None)
                self._set_save_modified(True)
                self._map.resize_map(1, 1, self._palette[self._default_new_map_fill_brush_index])
                self._map.set_cell(0, 0, self._palette[self._default_new_map_fill_brush_index])
                self._map.resize_map(new_map_dimensions[0], new_map_dimensions[1], self._palette[self._default_new_map_fill_brush_index])
                self._clear_undo_redo()


    def open_file(self):
        if not self._modified or self._view.prompt_confirm_file_open():
            file_name = self._view.prompt_for_open_file(self._open_types, self._default_open_extension)
            if file_name:
                self.disable_screen()
                self._set_selected_screen(0,0)
                try:
                    with open(file_name, "r") as input_file:
                        self._map.load_from_filepointer(input_file)

                    self._set_save_filename(file_name)
                    self._set_save_modified(False)

                    self._clear_undo_redo()

                except OSError as e:
                    self._view.display_open_file_error()

                except MapValidationError as e:
                    self._view.display_open_file_error()

    def previous_brush(self):
        self._set_brush(self._previous_brush_index)

    def previous_tool(self):
        self._set_tool(self._previous_tool_index)

    def redo(self):
        if self._redo_stack:
            command = self._redo_stack.pop()
            self._undo_stack.append(command)
            command.execute()
            self._set_save_modified(not command is self._last_action_before_save)
            self._set_undo_available(True)

            if not self._redo_stack:
                self._set_redo_available(False)

    def resize_screen(self):
        screen_dimensions = self._view.prompt_for_screen_resize(self._screen[0], self._screen[1])
        if screen_dimensions:
            self._set_screen_dimensions(*screen_dimensions)

    def save(self):
        if self._save_filename is not None:
            self._save_file(self._save_filename)
        else:
            self.save_as()

    def save_as(self):
        filename = self._view.prompt_for_save_as(  self._default_save_extension,
                                        self._save_types)
        if filename:
            self._save_file(filename)

    def screen_down(self):
        if self._screen_enabled:
            _, screen_hight, x, y = self._screen
            if (y + 1) < self._map.screens_high(screen_hight):
                self._set_selected_screen(x, y + 1)
                self._set_status(f"Screen: {(self._screen[2], self._screen[3])}")

    def screen_enabled(self):
        return self._screen_enabled

    def screen_left(self):
        if self._screen_enabled:
            _, _, x, y = self._screen
            if (x - 1) >= 0:
                self._set_selected_screen(x - 1, y)
                self._set_status(f"Screen: {(self._screen[2], self._screen[3])}")

    def screen_right(self):
        if self._screen_enabled:
            screen_width, _, x, y = self._screen
            if (x + 1) < self._map.screens_wide(screen_width):
                self._set_selected_screen(x + 1, y)
                self._set_status(f"Screen: {(self._screen[2], self._screen[3])}")

    def screen_up(self):
        if self._screen_enabled:
            _, _, x, y = self._screen
            if (y - 1) >= 0:
                self._set_selected_screen(x, y - 1)
                self._set_status(f"Screen: {(self._screen[2], self._screen[3])}")

    def set_brush(self, brush_index):
        self._set_brush(brush_index)

    def set_screen(self):
        screen_xy = self._view.prompt_for_screen_coordinates(
        self._screen[2],
        self._screen[3],
        self._map.screens_wide(self._screen[0]),
        self._map.screens_high(self._screen[1])
        )
        if screen_xy is not None:
            self._set_selected_screen(*screen_xy)
            changes = {'type' : 'selected_screen', 'selected_screen' : screen_xy}
            self.notify(changes)

    def set_tool(self, tool_index):
        self._set_tool(tool_index)

    def toggle_screen(self):
        if self._screen_enabled:
            self.disable_screen()
        else:
            self.enable_screen()

    def tool_hotkey(self, hotkey):
        if hotkey in tool_hotkeys:
            next_tool_index = 0
            if self._current_tool_index in tool_hotkeys[hotkey]:
                next_tool_index = tool_hotkeys[hotkey].index(self._current_tool_index) + 1
                if next_tool_index >= len(tool_hotkeys[hotkey]):
                    next_tool_index = 0
            self._set_tool(tool_hotkeys[hotkey][next_tool_index])

    def undo(self):
        if self._undo_stack:
            command = self._undo_stack.pop()
            self._redo_stack.append(command)
            command.undo()
            self._set_save_modified(True)
            if self._undo_stack:
                if self._undo_stack[-1] == self._last_action_before_save:
                    self._set_save_modified(False)
            else:
                self._set_save_modified(not self._saved_with_empty_undo_stack)
            self._set_redo_available(True)

            if not self._undo_stack:
                self._set_undo_available(False)

class NewMapDialog(tkinter.simpledialog.Dialog):
    def __init__(self, parent, default_width, default_height, title = "Create New Map"):
        self._map_width_string = tkinter.StringVar()
        self._map_height_string = tkinter.StringVar()
        self._map_width_string.set(str(default_width))
        self._map_height_string.set(str(default_height))
        self._map_height = default_height
        self._map_width = default_width

        self._main_frame = None
        self._dimension_frame = None
        self._button_frame = None
        self._error_label = None
        self._canceled = False

        self._error_text = "Enter integers greater than 0"
        self._error_text_color = "red"

        super().__init__(parent, title)

    def get_map_dimensions(self):
        return (self._map_width, self._map_height,)

    def get_canceled(self):
        return self._canceled

    def cancel(self):
        self._canceled = True
        self.destroy()

    def create(self):
        try:
            self._map_height = int(self._map_height_string.get())
            self._map_width = int(self._map_width_string.get())
            if self._map_height < 1 or self._map_width < 1:
                self._error_label.configure(text = self._error_text, fg = self._error_text_color)
            else:
                self.destroy()
        except ValueError:
            self._error_label.configure(text = self._error_text, fg = self._error_text_color)

    def body(self, frame):
        self._error_label = tkinter.Label(frame, text = "")
        self._error_label.pack()
        self._dimension_frame = tkinter.Frame(frame)

        self._map_width_string_label = tkinter.Label(self._dimension_frame, text = "Width")
        self._map_width_string_label.grid(row = 0, column = 0)
        self._map_width_string_spinbox = tkinter.Spinbox(self._dimension_frame, textvariable = self._map_width_string, from_ = 1, to = 1000000)
        self._map_width_string_spinbox.grid(row = 0, column = 1)

        self._map_height_string_label = tkinter.Label(self._dimension_frame, text = "Height")
        self._map_height_string_label.grid(row = 1, column = 0)
        self._map_height_string_spinbox = tkinter.Spinbox(self._dimension_frame, textvariable = self._map_height_string, from_ = 1, to = 1000000)
        self._map_height_string_spinbox.grid(row = 1, column = 1)

        self._dimension_frame.pack()

        return frame

    def buttonbox(self):
        self._button_frame = tkinter.Frame(self)
        self.create_button = tkinter.Button(self._button_frame, text = 'Create', command = self.create)
        self.create_button.grid(row = 0, column = 0)
        cancel_button = tkinter.Button(self._button_frame, text = 'Cancel', command = self.cancel)
        cancel_button.grid(row = 0, column = 1)
        self._button_frame.pack()

        self.bind("<Return>", lambda event: self.create())
        self.bind("<Escape>", lambda event: self.cancel())

class SetScreenDialog(tkinter.simpledialog.Dialog):
    def __init__(self, parent, default_x, default_y, screens_wide, screens_high, title = "Set Screen"):
        self._screen_x_string = tkinter.StringVar()
        self._screen_y_string = tkinter.StringVar()
        self._screen_x_string.set(str(default_x))
        self._screen_y_string.set(str(default_y))

        self._screen_x = default_x
        self._screen_y = default_y
        self._screens_wide = screens_wide - 1
        self._screens_high = screens_high - 1

        self._main_frame = None
        self._coordinate_frame = None
        self._button_frame = None
        self._error_label = None
        self._canceled = False

        self._error_high_text = "Coordinate too large."
        self._error_low_text = "Enter integers greater than 0"

        self._error_text_color = "red"

        super().__init__(parent, title)

    def body(self, frame):
        self._error_label = tkinter.Label(frame, text = "")
        self._error_label.pack()
        self._coordinate_frame = tkinter.Frame(frame)

        self._screen_x_string_label = tkinter.Label(self._coordinate_frame, text = "x")
        self._screen_x_string_label.grid(row = 0, column = 0)
        self._screen_x_string_spinbox = tkinter.Spinbox(
            self._coordinate_frame,
            textvariable = self._screen_x_string,
            from_ = 0,
            to = self._screens_wide
            )
        self._screen_x_string_spinbox.grid(row = 0, column = 1)

        self._screen_y_label = tkinter.Label(self._coordinate_frame, text = "y")
        self._screen_y_label.grid(row = 1, column = 0)
        self._screen_y_spinbox =  tkinter.Spinbox(
            self._coordinate_frame,
            textvariable = self._screen_y_string,
            from_ = 0,
            to = self._screens_high
            )
        self._screen_y_spinbox.grid(row = 1, column = 1)

        self._coordinate_frame.pack()

        return frame

    def buttonbox(self):
        self._button_frame = tkinter.Frame(self)
        self.create_button = tkinter.Button(self._button_frame, text = 'Ok', command = self.set_screen)
        self.create_button.grid(row = 0, column = 0)
        cancel_button = tkinter.Button(self._button_frame, text = 'Cancel', command = self.cancel)
        cancel_button.grid(row = 0, column = 1)
        self._button_frame.pack()

        self.bind("<Return>", lambda event: self.set_screen())
        self.bind("<Escape>", lambda event: self.cancel())

    def cancel(self):
        self._canceled = True
        self.destroy()

    def get_canceled(self):
        return self._canceled

    def get_coordinates(self):
        return (self._screen_x, self._screen_y)

    def set_screen(self):
        try:
            self._screen_x = int(self._screen_x_string.get())
            self._screen_y = int(self._screen_y_string.get())
            if self._screen_x  < 0 or self._screen_y < 0:
                self._error_label.configure(text = self._error_low_text, fg = self._error_text_color)
            elif (not self._screen_x <= self._screens_wide) or (not self._screen_y <= self._screens_high):
                self._error_label.configure(text = self._error_high_text, fg = self._error_text_color)
            else:
                self.destroy()
        except ValueError:
            self._error_label.configure(text = self._error_low_text, fg = self._error_text_color)

class ResizeScreenDialog(tkinter.simpledialog.Dialog):
    def __init__(self,
                parent,
                default_width,
                default_height,
                title = "Resize the screen"
                ):
        self._screen_width_string = tkinter.StringVar()
        self._screen_height_string = tkinter.StringVar()
        self._screen_width_string.set(str(default_width))
        self._screen_height_string.set(str(default_height))
        self._screen_height = default_height
        self._screen_width = default_width

        self._main_frame = None
        self._dimension_frame = None
        self._button_frame = None
        self._error_label = None
        self._canceled = False

        self._error_text = "Enter integers greater than 0"
        self._error_text_color = "red"

        super().__init__(parent, title)

    def body(self, frame):
        self._error_label = tkinter.Label(frame, text = "")
        self._error_label.pack()
        self._dimension_frame = tkinter.Frame(frame)

        self._screen_width_string_label = tkinter.Label(self._dimension_frame, text = "Width")
        self._screen_width_string_label.grid(row = 0, column = 0)
        self._screen_width_string_spinbox = tkinter.Spinbox(self._dimension_frame, textvariable = self._screen_width_string, from_ = 1, to = 1000000)
        self._screen_width_string_spinbox.grid(row = 0, column = 1)

        self._screen_height_string_label = tkinter.Label(self._dimension_frame, text = "Height")
        self._screen_height_string_label.grid(row = 1, column = 0)
        self._screen_height_string_spinbox = tkinter.Spinbox(self._dimension_frame, textvariable = self._screen_height_string, from_ = 1, to = 1000000)
        self._screen_height_string_spinbox.grid(row = 1, column = 1)

        self._dimension_frame.pack()

        return frame

    def buttonbox(self):
        self._button_frame = tkinter.Frame(self)
        self.resize_button = tkinter.Button(self._button_frame, text = 'Resize', command = self.resize)
        self.resize_button.grid(row = 0, column = 0)
        cancel_button = tkinter.Button(self._button_frame, text = 'Cancel', command = self.cancel)
        cancel_button.grid(row = 0, column = 1)
        self._button_frame.pack()

        self.bind("<Return>", lambda event: self.resize())
        self.bind("<Escape>", lambda event: self.cancel())

    def cancel(self):
        self._canceled = True
        self.destroy()

    def get_canceled(self):
        return self._canceled

    def get_screen_dimensions(self):
        return (self._screen_width, self._screen_height,)

    def resize(self):
        try:
            self._screen_height = int(self._screen_height_string.get())
            self._screen_width = int(self._screen_width_string.get())
            if self._screen_height < 1 or self._screen_width < 1:
                self._error_label.configure(text = self._error_text, fg = self._error_text_color)
            else:
                self.destroy()
        except ValueError:
            self._error_label.configure(text = self._error_text, fg = self._error_text_color)

class MapView:
    def __init__(self, map, controller):
        self._map = map
        self._controller = controller

        self._map.register_observer(self)
        self._controller.register_observer(self)

        self._root = tkinter.Tk()
        self._root.rowconfigure(0, weight = 1)
        self._root.columnconfigure(0, weight = 1)

        self._status_string = tkinter.StringVar()
        self._status_string.set(" ")
        self._status_frame = tkinter.Frame(self._root)
        self._status = tkinter.Label(   self._status_frame,
                                        textvariable = self._status_string
                                    )
        self._status.pack(side = "left")
        self._status_frame.pack(side = "bottom", fill = "x")

        self._cell_font = tkinter.font.Font(font = "TkFixedFont")
        self._cell_font_size = 12
        self._cell_font.configure(size = self._cell_font_size)
        self._cell_character_width = self._cell_font.measure(" ")
        self._cell_character_height = self._cell_font.metrics('linespace')
        self._cell_spacing_precentage = 0
        self._cell_font_kerning = self._cell_spacing_precentage * self._cell_character_width
        self._cell_font_line_spacing = self._cell_spacing_precentage * self._cell_character_height
        self._cell_x_offset = self._cell_character_width
        self._cell_y_offset = self._cell_character_height

        self._cell_canvas_frame = tkinter.Frame(self._root)
        self._cell_canvas_frame.columnconfigure(0, weight = 1)
        self._cell_canvas_frame.rowconfigure(0, weight = 1)

        self._canvas_horizontal_scroll_bar = tkinter.ttk.Scrollbar(self._cell_canvas_frame, orient = "horizontal")
        self._canvas_vertical_scroll_bar = tkinter.ttk.Scrollbar(self._cell_canvas_frame, orient = "vertical")
        self._canvas_horizontal_scroll_bar.grid(column = 0, row = 1, sticky = "ew")
        self._canvas_vertical_scroll_bar.grid(column = 1, row = 0, sticky = "ns")

        self._canvas = tkinter.Canvas(  self._cell_canvas_frame,
                                        xscrollcommand = self._canvas_horizontal_scroll_bar.set,
                                        yscrollcommand = self._canvas_vertical_scroll_bar.set
                                        )

        self._canvas_horizontal_scroll_bar['command'] = self._canvas.xview
        self._canvas_vertical_scroll_bar['command'] = self._canvas.yview

        self._canvas.grid(column = 0, row = 0, sticky = "nw")

        self._selected_color = "cyan"
        self._current_brush = None
        self._brush_palette_frame = tkinter.Frame(self._root)
        self._brush_buttons = []
        self._brush_palette_frame.pack(side = "left", anchor = "nw")

        self._current_tool = None
        self._toolbar_frame = tkinter.Frame(self._root)
        self._toolbar_buttons = []
        self._toolbar_frame.pack(side = "right", anchor = "ne")

        self._indicator_tag = "indicator"
        self._indicator_color = "red"

        self._cell_text_color = "black"
        self._cell_text_tag = "cell_text"
        self._cell_canvas_cell_xy = None
        self._canvas_cells = None
        self._preview_cells = tuple()

        self._cell_canvas_frame.pack(side = "right", expand = True, fill = "both")

        self._program_name = "Map Edit -"
        self._modified_symbol = "*"
        self._unnamed_file_title = "<Untitled>"

        self._screen = (None,) * 4
        self._screen_enabled = None

        self._file_modified = None
        self._filename = self._unnamed_file_title

        self._menubar = tkinter.Menu(self._root, tearoff = False)
        self._root.configure(menu = self._menubar)

        self._filemenu = tkinter.Menu(self._menubar, tearoff = False)
        self._menubar.add_cascade(menu = self._filemenu, label = 'File')
        self._filemenu.add_command(label = "New", command = self._new_file)
        self._filemenu.add_command(label = "Open", command = self._open_file)
        self._filemenu.add_command(label = "Save", command = self._save)
        self._filemenu.add_command(label = "Save As", command = self._save_as)

        self._editmenu = tkinter.Menu(self._menubar, tearoff = False)
        self._menubar.add_cascade(menu = self._editmenu, label = 'Edit')
        self._editmenu.add_command(label = "Undo", command = self._undo)
        self._editmenu.add_command(label = "Redo", command = self._redo)

        self._screenmenu = tkinter.Menu(self._menubar, tearoff = False)
        self._menubar.add_cascade(menu = self._screenmenu, label = 'Screen')
        self._screenmenu.add_command(label = "Enable Screen", command = self._enable_screen)
        self._screenmenu.add_command(label = "Set Screen", command = self._set_screen, state = "disabled")
        self._screenmenu.add_command(label = "Resize Screen", command = self._resize_screen)

        self._canvas.bind('<Button-1>', self._canvas_mouse_one_down)
        self._canvas.bind('<B1-Motion>', self._canvas_mouse_one_motion)
        self._canvas.bind('<ButtonRelease-1>', self._canvas_mouse_one_up)
        self._canvas.bind('<Button-3>', self._canvas_mouse_three_down)
        self._canvas.bind('<B3-Motion>', self._canvas_mouse_three_motion)
        self._canvas.bind('<ButtonRelease-3>', self._canvas_mouse_three_up)

        self._root.bind('<Control-o>', self._window_open)
        self._root.bind('<Control-n>', self._window_new)
        self._root.bind('<Control-z>', self._window_undo)
        self._root.bind('<Control-y>', self._window_redo)
        self._root.bind('<Control-s>', self._window_save)

        self._root.bind('<Up>', self._window_screen_up)
        self._root.bind('<Down>', self._window_screen_down)
        self._root.bind('<Left>', self._window_screen_left)
        self._root.bind('<Right>', self._window_screen_right)

        self._root.bind('w', self._window_screen_up)
        self._root.bind('s', self._window_screen_down)
        self._root.bind('a', self._window_screen_left)
        self._root.bind('d', self._window_screen_right)

        self._root.bind('1', self._window_brush_hotkey)
        self._root.bind('2', self._window_brush_hotkey)
        self._root.bind('3', self._window_brush_hotkey)
        self._root.bind('4', self._window_brush_hotkey)
        self._root.bind('5', self._window_brush_hotkey)
        self._root.bind('6', self._window_brush_hotkey)
        self._root.bind('7', self._window_brush_hotkey)
        self._root.bind('8', self._window_brush_hotkey)
        self._root.bind('9', self._window_brush_hotkey)
        self._root.bind('0', self._window_brush_hotkey)

        self._root.bind('q', self._window_previous_brush)

        self._root.bind('e', self._window_tool_hotkey)
        self._root.bind('r', self._window_tool_hotkey)
        self._root.bind('f', self._window_tool_hotkey)

        self._root.bind('c', self._window_previous_tool)

        self._root.bind('<space>', self._window_toggle_screen)


        self._canvas.delete('all')

    def _canvas_mouse_one_down(self, event):
        cell_id = self._canvas.find_closest(event.widget.canvasx(event.x), event.widget.canvasy(event.y))[0]
        cell = self._cell_canvas_cell_xy[cell_id]
        self._controller.cell_mouse_one_down(cell)

    def _canvas_mouse_one_motion(self, event):
        cell_id = self._canvas.find_closest(event.widget.canvasx(event.x), event.widget.canvasy(event.y))[0]
        cell = self._cell_canvas_cell_xy[cell_id]
        self._controller.cell_mouse_one_motion(cell)

    def _canvas_mouse_one_up(self, event):
        cell_id = self._canvas.find_closest(event.widget.canvasx(event.x), event.widget.canvasy(event.y))[0]
        cell = self._cell_canvas_cell_xy[cell_id]
        self._controller.cell_mouse_one_up(cell)

    def _canvas_mouse_three_down(self, event):
        cell_id = self._canvas.find_closest(event.widget.canvasx(event.x), event.widget.canvasy(event.y))[0]
        cell = self._cell_canvas_cell_xy[cell_id]
        self._controller.cell_mouse_three_down(cell)

    def _canvas_mouse_three_motion(self, event):
        cell_id = self._canvas.find_closest(event.widget.canvasx(event.x), event.widget.canvasy(event.y))[0]
        cell = self._cell_canvas_cell_xy[cell_id]
        self._controller.cell_mouse_three_motion(cell)

    def _canvas_mouse_three_up(self, event):
        cell_id = self._canvas.find_closest(event.widget.canvasx(event.x), event.widget.canvasy(event.y))[0]
        cell = self._cell_canvas_cell_xy[cell_id]
        self._controller.cell_mouse_three_up(cell)

    def _clear_cell_indicators(self):
        indicators = self._canvas.find_withtag(self._indicator_tag)
        for indicator in indicators:
            cell = self._cell_canvas_cell_xy[indicator]
            self._canvas.itemconfigure(indicator, fill = self._cell_text_color, text = self._map.cell(cell[0], cell[1])[2])
        self._canvas.dtag(self._indicator_tag, self._indicator_tag)

    def _disable_screen(self):
        self._controller.disable_screen()

    def _enable_screen(self):
        self._controller.enable_screen()

    def _new_file(self):
        self._controller.new_file()

    def _open_file(self):
        self._controller.open_file()

    def _redo(self):
        self._controller.redo()

    def _resize_screen(self):
        self._controller.resize_screen()

    def _save(self):
        self._controller.save()

    def _save_as(self):
        self._controller.save_as()

    def _set_screen(self):
        self._controller.set_screen()

    def _undo(self):
        self._controller.undo()

    def _window_brush_hotkey(self, event):
        self._controller.brush_hotkey(event.keysym)

    def _window_new(self, event):
        self._new_file()

    def _window_open(self, event):
        self._open_file()

    def _window_previous_brush(self, event):
        self._controller.previous_brush()

    def _window_previous_tool(self, event):
        self._controller.previous_tool()

    def _window_redo(self, event):
        self._redo()

    def _window_save(self, event):
        self._save()

    def _window_screen_down(self, event):
        self._controller.screen_down()

    def _window_screen_left(self, event):
        self._controller.screen_left()

    def _window_screen_right(self, event):
        self._controller.screen_right()

    def _window_screen_up(self, event):
        self._controller.screen_up()

    def _window_toggle_screen(self, event):
        self._controller.toggle_screen()

    def _window_tool_hotkey(self, event):
        self._controller.tool_hotkey(event.keysym)

    def _window_undo(self, event):
        self._undo()

    def display_open_file_error(self):
        tkinter.messagebox.showerror(title = "Error", message = "Error opening file!")

    def display_save_file_error(self):
        tkinter.messagebox.showerror(title = "Error", message = "Error saving file!")

    def prompt_confirm_file_new(self):
        return tkinter.messagebox.askyesno(title = "Discard Changes?", message = "There are unsaved changes. Discard changes?")

    def prompt_confirm_file_open(self):
        return tkinter.messagebox.askyesno(title = "Discard Changes?", message = "There are unsaved changes. Discard changes and open file?")

    def prompt_for_new_file(self, default_map_width, default_map_height):
        new_file_dialog = NewMapDialog( self._root,
                                        default_map_width,
                                        default_map_height)
        dimensions = None
        if not new_file_dialog.get_canceled():
            dimensions = new_file_dialog.get_map_dimensions()
        return dimensions

    def prompt_for_open_file(self, open_types, default_extensions):
        filename = tkinter.filedialog.askopenfilename(
                                        filetypes = open_types,
                                        defaultextension = default_extensions
                                        )
        return filename

    def prompt_for_save_as(self, default_extension, save_types):
        filename = tkinter.filedialog.asksaveasfilename(
                                        filetypes = save_types,
                                        defaultextension = default_extension
                                        )
        return filename

    def prompt_for_screen_coordinates(self, default_x, default_y, screens_wide, screens_high):

        set_screen_dialog = SetScreenDialog(self._root, default_x, default_y, screens_wide, screens_high)
        coordinates = None
        if not set_screen_dialog.get_canceled():
            coordinates = set_screen_dialog.get_coordinates()
        return coordinates

    def prompt_for_screen_resize(self, default_width, default_height):
        resize_screen_dialog = ResizeScreenDialog(
                                self._root,
                                default_width,
                                default_height)
        dimensions = None
        if not resize_screen_dialog.get_canceled():
            dimensions = resize_screen_dialog.get_screen_dimensions()
        return dimensions

    def start(self):
        self._root.mainloop()

    def update(self, changes, caller = None):
        self._update_screen(changes)
        self._update_title_bar(changes)
        self._update_save_enabled(changes)
        self._update_redo_undo(changes)
        self._update_cells(changes)
        self._update_cell_indicators(changes)
        self._update_brush_palette(changes)
        self._update_toolbar(changes)
        self._update_brush_selection(changes)
        self._update_tool_selection(changes)
        self._update_status(changes)

    def _update_brush_palette(self, changes):
        if changes['type'] == 'palette':
            palette = changes['palette']
            if len(self._brush_buttons) > len(palette):
                for button in self._brush_buttons[len(palette):]:
                    button.destroy()
            elif len(self._brush_buttons) < len(palette):
                for _ in range(len(self._brush_buttons), len(palette)):
                    button = tkinter.Button(self._brush_palette_frame)
                    self._brush_buttons.append(button)

            row = 0
            for brush_index, brush in enumerate(palette):
                command = lambda i=brush_index: self._controller.set_brush(i)
                self._brush_buttons[brush_index].configure(text = str(brush), command = command)
                self._brush_buttons[brush_index]['font'] = self._cell_font
                self._brush_buttons[brush_index].grid(column = brush_index % 4, row = row)
                if (brush_index % 4) == 3:
                    row += 1

    def _update_brush_selection(self, changes):
        if changes['type'] == 'brush_selection':
            brush_index = changes['brush_selection']
            if self._current_brush != None:
                self._brush_buttons[self._current_brush]["bg"] = "SystemButtonFace"
            self._current_brush = brush_index
            self._brush_buttons[self._current_brush]["bg"] = self._selected_color

    def _update_cell_indicators(self, changes):
        if changes['type'] == 'cell_indicators':
            self._clear_cell_indicators()
            if not self._screen_enabled:
                change_set = changes['cell_indicators']
            else:
                change_set = self._map.convert_cells_from_map_to_screen(
                                *self._screen,
                                changes['cell_indicators'])
            for cell in change_set:
                self._canvas.itemconfigure(self._canvas_cells[cell[1]][cell[0]], fill = self._indicator_color, text = cell[2])
                self._canvas.addtag_withtag(self._indicator_tag, self._canvas_cells[cell[1]][cell[0]])

    def _update_cells(self, changes):
        repaint_changes = ['screen_enabled', 'selected_screen', 'screen_resize', 'map_resize']
        change_set = []
        if changes['type'] in repaint_changes:
            if not self._screen_enabled:
                number_of_rows = self._map.height()
                number_of_columns = self._map.width()
                change_set = self._map.map_as_cells()
            else:
                number_of_rows = self._map.screen_height(self._screen[1], self._screen[3])
                number_of_columns = self._map.screen_width(self._screen[0], self._screen[2])
                change_set = self._map.screen_as_screen_cells(*self._screen)

            self._cell_canvas_cell_xy = {}
            self._canvas_cells = []
            self._canvas.delete('all')
            canvas_width = (self._cell_character_width + self._cell_font_kerning) * number_of_columns + self._cell_x_offset
            canvas_height = ( self._cell_character_height + self._cell_font_line_spacing) * number_of_rows + self._cell_y_offset
            self._canvas.config(    scrollregion = f"0 0 {canvas_width} {canvas_height}",
                                    width = canvas_width,
                                    height = canvas_height )

            for y in range(number_of_rows):
                cell_row = []
                for x in range(number_of_columns):
                    cell_x_position = ((self._cell_character_width + self._cell_font_kerning ) * x) + self._cell_x_offset
                    cell_y_position = ((self._cell_character_height + self._cell_font_line_spacing) * y) + self._cell_y_offset
                    cell_id = self._canvas.create_text(cell_x_position, cell_y_position, font = self._cell_font, tag = self._cell_text_tag)
                    self._cell_canvas_cell_xy[cell_id] = (x, y)
                    cell_row.append(cell_id)
                self._canvas_cells.append(cell_row)

        elif changes['type'] == 'cells':
            if not self._screen_enabled:
                change_set = changes['cells']
            else:
                coordinates_in_screen = self._map.screen_as_map_coordinates(*self._screen)
                valid_coordinates = self._map.extract_valid_coordinates(
                                                        changes['cells'],
                                                        coordinates_in_screen)
                valid_cells = []
                for cell in changes['cells']:
                    if (cell[0], cell[1]) in valid_coordinates:
                        valid_cells.append(cell)

                change_set = self._map.convert_cells_from_map_to_screen(
                                *self._screen,
                                valid_cells)

        for cell in change_set:
            cell_id = self._canvas_cells[cell[1]][cell[0]]
            self._canvas.itemconfigure(cell_id, text = str(cell[2]))

    def _update_redo_undo(self, changes):
        if changes['type'] == 'redo_available':
            if changes['redo_available']:
                self._editmenu.entryconfig(1, state = "normal")
            else:
                self._editmenu.entryconfig(1, state = "disabled")
        elif changes['type'] == 'undo_available':
            if changes['undo_available']:
                self._editmenu.entryconfig(0, state = "normal")
            else:
                self._editmenu.entryconfig(0, state = "disabled")

    def _update_save_enabled(self, changes):
        if changes['type'] == 'save_enabled':
            if changes['save_enabled']:
                self._filemenu.entryconfig(2, state = "normal")
            else:
                self._filemenu.entryconfig(2, state = "disabled")

    def _update_screen(self, changes):
        if changes['type'] == 'screen_enabled':
            self._screen_enabled = changes['screen_enabled']
            if self._screen_enabled:
                self._screenmenu.entryconfig(0, label = "Disable Screen", command = self._controller.disable_screen)
                self._screenmenu.entryconfig(1, state = "normal")
            else:
                self._screenmenu.entryconfig(0, label = "Enable Screen", command = self._controller.enable_screen)
                self._screenmenu.entryconfig(1, state = "disabled")
        elif changes['type'] == 'screen_resize':
            self._screen = (
                            *changes['screen_resize'],
                            self._screen[2],
                            self._screen[3]
                        )
        elif  changes['type'] == 'selected_screen':
            self._screen = (
                            self._screen[0],
                            self._screen[1],
                            *changes['selected_screen']
                        )

    def _update_status(self, changes):
        if changes['type'] == 'status':
            text = changes['status']
            self._status_string.set(text)

    def _update_title_bar(self, changes):
        redraw_title_changes = ['file_modified', 'filename']
        redraw_title = False
        if changes['type'] == 'file_modified':
            self._file_modified = changes['file_modified']
            redraw_title = True
        elif changes['type'] == 'filename':
            self._filename = changes['filename']
            if self._filename is None:
                self._filename = self._unnamed_file_title
            redraw_title = True

        if redraw_title:
            title_bar = [self._program_name]
            if self._file_modified:
                title_bar.append(self._modified_symbol)
            title_bar.append(self._filename)
            self._root.title(" ".join(title_bar))

    def _update_tool_selection(self, changes):
        if changes['type'] == 'tool_selection':
            tool_index = changes['tool_selection']
            if self._current_tool != None:
                self._toolbar_buttons[self._current_tool]["bg"] = "SystemButtonFace"
            self._current_tool = tool_index
            self._toolbar_buttons[self._current_tool]["bg"] = self._selected_color

    def _update_toolbar(self, changes):
        if changes['type'] == 'toolbar':
            tools = changes['toolbar']
            if len(self._toolbar_buttons) > len(tools):
                for button in self._toolbar_buttons[len(tools):]:
                    button.destroy()
            elif len(self._toolbar_buttons) < len(tools):
                for _ in range(len(self._toolbar_buttons), len(tools)):
                    button = tkinter.Button(self._toolbar_frame)
                    self._toolbar_buttons.append(button)

            for tool_index, tool in enumerate(tools):
                command = lambda i = tool_index: self._controller.set_tool(i)
                self._toolbar_buttons[tool_index].configure(text = str(tool), command = command)
                self._toolbar_buttons[tool_index]['font'] = self._cell_font
                self._toolbar_buttons[tool_index].pack(side = 'top', anchor="n", fill = "both")

if __name__ == "__main__":
    brush_hotkeys = {
                        '1' : [0, 1, 2, 3],
                        '2' : [4, 5, 6, 7],
                        '3' : [8, 9, 10, 11],
                        '4' : [12, 13, 14, 15],
                        '5' : [16, 17, 18, 19],
                        '6' : [20, 21, 22, 23],
                        '7' : [24, 25, 26, 27],
                        '8' : [28, 29, 30, 31],
                        '9' : [32, 33, 34, 35],
                        '0' : [36, 37, 38, 39]
                        }

    tool_hotkeys = {
        'e' : [1, 0],
        'r' : [5, 4],
        'f' : [2, 3]
    }
    m = MapModel(100,100, " ")
    c = MapController(m, m.ASCII_BRUSHES, brush_hotkeys, tool_hotkeys)
