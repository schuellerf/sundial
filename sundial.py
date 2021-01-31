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
                                default=30,
                                dest="length", 
                                help="Sundial shadow stick length")
                self.arg_parser.add_argument("--offset_x", type=int,
                                action="store",
                                default=165,
                                dest="offset_x", 
                                help="X-Offset of the stick on the paper")
                self.arg_parser.add_argument("--offset_y", type=int,
                                action="store",
                                default=150,
                                dest="offset_y", 
                                help="Y-Offset of the stick on the paper")
                self.arg_parser.add_argument("--bounding_box", type=int,
                                action="store",
                                default=140,
                                dest="bounding_box", 
                                help="Bounding box size to cut the paths")
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

                self.txt_i = 1
        def new_path(self, parent, path, color, name=None, close= False):
            if name is None:
                name = name = f"path{self.txt_i}"
                self.txt_i += 1

            path_str = " ".join([f"{x},{y}" for x,y in path])
            style   = str(inkex.Style({
                    'stroke'        : color,
                    'stroke-width': inkex.units.convert_unit('1px', 'mm'),
                     'fill'          : 'none',
                     'stroke-linejoin':'round'
                   }))

            if close:
                close_str = ' z'
            else:
                close_str = ''

            attribs = {'style' : style,
                    inkex.addNS('label','inkscape') : name,
                    'stroke-linecap': 'round',
                    'd' : f'M {path_str}{close_str}'}

            line = etree.SubElement(parent, inkex.addNS('path','svg'), attribs )
        def new_circle(self, parent, x,y, color=None, name=None):
            if color is None:
                color = '#000000'

            if name is None:
                name = name = f"circle{self.txt_i}"
                self.txt_i += 1

            style   = str(inkex.Style({
                    'stroke'        : color,
                    'fill'        : color,
                     'stroke-width': '1px',
                     'fill-opacity': '1'
                   }))

            attribs = {'style' : style,
                    'id' : name,
                    'cx': str(x),
                    'cy': str(y),
                    'rx': '0.5',
                    'ry': '0.5'}

            line = etree.SubElement(parent, inkex.addNS('ellipse','svg'), attribs )

        def new_text(self, parent, name, x,y, text, anchor="start"):
            style   = str(inkex.Style({
                    'font-size'        : '3px',
                    'font-family': 'sans-serif',
                     'stroke-width':0.2,
                   }))
            if name is None:
                name = f"text{self.txt_i}"
                self.txt_i += 1
            attribs = { 'style' : style,
                        'x': str(x),
                        'y': str(y),
                        'text-anchor': anchor,
                        'id': name }
            line = etree.SubElement(parent, inkex.addNS('text','svg'), attribs)
            line.text = text

        def map_coords(self, length, el, az):
            el_rad = (el / 180.0) * math.pi
            az_rad = (az / 180.0) * math.pi
            d = length / math.tan(el_rad)
            x = math.cos(az_rad) * d + self.offset_x
            y = math.sin(az_rad) * d + self.offset_y
            return (x,y)

        def effect(self):
            self.length = self.options.length
            self.day_start = self.options.day_start
            self.day_end = self.options.day_end
            self.offset_x = self.options.offset_x
            self.offset_y = self.options.offset_y
            self.bounding_box = self.options.bounding_box

            parent = self.svg.get_current_layer()
            color = '#000000'
            direction = None
            months = {} #full day of each 1st in a month
            hours = {} # one hour over the whole year


            self.new_circle(parent, self.offset_x,self.offset_y, color)
            x = self.offset_x
            y = self.offset_y
            l = self.length
            d = l * math.sin(math.pi / 4) # length l in 45° angle
            self.new_path(parent, [(x     , y),
                                   (x, y + l)], color)

            self.new_text(parent, None, x + 3, y + l, f"Shadow stick length", anchor='start')

            self.new_path(parent, [(x + d, y + d),
                                   (x    , y),
                                   (x + d, y - d)], color, close=False)

            #self.new_path(parent, [(x + d, y + d),
            #                       (x + 2 * d, y ),
            #                       (x + d + l, y - d)], color, close=True)

            #self.new_path(parent, [(x + d + l, y - d),
            #                       (x + d, y - d),
            #                       (x + d, y - 2 * d)], color, close=True)

            with open(self.options.csvfile) as csvfile:
                reader = csv.DictReader(csvfile)
                date_col = reader.fieldnames[0]
                year = None
                for row in reader:
                    for h in range(self.day_start, self.day_end + 1):
                        try:
                            az_csv = float(row[f"A {h:02d}:00:00"])
                            el_csv = float(row[f"E {h:02d}:00:00"])
                        except ValueError:
                            continue
                        x,y = self.map_coords(self.length, el_csv, az_csv)
                        if abs(x-self.offset_x) > self.bounding_box:
                            continue
                        if abs(y-self.offset_y) > self.bounding_box:
                            continue

                        date_txt = row[date_col]

                        hrs = hours.get(h,[])
                        hrs.append((x,y))
                        hours[h] = hrs

                        date = datetime.datetime.strptime(date_txt, '%Y-%m-%d')

                        if year is None:
                            year = date.year
                        # only draw dates of one year
                        if year != date.year:
                            continue

                        anchor = 'start'
                        if date.month < 4:
                            anchor = 'end'
                        if date.month >= 7 and date.month <= 9:
                            anchor = 'end'

                        if date.day == 1:
                            #self.new_text(parent, None, x,y, date_txt, anchor)
                            #self.new_circle(parent, x,y, color)

                            m = months.get(date.month,[])
                            m.append((x,y))
                            months[date.month] = m


            for m in months:
                if m < 7:
                    color = '#000000'
                    anchor = 'end'
                    offset = -3
                else:
                    color = '#FF0000'
                    anchor = 'start'
                    offset = +3

                self.new_path(parent, months[m], color, f"Month {m}")
                coord = months[m][0]
                self.new_text(parent, None, coord[0] + offset, coord[1], f"{calendar.month_name[m]}", anchor=anchor)
                for p in months[m]:
                    self.new_circle(parent, p[0], p[1], color)

            for h in hours:
                self.new_path(parent, hours[h], '#FF0000', f"{h}h")
                coord = hours[h][0]
                self.new_text(parent, None, coord[0] - 3, coord[1]-3, f"{h:02d}:00", anchor='end')
                


if __name__ == '__main__':
        e = Sundial()
        e.run()

