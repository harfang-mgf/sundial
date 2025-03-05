# 
# trace of a shadow in form of a sundial
# 
# source : OMBRE.C / Markus Fischer, Genève, décembre 1993
# 
# version 1.1 – ported to python, February 2025
#   mimic c language, awkward
#
# version 1.2 – pythonification of the code
#   elimination of global variables, simplifications, etc.
#   added SVG output, replacing GLE from the c original
# 
__version__ = '1.3 2025-03-05'

usage: str = """
ombre - draws a sundial  (Markus Fischer, Feb. 2025)
parameters:
    l <ang>  latitude ( + : north ; - : south )
    g <ang>  longitude ( + : west ; - : east )
    o <ang>  orientation ( 0 : south, +90° : west ; -90° : east )
    p <ang>  slope of the wall ( 0 : flat ; 90° : vertical )
    z <val>  time zone
    d <val>  perpendicular distance of the style (sets origin)
    s <val>  length of the style (sets origin)
    h <val>  horizontal shift of origin
    v <val>  vertical shift of origin
    H <val>  width of the wall (origin defaults to left)
    V <val>  height of the wall (origin defaults to bottom)
    e <int>  scale (defaults to 1 unit = 200 pixel)
    n <nam>  writes data files using a base name (max. 4 chars)
    c        sets all values to zero
    x|i <#>  excludes|includes one of the six calculations:
             0|'txt', 1|'std', 2|'ext', 5|'hyp', 4|'teq', 5|'sha'
    k        'nocturnal' dial (i.e. for a transparent earth :)
    b        supress bold, e.g. highlights (lines and files)
    <ang>    all angles are entered in degrees, decimal or deg:min:sec
             ( -l46.50  ==  -l 46:30  ==  -l 46°30'00.00 )
    <val>    distances in any consistent unit (but see -e)
"""

import sys, os, math
from math import pi, sin, asin, cos, acos, tan, atan, atan2, \
    radians as rad, degrees as deg
from datetime import datetime
from dataclasses import dataclass
from typing import TextIO

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame as pg

# contains the equation of time for the year 2000
# and a quick implementation of c's 'struct' data containers
from sundata import sunpos, tropic, kwvals, struct

# from etc.solar_calculator import sunpos as sun, jd2000


# global constants and methods          #TAG global
tim = lambda        a: a*12/pi          # convert rad -> 24 hours
raddm = lambda      d,m: rad(d+m/60)    # degrees and minutes to rad
ON: bool =          True
OFF: bool =         False
SMALL: float =      1e-10               # very small number
LARGE: float =      1e+10               # very large number
FOURDEG: float =    pi/45.0             # four degrees in radians
debug: bool =       False               # displays S calculations only

# sundial parameters, static data class
class S():                              #TAG S
    # used in getargs():
    @classmethod                        # access attribute by name
    def get(cls, attr: str) -> any:
        return getattr(cls, attr)
    @classmethod                        # set attribute by name
    def set(cls, attr: str, val: any):
        setattr(cls, attr, val)

    # geographic parameters
    lat: float =    +0.80663            # latitude of the sundial
    lon: float =    -0.10734            # longitude of the sundial
    ori: float =    +0.5236             # orientation of the wall
    slo: float =    +1.5708             # slope of the wall
    zon: float =    +1.0                # time zone
    # calculations
    tdi: float =    0.0                 # time difference legal-mean solar
    tdirad: float = 0.0                 # in radians (12h==pi)
    rot: float =    0.0                 # rotation of the dial
    lam: float =    0.0                 # equiv. latitude of the wall
    lom: float =    0.0                 # equiv. rel. longitude " " "
    # gnomon geometry
    perp: int =     OFF                 # perpendicular style
    style: float =  1.0                 # length of the style
    hsty: float =   0.0                 # height (or perpendicular length)
    lsty: float =   0.0                 # base length
    # dial geometry
    totx: float =   3.7                 # width of the sundial
    toty: float =   2.0                 # height of the sundial
    addx: float =   -0.3               # gnomon horizontal offset
    addy: float =   1.0                 # gnomon vertical offset
    tmpx: float =   0.0                 # temp additional horiz. offset
    tmpy: float =   0.0                 # temp additional vert. offset
    tmpz: float =   0.0                 # temp additional perp. offset
    # graphical options
    noct: bool =    OFF                 # show nocturnal lines
    mark: bool =    OFF                 # displays a marker
    dohigh: bool =  ON                  # highlighting

    @staticmethod # TODO
    def init():
        "Perform calculations of sundial parameters"

        # The program really deals only with horizontal sundials. For mural dials,
        # the latitude and longitude where the same sundial would be horizontal are
        # calculated.
        # Spherical trigonometry is confusing…

        # find the equivalent latitude and orientation of the wall
        if (S.slo):
            S.lam = asin( cos(S.slo)*sin(S.lat) - sin(S.slo)*cos(S.lat)*cos(S.ori) )
            S.lom = atan2( sin(S.ori), cos(S.lat)/tan(S.slo) + sin(S.lat)*cos(S.ori) )
            S.rot = atan2( sin(S.ori), cos(S.ori)*cos(S.slo) + sin(S.slo)*tan(S.lat) )
        else:
            S.lam = S.lat
            S.lom = 0
            S.rot = S.ori

        # The logical coordinates system has its origin (0,0) below the tip of the
        # style (the extremity of the gnomon) and follows mathematical convention
        # (upwards y axis).
        # For the graphical output, the origin is set at the center of the display
        # area and is adjusted by the wall parameters (-H, -V) and by the offset
        # parameters (-h, -v).
        # The final origin is determined by calculation from the basis of the style
        # or set by the -d parameter, giving the height of the gnomon instead of
        # the length of the style. (See S.perp below for 'perpendicular')
        # The parameters addx and addy contain the offset from the center.

        # deal with style
        if (not S.perp):
            # base calculations on style length
            S.hsty = abs( sin(S.lam) * S.style )
            S.lsty = abs( cos(S.lam) * S.style ) * (-1 if S.lam<0 else 1)
            S.addx -= sin(S.rot) * S.lsty
            S.addy += cos(S.rot) * S.lsty
        if (S.hsty < SMALL):
            # this failed: auto-switch to perpendicular
            S.hsty = 1.0
            S.perp = True
        if (S.perp):
            # base calculations on gnomon height
            S.style = abs(S.hsty / (sin(S.lam) + SMALL));
            S.lsty = S.hsty / (tan(S.lam) + SMALL);

        # deal with time
        S.tdi = S.zon + tim(S.lon)
        S.tdirad = S.tdi/12*pi

    @staticmethod
    def height() -> float:           
        "total hsty, with adjustments"
        return S.hsty + S.tmpz
    @staticmethod
    def ah(hour: float) -> float:  # hour angle for given hangle
        "legal hour angle (rad)"
        return rad((hour - S.tdi - 12.0) * 15)
    @staticmethod
    def set_tmp(x: float, y: float, z: float):
        "displace the tip of the gnomon"
        S.tmpx = x ; S.tmpy = y ; S.tmpz = z
    @staticmethod
    def clear_tmp() -> None:
        "clears the temporaray displacement"
        S.tmpx = S.tmpy = S.tmpz = 0.0


# Graphic state, static data class
class G():                              #TAG G

    screen: bool =  True                # default mode
    tofile: str =   ''                  # base name of the output file
    scale: int =    200                 # pixels per base unit
    fscrn: bool =   OFF                 # fullscreen mode
    maxx: int =     1000                # horizontal pixels
    maxy: int =     1000                # vertical pixels
    pen: bool =     OFF                 # plotter mode

    background: int|str|None            # background color
    color: int|str|None                 # line color
    style: int                          # line style
    width: int                          # line width

    @dataclass
    class LParam():                     # line parameters
        on: int                         # drawing it?
        color: str                      # normal color
        cbold: str                      # bold (highlight) color
        style: int = 0                  # line style
        width: int = 1                  # line width

    # # Colors for pygame, using color names
    # lines: dict[LParam] = dict(
    #     _pg = LParam(True, 'black', 'white'),
    #     txt = LParam(True, 'darkgray', 'white'),
    #     std = LParam(True, 'green4', 'green1', 1),
    #     ext = LParam(True, 'blue4', 'blue3', 1),
    #     hyp = LParam(True, 'blue4', 'blue3', 1),
    #     teq = LParam(True, 'red4', 'red2', 0, 3),
    #     sha = LParam(False, 'white', 'white'),
    # )

    # CGA 16-color palette
    lines: dict[LParam] = dict(
        _pg = LParam(True,  '#000000', '#FFFFFF'),
        txt = LParam(True,  '#AAAAAA', '#FFFFFF'),
        std = LParam(True,  '#00AA00', '#55FF55', 1),
        ext = LParam(True,  '#0000AA', '#5555FF', 1),
        hyp = LParam(True,  '#0000AA', '#5555FF', 1),
        teq = LParam(True,  '#AA0000', '#FF5555', 0, 3),
        sha = LParam(False, '#AA5500', '#FFFF55'),
    )

    # black-and white scheme
    lines: dict[LParam] = dict(
        _pg = LParam(True,  None,     'black'),
        txt = LParam(True,  'gray', 'black'),
        std = LParam(True,  'gray', 'black', 1),
        ext = LParam(True,  'gray', 'black', 1),
        hyp = LParam(True,  'gray', 'black', 1),
        teq = LParam(True,  'gray', 'gray', 0, 3),
        sha = LParam(False, 'gray', 'black'),
    )

    active: str = '_pg'                 # active tag
    @classmethod
    def activate(cls, tag: str = '_pg') -> bool:
        "activates attributes for the given line type"
        line = cls.lines[tag]
        if tag == '_pg':
            cls.background = line.color
            cls.color = line.cbold
        else:
            cls.color = line.color
        cls.style = line.style
        cls.width = line.width
        cls.active = tag
        return line.on


# common interface, depending on implementation
class GraphicInterface():
    "methods used to draw a sundial, on screen or to a file"
    def init(self) -> None: pass
    def group_start(self) -> None: pass
    def group_end(self) -> None: pass
    def line(self, x1: int, y1: int, x2: int, y2: int) -> None: pass
    def line_to(self, x: int, y: int) -> None:  pass
    def line_end(self) -> None: pass
    def rect(self, x: int, y: int, w: int, h: int) -> None: pass
    def circle(self, cx: int, cy: int, r: int) -> None: pass
    def marker(self, mx: int, my: int, color: str = '', size: int = 3) -> None: pass
    def textbox(self, px: int, py: int, text: list[str]|str) -> None: pass
    def redraw(self) -> None: pass
    def idle(self) -> None: pass
    def close(self) -> None: pass


# on-screen interface, using pygame
class CGA_interface(GraphicInterface): #TAG CGA
    "uses the pygame library for old-school screen management"

    def __init__(self):
        self.last_pos: tuple[float, float] = (0.0, 0.0)
        pg.init()
        if (G.fscrn):
            pg.display.set_mode()
            pg.display.toggle_fullscreen()
            G.maxx, G.maxy = pg.display.get_window_size()
        else:
            pg.display.set_mode((G.maxx,G.maxy))
        self.screen: pg.Surface = pg.display.get_surface()
        self.screen.fill(G.background or 'white')
        self.font: pg.font = pg.font.SysFont('consolas', 16)
        pg.display.set_caption("Sundial")
        pg.display.flip()

    @staticmethod
    def gx(x: int):
        "logical coordinates to screen coordinates"
        return (G.maxx+1)//2+1 + G.scale*(x + S.addx + S.tmpx)
    @staticmethod
    def gy(y: int):
        "logical coordinates to screen coordinates"
        return (G.maxy+1)//2+1 - G.scale*(y + S.addy + S.tmpy)

    def line(self, x1, y1, x2, y2):
        "draw.line(), using current G attributes"
        p1 = self.gx(x1), self.gy(y1) ; p2 = self.gx(x2), self.gy(y2)
        pg.draw.line(self.screen, G.color, p1, p2, G.width)
        self.last_pos = p2

    def line_to(self, x, y):
        "draw.line() from the last coordinates"
        pt = self.gx(x), self.gy(y)
        if (G.pen):
            pg.draw.line(self.screen, G.color, self.last_pos, pt, G.width)
        self.last_pos = pt
        G.pen = ON

    def rect(self, x: int, y: int, w: int, h: int):
        "draw.rect(), using current G attributes"
        # position must be on the top left, sizes must be positive
        top_left = self.gx(x), self.gy(y + h)
        size = G.scale*(w), G.scale*(h)
        pg.draw.rect(self.screen, G.color, (top_left, size), G.width)

    def circle(self, cx: int, cy: int, r: int):
        "draw.circle(), using current G attributes"
        pt = self.gx(cx), self.gy(cy)
        pg.draw.circle(self.screen, G.color, pt, r, G.width)

    def marker(self, mx: int, my: int, color: str = '', size: int = 3):
        "draw.circle(), filled, with optional color override"
        pt = self.gx(mx), self.gy(my)
        if not color: color = G.color
        pg.draw.circle(self.screen, color, pt, size, 0)

    def textbox(self, px: int, py: int, text: list[str]|str):
        "renders text on a new surface and blits it on the screen"
        if isinstance(text, list):
            lines = text.copy()
        else:
            lines = text.split('\n')
        labels: list[pg.Rect] = []
        width: int = 0
        height: int = 0
        line_height = 0
        for line in lines:
            label: pg.Surface = self.font.render(line, True, G.color)
            if not line_height: line_height = label.get_height()
            if line:
                if label.get_width() > width: width = label.get_width()
                height += line_height
            else:
                label = None
                height += line_height//3
            labels += [label]
        size = width+6, height+6
        box = pg.Surface(size).convert()
        box.fill(G.background or 'white')
        height = 3
        for i, label in enumerate(labels):
            if label:
                box.blit(label, label.get_rect(topleft=(3, height)))
                height += line_height
            else:
                height += line_height//3
        pg.draw.rect(box, G.color, ((0,0), size), 1)
        self.screen.blit(box, box.get_rect(topleft=(px, py)))

    def redraw(self): pg.display.flip()

    def idle(self):
        "waits for user input (any key) before resuming, or closing"
        pg.display.flip()
        try:
            while True:
                event = pg.event.wait()
                if event.type == pg.QUIT:
                    sys.exit( 1 )
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE or event.unicode == "q":
                        sys.exit( 1 )
                    else:
                        break
                pg.display.flip()
        finally: return

    def close(self):
        "closes the window and releases all memory"
        pg.display.quit()


# text output, SVG format
class SVG_interface(GraphicInterface):  #TAG SVG
    svg: TextIO

    def __init__(self):
        self._poly: list[str] = []
        self.basename = G.tofile
        self.filename = self.basename + '.svg'
        mypath = os.path.dirname(__file__)
        path = os.path.join(mypath, self.filename)
        self.svg: TextIO = open(path, 'wt')
        print('<svg xmlns="http://www.w3.org/2000/svg"'
            f' width="{G.maxx}" height="{G.maxy}" >',
            file=self.svg)
        if G.background:
            print(f'<rect'
                f' x="0" y="0" width="{G.maxx}" height="{G.maxy}"'
                f' fill="{G.background}"'
                ' />', file=self.svg)

    @staticmethod
    def gx(x: int) -> int:
        "converts from logical to graphic output coordinates"
        return round((G.maxx+1)//2+1 + G.scale*(x + S.addx + S.tmpx), 1)
    @staticmethod
    def gy(y: int) -> int:
        "converts from logical to graphic output coordinates"
        return round((G.maxy+1)//2+1 - G.scale*(y + S.addy + S.tmpy), 1)

    def group_start(self) -> None:
        "start an svg <group> with common attibutes"
        print(f'<g class="{G.active}"'
            f' stroke="{G.color}" stroke-width="{G.width}" fill="none"'
            f' >', file=self.svg)

    def group_end(self) -> None:
        "end the current svg <group>"
        print(f'</g><!-- {G.active} -->', file=self.svg)

    def line(self, x1: int, y1: int, x2: int, y2: int):
        "svg <line/> using current default attributes"
        print('<line'
            f' x1="{self.gx(x1)}" y1="{self.gy(y1)}"'
            f' x2="{self.gx(x2)}" y2="{self.gy(y2)}"'
            f' />', file=self.svg)

    def line_to(self, x: int, y: int):
        "starts or continues an svg <polyline... (open tag!)"
        if (not G.pen):
            self._poly = [f'<polyline points="' ]
        self._poly += [f'{self.gx(x)},{self.gy(y)}']
        G.pen = ON

    def line_end(self):
        "ends the current <polyline> tag"
        if len(self._poly) > 2:
            self._poly += ['" />']
            print(' '.join(self._poly), file=self.svg)
            self._poly = []

    def rect(self, x: int, y: int, w: int, h: int):
        "simple svg <rect/> with current attributes"
        # position must be on the top left, sizes must be positive
        x, y = self.gx(x), self.gy(y + h)
        w, h = G.scale*(w), G.scale*(h)
        print('<rect'
            f' x="{x}" y="{y}" width="{w}" height="{h}"'
            f' stroke="{G.color}" stroke-width="{G.width}"'
            f' fill="none"'
            f' />', file=self.svg)

    def circle(self, cx: int, cy: int, r: int):
        "simplle svg <circle/>, with current attributes"
        print('<circle '
            f'cx="{self.gx(cx)}" cy="{self.gy(cy)}" r="{r}"'
            f' stroke="{G.color}" stroke-width="{G.width}"'
            f' fill="none"'
            f' />', file=self.svg)

    def marker(self, mx: int, my: int, color: str = '', size: int = 3):
        "small filled <circle/> with optional color override"
        if not color: color = G.color
        print('<circle '
            f'cx="{self.gx(mx)}" cy="{self.gy(my)}" r="{size}"'
            f' fill="{color}"'
            f' />', file=self.svg)

    def textbox(self, px: int, py: int, text: list[str]|str) -> None:
        "multi-line textbox, stacked <text> tags"
        if isinstance(text, list):
            lines = text.copy()
        else:
            lines = text.split('\n')
        print('<g class="textbox"'
            f' style="font-family:consolas,monospace;font-size:16px"'
            f' transform="translate({px},{py})"'
            f' fill="{G.color}" stroke="none"'
            f' >', file=self.svg)
        height: int = 16
        for line in lines:
            if line:
                safe = line.replace(' ', '\xa0')
                print(f'<text x="3" y="{height}">{safe}</text>', file=self.svg)
                height += 16
            else:
                height +=5
        print(f'</g><!-- textbox -->', file=self.svg)

    def close(self):
        "sign-out and close file"
        stamp = datetime.now().astimezone().replace(microsecond=0).isoformat()
        print('</svg>', file=self.svg)
        print(f"<!-- sundial, by 'ombre' {stamp} (°v°) -->", file=self.svg)
        self.svg.close()
        print(f"output: {self.filename} at {stamp}")


# shap: list[dict] = struct
shape: list[kwvals] = struct(
    (  'x',  'y',  'd'),
    [ # octahedron
    (  0.0,  0.0,  0.1 ),
    ( -0.1,  0.0,  0.0 ),
    (  0.0,  0.0, -0.1 ),
    (  0.1,  0.0,  0.0 ),
    (  0.0,  0.1,  0.0 ),
    ( -0.1,  0.0,  0.0 ),
    (  0.0, -0.1,  0.0 ),
    (  0.1,  0.0,  0.0 ),
    (  0.0,  0.0,  0.1 ),
    (  0.0,  0.1,  0.0 ),
    (  0.0,  0.0, -0.1 ),
    (  0.0, -0.1,  0.0 ),
    (  0.0,  0.0,  0.1 ),
    # [ # wall
    # ( -0.5,  0.0,  0.0 ),
    # (  0.0,  0.0,  0.0 ),
    # (  0.0, -0.5,  0.0 ),
    # (  0.0,  0.0,  0.0 ),
    # (  0.0,  0.0,  0.1 ),
    # ( -0.5,  0.0,  0.1 ),
    # (  0.0,  0.0,  0.1 ),
    # (  0.0, -0.5,  0.1 ),
    # (  0.0,  0.0,  0.1 ),
    # [ # square
    # ( -0.1, -0.1,  0.1 ),
    # ( -0.1,  0.1,  0.1 ),
    # (  0.1,  0.1,  0.1 ),
    # (  0.1, -0.1,  0.1 ),
    # ( -0.1, -0.1,  0.1 ),
    # ( -0.1, -0.1, -0.1 ),
    # ( -0.1,  0.1, -0.1 ),
    # (  0.1,  0.1, -0.1 ),
    # (  0.1, -0.1, -0.1 ),
    # ( -0.1, -0.1, -0.1 ),
    ])

def go_to_work():                       #TAG go_to_work()

    def startof_line ( line_tag: str ):
        if G.activate(line_tag):
            GRI.group_start()
            return True
        return False

    def endof_line() -> None:
        GRI.group_end()
        GRI.redraw()

    def highlight ( test: int ) -> None:
        if (S.dohigh and test):
            G.color = G.lines[G.active].cbold
        else:
            G.color = G.lines[G.active].color

    def penup () -> None:
        G.pen = OFF
        GRI.line_end()

    def data_point ( angle: float, distance: float, from_base: bool = False ):

        if (abs(distance)*G.scale > G.maxx*10):
            return
        x: float = sin(angle) * distance
        y: float = cos(angle) * distance
        if from_base:
            x += sin(S.rot) * S.lsty
            y -= cos(S.rot) * S.lsty
        if (S.mark):
            GRI.marker( x, y, size=3 )
        else: 
            GRI.line_to( x, y )

    def shadow ( tro: float, ah: float ) -> int:

        ahm: float ; els: float ; elm: float ; ahs: float ; las: float

        ahm = ah-S.lom
        elm = asin( sin(S.lam)*sin(tro) + cos(S.lam)*cos(tro)*cos(ahm) )
        els = asin( sin(S.lat)*sin(tro) + cos(S.lat)*cos(tro)*cos(ah) )
        if (elm > 0 and (S.noct or els > 0)):
            ahs = atan2( sin(ahm), sin(S.lam)*cos(ahm) - cos(S.lam)*tan(tro) )
            las = S.height() / (tan(elm) + SMALL)
            data_point( ahs-S.rot, las )
            return ( ON )
        return ( OFF )

    G.activate()
    GRI: GraphicInterface = \
        CGA_interface() if G.screen else \
        SVG_interface()
    GRI.rect( -S.totx/2-S.addx, -S.toty/2-S.addy, S.totx, S.toty )
    GRI.circle( sin(S.rot)*S.lsty, -cos(S.rot)*S.lsty, 2 )
    GRI.circle( 0, 0, 1 )
    GRI.circle( 0, 0, 7 )
    GRI.redraw()

    # write values */
    if (startof_line( 'txt' )):
        GRI.textbox(10,10, inform())
        endof_line()

    # standard dial
    if ( startof_line( 'std' ) and abs(S.lam) > rad(0.5) ):
        for hour in range(0,25):
            highlight( hour == 12.0 )
            ah: float = S.ah(hour)
            ao = atan2( sin(ah-S.lom)*sin(S.lam), cos(ah-S.lom) ) - S.rot
            data_point( 0, 0, True )
            data_point( ao, S.lsty, True )
            penup()
        endof_line()
        print(GRI.__class__)
        # BAD better handling of highlight for SVG
        if isinstance(GRI, SVG_interface):
            ah: float = S.ah(12.0)
            ao = atan2( sin(ah-S.lom)*sin(S.lam), cos(ah-S.lom) ) - S.rot
            highlight(True)
            GRI.group_start()
            data_point( 0, 0, True )
            data_point( ao, S.lsty, True )
            penup()
            GRI.group_end()


    # extreme shadows
    if (startof_line( 'ext' )):
        for hour in (i/4 for i in range(24*4+1)): # range(0.0, 24.1, 0.25)
            
            ah: float = S.ah(hour)
            highlight( hour % 1.0 == 0.0 )
            # summer solstice
            shadow( rad(tropic), ah )

          # declination of sun set for that hour
            if (abs(S.lat) > rad(0.5) and not S.noct):
                S.noct = ON
                t = atan( -cos(ah) / tan(S.lat) )
                if (abs(t) <= rad(tropic)):
                    shadow( t, ah )
                S.noct = OFF

          # declination of first shadow on the wall for that hour
            if (abs(S.lam) > rad(0.5)):
                t = atan( -cos(ah-S.lom) / tan(S.lam) )
                if (abs(t+FOURDEG) <= rad(tropic)):
                    shadow( t+FOURDEG, ah )
                if (abs(t-FOURDEG) <= rad(tropic)):
                    shadow( t-FOURDEG, ah );

            # winter solstice
            shadow( rad(-tropic), ah )
            penup()

        endof_line()

    # conic day-lines (hyperboles, paraboles, elipse or circle...)
    if (startof_line( 'hyp' )):
        for l in range(90, 271, 30):
            highlight( l%90 == 0 )
            # time of sun-set at horiz. location of sundial
            s = - tan(rad(sunpos[l].decl)) * tan(S.lam)
            if (s < 1):
                s = acos(s) if s > -1 else pi
                # for (a = -s+pi/180 ; a <= s-pi/180 ; a += pi/90)
                a = -s+pi/180
                while a <= s-pi/180:
                    # print( rad(sunpos[l].decl), a+S.lom )
                    shadow( rad(sunpos[l].decl), a+S.lom )
                    a += pi/90
                penup()
        endof_line()

    # equation of time
    if (startof_line( 'teq' )):               #TAG teq
        for hour in range(25):
            drawing: int = OFF
            ah: float = S.ah(hour)
            highlight( hour == 12.0 )
            for l in sunpos:
                if (shadow( rad(l.decl), ah + rad(l.tequ/4) )):
                    drawing = ON
                else:
                    if (drawing):
                        penup()
                        drawing = OFF
            penup()
        endof_line()

    # # shapes ...
    # if (output_line( 'sha' )):
    #     for hour in range(25):
    #         ah: float = S.ah(hour)
    #         highlight( hour == 12.0 )
    #         for l in (sunpos[i] for i in range(0, len(sunpos), 30)):
    #             S.mark = ON
    #             shadow( rad(l.decl), ah + rad(l.tequ/4) )
    #             S.mark = OFF
    #             for pt in shape:
    #                 S.set_tmp( pt.x, pt.y, pt.d)
    #                 shadow( rad(l.decl), ah + rad(l.tequ/4) );
    #             S.clear_tmp()
    #             penup()
    #     endof_line()

    # shapes ... better
    if (startof_line( 'sha' )):
        for i in range(-3, 4):
            t = asin( sin(i*pi/6.0) * sin(rad(tropic)) );
            # time of sun-set */
            s = - tan(t) * tan(S.lam)
            if (s < 1):
                s = acos(s) if (s > -1) else pi
                for hour in range(25):
                    ah: float = S.ah(hour)
                    if (-s <= ah-S.lom <= s):
                        S.mark = ON
                        shadow( t+SMALL, ah )
                        for pt in shape:
                            S.set_tmp(pt.x, pt.y, pt.d)
                            shadow( t+SMALL, ah )
                        S.mark = OFF
                        for pt in shape:
                            S.set_tmp( pt.x, pt.y, pt.d )
                            shadow( t+SMALL, ah )
                        S.clear_tmp
                        penup()
        endof_line()

    GRI.idle()
    GRI.close()
# end go_to_work()


def main():                               #TAG main()

    hour: float                         # hour of the day
    ah: float                           # ... and angles
    ao: float                           # angle style-shadow
    i: int ; l: int
    a: float ; s: float ; t:float

    get_args()
    S.init()

    if (G.scale < 1):
        G.scale = 100

    if debug:
        print('\n'.join(inform()))
        print('\n-------------',
            f"totx = {S.totx:.1f}",
            f"toty = {S.toty:.1f}",
            f"addx = {S.addx:.1f}",
            f"addy = {S.addy:.1f}",
            f"rot = {deg(S.rot):.1f}",
            f"sin = {sin(S.rot):.1f}",
            f"cos = {cos(S.rot):.1f}",
            sep = '\n')
        exit( 0 )


    # end • all lines
    go_to_work()

# end main()

# argument parser, ported from c, could probably be pythonized a bit more
def get_args() -> None:                 #TAG get_args()
    "handles command-line arguments"
    
    from enum import Enum

    def atof(number:str) -> float:
        try:    return float(number)
        except: return 0
    
    def toggle(arg: str, state: bool) -> bool:
        "expects one of : '-?' ; '-?+' ; '-?-'"
        return True if arg[2:]=='+' else False if arg[2:]=='-' else not state

    X = Enum('next', ['NONE', 'ANG', 'TIM', 'VAL', 'INT', 'STR', 'LIN'])
    expect = X.NONE
    val: str                            # serves as a variable pointer (!)
    mode: int
    m: float
    i: int

    for a in sys.argv[1:]:
        if expect == X.NONE and (a[0] == '-' or a[0] == '/'):
            match a[1:2]:
                case '?' : print(usage) ; exit( 0 )
                case '-' : global debug ; debug = True
                case 'c' : # removes default Geneva demo values
                    S.lat = S.lon = S.ori = S.slo = S.zon = 0.0
                    S.totx = S.toty = S.addx = S.addy = 0.0
                case 'l' : expect = X.ANG ; val = 'lat'
                case 'g' : expect = X.ANG ; val = 'lon'
                case 'o' : expect = X.ANG ; val = 'ori'
                case 'p' : expect = X.ANG ; val = 'slo'
                case 'z' : expect = X.TIM ; val = 'zon'
                case 'd' : expect = X.VAL ; val = 'hsty' ; S.perp = ON
                case 's' : expect = X.VAL ; val = 'style'; S.perp = OFF
                case 'h' : expect = X.VAL ; val = 'addx'
                case 'v' : expect = X.VAL ; val = 'addy'
                case 'H' : expect = X.VAL ; val = 'totx'
                case 'V' : expect = X.VAL ; val = 'toty'

                case 'e' : expect = X.INT ; val = 'scale'
                case 'n' : expect = X.STR ; val = 'name'
                case 'x' : expect = X.LIN; mode = OFF
                case 'i' : expect = X.LIN; mode = ON

                case 'k' : S.noct = toggle(a, S.noct)
                case 'b' : S.dohigh = toggle(a, S.dohigh)
                case 'f' : G.fscrn = toggle(a, G.fscrn)
                case _ :
                    print( "unknown argument {} (-? for help)".format(a),
                           file=sys.stderr )
                    exit( 1 )
            a = a[2:]

        if (a):
            match (expect) :
                case X.NONE :
                    if a not in '+-':
                        print("don't know what to do with {} (-? for help)\n"
                            .format(a), file=sys.stderr )
                        exit( 1 )
                case X.ANG | X.TIM :
                    ang = 0.0
                    sign = +1
                    if a[0] in '+-':
                        if a[0] == '-': sign = -1
                        a = a[1:]
                    m = 1.0
                    while a:
                        i = 0
                        while i<len(a) and a[i] in '0123456789.': i += 1
                        ang += atof(a[:i]) * m
                        m = m/60
                        a = a[i+1:]
                    if expect == X.ANG: ang = rad(ang)
                    S.set(val, sign * ang)
                case X.VAL : S.set(val, atof(a))
                case X.INT : G.scale = int(atof(a))
                case X.STR : G.tofile = a ; G.screen = False
                case X.LIN :
                    if a in G.lines:
                        G.lines[a].on = mode
                    else:
                        i = int(atof(a))
                        if (i < 0 or i >= len(G.lines)):
                            print( "can't {} {}".format(
                                "include" if mode else "exclude",
                                a ), file=sys.stderr)
                            exit( 1 )
                        G.lines[list(G.lines)[i]].on = mode
            expect = X.NONE;

    if (expect != X.NONE):
        print( "unexpected end of args after {}".format(sys.argv[-1]),
            file=sys.stderr )
        exit( 1 )

# end get_args()



def inform() -> list[str]:

    def to_dms(ang: float) -> tuple[int,int,int]:
        sign = 1
        if ang<0: sign = -1; ang=-ang
        ang = int(round(deg(ang) * 3600))
        return sign * (ang // 3600), ang // 60 % 60, ang % 60    

    def to_dm(ang: float) -> tuple[int,int]:
        sign = 1
        if ang<0: sign = -1; ang=-ang
        ang = int(round(deg(ang) * 60))
        return sign * (ang // 60), ang % 60    

    def to_hm(ang: float) -> tuple[int,int]:
        sign = 1
        if ang<0: sign = -1; ang=-ang
        ang = int(round(tim(ang) * 60))
        return sign * (ang // 60), ang % 60    

    # DONE rewrite inform
        
    info: list[str] = [   # f"SCALE: {G.scale}","",
        "Lat {:4d}°{:02d}'".format(*to_dm(S.lat)),
        ]
    if (S.lon): info += [
        "Lon {:4d}°{:02d}'".format(*to_dm(S.lon)),
        "zone {:+3d}:{:02d}".format(*to_hm(S.zon/12*pi)),
        "diff {:+3d}:{:02d}".format(*to_hm(S.tdi/12*pi)),
        ]
    if (S.slo): info += [
        "",
        "ori {:+4d}°{:02d}'".format(*to_dm(S.ori)),
        "slo {:+4d}°{:02d}'".format(*to_dm(S.slo)),
        "",
        "rot {:+4d}°{:02d}'".format(*to_dm(S.rot)),
        "lam {:+4d}°{:02d}'".format(*to_dm(S.lam)),
        "lom {:+4d}°{:02d}'".format(*to_dm(S.lom)),
        "diff {:+3d}°{:02d}".format(*to_hm(S.lom)),
        ]
    if (S.style < LARGE): info += [
        "",
        "styl{:7.2f}".format(S.style),
        "hsty{:7.2f}".format(S.hsty),
        ]
    if (S.lsty < LARGE): info += [
        "lsty{:7.2f}".format(S.lsty),
        ]
    return info

# end inform()

def draw_sundial(
    latitude: float = 46.2074,
    longitude: float = 6.1559,
    orientation: float = 12,
    slope: float = 90,
    *,
    time_zone: float = -1,
    style_length: float = 1.0,
    gnomon_height: float = 0,
    add_x: float = 0.0,
    add_y: float = 0.0,
    wall_width: float = 0,
    wall_height: float = 0,
    nocturnal: bool = False,
    use_bold: bool = True,
    scale: float = 200,
    draw_text: bool = True,
    draw_standard: bool = True,
    draw_extremes: bool = True,
    draw_traces: bool = True,
    draw_equation: bool = True,
    draw_special: bool = False,
    full_screen: bool = False,
    file_name: str|None = None,
    ) -> None:
    "all angles in degrees"
    S.lat = rad(latitude)
    S.lon = rad(longitude)
    S.ori = rad(orientation)
    S.slo = rad(slope)
    S.zon = time_zone
    S.style = style_length
    if gnomon_height:
        S.perp = True
        S.hsty = gnomon_height
    else:
        S.perp = False
    S.addx = add_x
    S.addy = add_y
    S.totx = wall_width
    S.toty = wall_height
    S.noct = nocturnal
    S.dohigh = use_bold
    G.scale = scale
    G.lines['txt'].on = draw_text
    G.lines['std'].on = draw_standard
    G.lines['ext'].on = draw_extremes
    G.lines['hyp'].on = draw_traces
    G.lines['teq'].on = draw_equation
    G.lines['sha'].on = draw_special
    G.fscrn = full_screen
    if file_name is not None:
        G.tofile = file_name
        G.screen = False
    main()
