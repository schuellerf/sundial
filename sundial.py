#!/usr/bin/env python3

import inkex
import simplepath
import simplestyle
import re
import math
import sys
import csv
from lxml import etree
import datetime
import calendar

class Sundial(inkex.Effect):
        def __init__(self):
                inkex.Effect.__init__(self)
                self.arg_parser.add_argument("--csvfile", type=str,
                                action="store",
                                default=None,
                                dest="csvfile", 
                                help="Sundial input data (CSV)")
                self.arg_parser.add_argument("--length", type=int,
                                action="store",
                                default=27,
                                dest="length", 
                                help="Sundial shadow stick length")
                self.arg_parser.add_argument("--box_mode", type=str,
                                action="store",
                                default="false",
                                dest="box_mode", 
                                help="Generate the more advanced 'Box-Mode'")
                self.arg_parser.add_argument("--day_start", type=int,
                                action="store",
                                default=6,
                                dest="day_start", 
                                help="Hour of the day to start")
                self.arg_parser.add_argument("--day_end", type=int,
                                action="store",
                                default=18,
                                dest="day_end", 
                                help="Hour of the day to end")
                self.arg_parser.add_argument("--sundial_type", type=str,
                                action="store",
                                default="both",
                                dest="sundial_type", 
                                help="Print the whole year or only half values are: both, summer_to_winter_only, winter_to_summer_only")
                self.arg_parser.add_argument("--solstice_summer", type=str,
                                action="store",
                                default="06-21",
                                dest="solstice_summer", 
                                help="Day of the summer solstice MM-DD")
                self.arg_parser.add_argument("--solstice_winter", type=str,
                                action="store",
                                default="12-21",
                                dest="solstice_winter", 
                                help="Day of the winter solstice MM-DD")

                self.arg_parser.add_argument("--offset_x", type=int,
                                action="store",
                                default=150,
                                dest="offset_x", 
                                help="X-Offset of the stick on the paper")
                self.arg_parser.add_argument("--offset_y", type=int,
                                action="store",
                                default=150,
                                dest="offset_y", 
                                help="Y-Offset of the stick on the paper")
                self.arg_parser.add_argument("--bounding_box", type=int,
                                action="store",
                                default=130,
                                dest="bounding_box", 
                                help="Bounding box size to cut the paths")

                self.txt_i = 1

        def new_path(self, parent, path, color, name=None, close= False, dashed=False):
            if name is None:
                name = name = f"path{self.txt_i}"
                self.txt_i += 1

            path_str = " ".join([f"{x},{y}" for x,y in path])
            style   = {
                    'stroke'        : color,
                    'stroke-width': inkex.units.convert_unit('1px', 'mm'),
                     'fill'          : 'none',
                     'stroke-linejoin':'round'
                   }

            if dashed:
                style['stroke-miterlimit'] = 4
                style['stroke-dasharray'] = "1.58749792,1.58749792"
                style['stroke-dashoffset'] = 0

            style_str   = str(inkex.Style(style))

            if close:
                close_str = ' z'
            else:
                close_str = ''

            attribs = {'style' : style_str,
                    inkex.addNS('label','inkscape') : name,
                    'stroke-linecap': 'round',
                    'd' : f'M {path_str}{close_str}'}

            line = etree.SubElement(parent, inkex.addNS('path','svg'), attribs )
        def new_circle(self, parent, x,y, color=None, name=None, fill=True):
            if color is None:
                color = '#000000'

            if name is None:
                name = name = f"circle{self.txt_i}"
                self.txt_i += 1

            style   = {
                    'stroke'        : color,
                     'stroke-width': '0.1px',
                   }

            if fill:
                style['fill'] = color
                style['fill-opacity'] = '1'
            else:
                style['fill'] = 'none'
                style['fill-opacity'] = '1'

            style_str   = str(inkex.Style(style))

            attribs = {'style' : style_str,
                    'id' : name,
                    'cx': str(x),
                    'cy': str(y),
                    'rx': '1',
                    'ry': '1'}

            line = etree.SubElement(parent, inkex.addNS('ellipse','svg'), attribs )

        def new_text(self, parent, name, x,y, text, anchor="start", rotate=None, fontsize=None):
            if not fontsize:
                # just some estimation
                fontsize = self.fontsize

            style   = str(inkex.Style({
                    'font-size'    : str(fontsize),
                    'font-family'  : 'sans-serif',
                     'stroke-width':0.2,
                   }))
            if name is None:
                name = f"text{self.txt_i}"
                self.txt_i += 1
            attribs = { 'style' : style,
                        'text-anchor': anchor,
                        'id': name }
            if rotate:
                attribs['transform'] = f"translate({x},{y}) rotate({rotate})"
            else:
                attribs['x'] = str(x)
                attribs['y'] = str(y)

            line = etree.SubElement(parent, inkex.addNS('text','svg'), attribs)
            line.text = text

        def map_coords(self, length, el, az, box_mode = None):
            # on the flat surface
            el_rad = (el / 180.0) * math.pi
            az_rad = (az / 180.0) * math.pi
            d = length / math.tan(el_rad)
            x = math.cos(az_rad) * d + self.offset_x
            y = math.sin(az_rad) * d + self.offset_y
            if box_mode is None:
                box_mode = self.box_mode

            if box_mode:
                flat_size = self.bounding_box - self.length
                if y < (self.offset_y - flat_size):
                    x_out = (1/math.tan(az_rad)) * flat_size
                    d2 = math.sqrt(math.pow(x_out,2) + math.pow(flat_size,2))
                    y_out = length - math.tan(el_rad) * d2
                    y = self.offset_y - flat_size - y_out
                    x = self.offset_x - x_out
                if x < self.offset_x - flat_size:
                    y_out = math.tan(az_rad) * flat_size
                    d2 = math.sqrt(math.pow(y_out,2) + math.pow(flat_size,2))
                    x_out = length - math.tan(el_rad) * d2
                    y = self.offset_y - y_out
                    x = self.offset_x - flat_size - x_out
                if y > (self.offset_y + flat_size):
                    x_out = (1/math.tan(az_rad)) * flat_size
                    d2 = math.sqrt(math.pow(x_out,2) + math.pow(flat_size,2))
                    y_out = length - math.tan(el_rad) * d2
                    y = self.offset_y + flat_size + y_out
                    x = self.offset_x + x_out
                    
            return (x,y)

        def effect(self):
            self.length = self.options.length
            self.box_mode = True if self.options.box_mode == 'true' else False
            self.day_start = self.options.day_start
            self.day_end = self.options.day_end
            self.sundial_type = self.options.sundial_type
            self.solstice_summer = self.options.solstice_summer
            self.solstice_winter = self.options.solstice_winter
            self.offset_x = self.options.offset_x
            self.offset_y = self.options.offset_y
            self.bounding_box = self.options.bounding_box
            # some rough estimation for the fontsize
            self.fontsize = self.length / 10
            self.fontsize_x_spacing = self.fontsize
            self.fontsize_y_spacing = self.fontsize * 1.3
            # just a shorter variable name
            txt_x_gap = self.fontsize_x_spacing
            txt_y_gap = self.fontsize_y_spacing

            parent = self.svg.get_current_layer()
            color = '#000000'
            direction = None
            months = {} #full day of each 1st in a month
            month_dots = {} #full day of each 1st in a month only full hours

            #time from 1st of Jan to summer solstice
            hours_summer1 = {} # one hour over the whole year

            #time from winter solstice to 31st of December
            hours_summer2 = {} # one hour over the whole year
            hours_winter = {} # one hour over the whole year

            x = self.offset_x
            y = self.offset_y
            l = self.length
            d = l * math.sin(math.pi / 4) # length l in 45° angle
            y_15 = l * math.sin(math.pi / 12) # length l in 15° angle
            x_15 = l * math.cos(math.pi / 12) # length l in 15° angle
            hgt = math.sqrt(3*math.pow(d,2))

            self.new_path(parent, [(x     , y),
                                   (x, y + l)], color='#909090', name="Reference length")
            self.new_text(parent, None, x + 1, y + l, f"Stick height reference", anchor='start')

            # Cut instructions:
            self.new_path(parent, [(x + d, y + d),
                                   (x    , y)], color, close=False, name="Places of triangle 1")

            self.new_path(parent, [(x    , y),
                                   (x + d, y - d)], color, close=False, dashed=True, name="Places of triangle 2")

            self.new_path(parent, [(x + d, y + d),
                                   (x + d , y - d),
                                   (x + d + hgt, y )], color)

            self.new_path(parent, [(x + d + hgt, y),
                                   (x + d, y + d)], color, close=False, dashed=True)

            self.new_path(parent, [(x + d , y - d),
                                   (x + d + x_15, y - d - y_15),
                                   (x + d + hgt, y)], color, close=False, dashed=True)

            self.new_text(parent, None, x + d + x_15 - txt_x_gap, y - d - y_15 - 1 - 2 * txt_y_gap, f"Cut on dashed lines,", anchor='end')
            self.new_text(parent, None, x + d + x_15 - txt_x_gap, y - d - y_15 - 1 - 1 * txt_y_gap, f"Bend on solid lines,", anchor='end')
            self.new_text(parent, None, x + d + x_15 - txt_x_gap, y - d - y_15 - 1 - 0 * txt_y_gap, f"tape to numbers", anchor='end')
            self.new_text(parent, None, x + d/2, y - d/2 + txt_x_gap, f"1", anchor='start')
            self.new_text(parent, None, x + d + x_15/2, y - d - y_15 / 2 + txt_y_gap, f"1", anchor='start')

            self.new_text(parent, None, x + d/2, y - d/2 - txt_y_gap, f"2", anchor='end')
            self.new_text(parent, None, x + d + x_15 + y_15 / 2 - 1, y - d - y_15 + x_15/2, f"2", anchor='end')

        
            if self.box_mode:
                x_right_end = x + d + x_15 + y_15 + txt_x_gap
                self.new_path(parent, [(x_right_end, y - self.bounding_box + l),
                                       (x - self.bounding_box + l, y - self.bounding_box + l),
                                       (x - self.bounding_box + l, y + self.bounding_box - l),
                                       (x_right_end, y + self.bounding_box - l)], color, close=False)
                self.new_text(parent, None, x_right_end, y - self.bounding_box + l + 2, f"https://github.com/schuellerf/sundial", anchor='end', rotate=-90)

                self.new_path(parent, [(x - self.bounding_box + l, y - self.bounding_box + l),
                                       (x - self.bounding_box, y - self.bounding_box + l)], color, close=False, dashed=True)
                self.new_text(parent, None, x - self.bounding_box + txt_x_gap, y - self.bounding_box + l + txt_y_gap, f"3", anchor='start')

                self.new_path(parent, [(x - self.bounding_box + l, y + self.bounding_box - l),
                                       (x - self.bounding_box, y + self.bounding_box - l)], color, close=False, dashed=True)
                self.new_text(parent, None, x - self.bounding_box + txt_x_gap, y + self.bounding_box - l - txt_y_gap, f"4", anchor='start')

                self.new_path(parent, [(x - self.bounding_box + l, y - self.bounding_box + l),
                                       (x - self.bounding_box + l, y - self.bounding_box)], color, close=False, dashed=True)
                self.new_text(parent, None, x - self.bounding_box + l + txt_x_gap, y - self.bounding_box + txt_y_gap, f"3", anchor='start')

                self.new_path(parent, [(x - self.bounding_box + l, y + self.bounding_box - l),
                                       (x - self.bounding_box + l, y + self.bounding_box)], color, close=False, dashed=True)
                self.new_text(parent, None, x - self.bounding_box + l + txt_x_gap, y + self.bounding_box - txt_y_gap, f"4", anchor='start')

                # Box outer border
                self.new_path(parent, [(x_right_end, y - self.bounding_box),
                                       (x - self.bounding_box + l, y - self.bounding_box)], color, close=False, dashed=True)
                self.new_path(parent, [(x - self.bounding_box, y - self.bounding_box + l),
                                       (x - self.bounding_box, y + self.bounding_box - l)], color, close=False, dashed=True)
                self.new_path(parent, [(x - self.bounding_box + l, y + self.bounding_box),
                                       (x_right_end, y + self.bounding_box)], color, close=False, dashed=True)


            summer_date = None
            winter_date = None
            date_re = re.compile(r"(?P<angle>[AE]) (?P<timestamp>(?P<timestamp_min_only>(?P<h>\d{2}):(?P<m>\d{2})):(?P<s>\d{2}))")

            with open(self.options.csvfile) as csvfile:
                dialect = csv.Sniffer().sniff(csvfile.readline())
                csvfile.seek(0)

                reader = csv.DictReader(csvfile, dialect=dialect)
                #example how do debug: inkex.utils.debug(reader.fieldnames)
                date_col = reader.fieldnames[0]
                year = None

                gps_coords = date_col.replace("coo: ","")
                # 1.4 as an approximation as the text is tilted
                self.new_text(parent, None, x + d + txt_x_gap/1.4, y + d - txt_y_gap/1.4, f"{gps_coords}", anchor='start', rotate=-30)
                for row in reader:
                    for col in reader.fieldnames:
                        time_col = date_re.match(col)
                        if not time_col:
                            continue
                        # only use Azimuth! Elevation is fetched later anyway
                        if time_col.group("angle") != "A":
                            continue

                        if int(time_col.group("h")) < self.day_start or \
                           int(time_col.group("h")) > self.day_end:
                            continue
                        if int(time_col.group("h")) == self.day_end and \
                           (int(time_col.group("m")) != 0 or \
                            int(time_col.group("s")) != 0):
                            continue

                        timestamp = time_col.group("timestamp")
                        timestamp_min_only = time_col.group("timestamp_min_only")
                        
                    #for h in range(self.day_start, self.day_end + 1):
                        try:
                            az_csv = float(row[f"A {timestamp}"])
                            el_csv = float(row[f"E {timestamp}"])

                            if el_csv == 0 or az_csv == 0:
                                raise ValueError()
                        except ValueError:
                            continue
                        x,y = self.map_coords(self.length, el_csv, az_csv)
                        planar_x, planar_y = self.map_coords(self.length, el_csv, az_csv, box_mode = False)

                        if abs(x-self.offset_x) > self.bounding_box:
                            continue
                        if abs(y-self.offset_y) > self.bounding_box:
                            continue

                        date_txt = row[date_col]


                        date = datetime.datetime.strptime(date_txt, '%Y-%m-%d')

                        if year is None:
                            year = date.year
                            sdate = self.solstice_summer.split("-")
                            wdate = self.solstice_winter.split("-")
                            summer_date = datetime.datetime(year, int(sdate[0]), int(sdate[1]))
                            winter_date = datetime.datetime(year, int(wdate[0]), int(wdate[1]))
                        # only draw dates of one year
                        if year != date.year:
                            continue

                        if date < summer_date:
                            hours = hours_summer1
                        elif date < winter_date and date > summer_date:
                            hours = hours_winter
                        elif date > winter_date:
                            hours = hours_summer2

                        hrs = hours.get(timestamp_min_only,[])
                        hrs.append((x,y))
                        hours[timestamp_min_only] = hrs

                        anchor = 'start'
                        if date.month < 4:
                            anchor = 'end'
                        if date.month >= 7 and date.month <= 9:
                            anchor = 'end'

                        # SMELL skip drawing month lines on box sides
                        # adding a point on the box edge would be needed
                        
                        if date.day == 1 and (x == planar_x) and (y == planar_y):

                            #self.new_text(parent, None, x,y, date_txt, anchor)
                            #self.new_circle(parent, x,y, color)
                            m = months.get(date.month,[])
                            m.append((x,y))
                            months[date.month] = m
                            if timestamp.endswith(":00:00") or len(m) == 1:
                                m = month_dots.get(date.month,[])
                                m.append((x,y))
                                month_dots[date.month] = m
                            



            for m in months:
                if m > summer_date.month and m <= winter_date.month:
                    if self.sundial_type == 'winter_to_summer_only':
                        continue
                    color = '#000000'
                    anchor = 'end'
                    offset = -3
                else:
                    if self.sundial_type == 'summer_to_winter_only':
                        continue
                    color = '#FF0000'
                    anchor = 'start'
                    offset = +3

                self.new_path(parent, months[m], color, f"Month {m}")
                coord = months[m][0]
                self.new_text(parent, None, coord[0] + offset, coord[1], f"{calendar.month_name[m]}", anchor=anchor)
                for p in month_dots[m]:
                    self.new_circle(parent, p[0], p[1], color)

            if self.sundial_type != 'summer_to_winter_only':
                for h in hours_summer1:
                    if h.endswith(":00"):
                        color = '#FF0000'
                    else:
                        color = '#FFBEBE'
                    self.new_path(parent, hours_summer1[h], color, f"{h}h")

                    # only label full hours
                    if not h.endswith(":00"):
                        continue

                    coord = hours_summer1[h][-1]
                    self.new_circle(parent, coord[0], coord[1], color, fill=False)
                    self.new_text(parent, None, coord[0] + txt_x_gap, coord[1], f"{h}", anchor='start')

                    coord = hours_summer1[h][0]
                    self.new_circle(parent, coord[0], coord[1], color, fill=False)
                    if coord[1] < self.offset_y:
                        coord = (coord[0],coord[1] + txt_y_gap)
                    self.new_text(parent, None, coord[0] - txt_x_gap, coord[1], f"{h}", anchor='end')

                for h in hours_summer2:
                    if h.endswith(":00"):
                        color = '#FF0000'
                    else:
                        color = '#FFBEBE'

                    self.new_path(parent, hours_summer2[h], color, f"{h}")
                    #connect both
                    if h in hours_summer1:
                        self.new_path(parent, [hours_summer2[h][-1],hours_summer1[h][0]], color, f"{h}")

            if self.sundial_type != 'winter_to_summer_only':
                for h in hours_winter:
                    if h.endswith(":00"):
                        color = '#000000'
                    else:
                        color = '#C6C6C6'

                    self.new_path(parent, hours_winter[h], color, f"{h}")

                    # only label full hours
                    if not h.endswith(":00"):
                        continue
                    if self.sundial_type != 'both':

                        coord = hours_winter[h][0]
                        self.new_circle(parent, coord[0], coord[1], color, fill=False)
                        self.new_text(parent, None, coord[0] + txt_x_gap, coord[1], f"{h}", anchor='start')

                        coord = hours_winter[h][-1]
                        self.new_circle(parent, coord[0], coord[1], color, fill=False)
                        if coord[1] < self.offset_y:
                            coord = (coord[0],coord[1] + txt_y_gap)
                        self.new_text(parent, None, coord[0] - txt_x_gap, coord[1], f"{h}", anchor='end')
                


if __name__ == '__main__':
        e = Sundial()
        e.run()

