""" solar ephemerides

Implements ephemerides(), a pandas dataframe normally for a year (same time),
or a single day.

It is a much faster version than its predecessor, solar_calculator.py v.1.0.
On the downside, the formulas have become horribly unreadable!

Source for all computations:
**Global Monitoring Laboratory**
» U.S. Department of Commerce
» National Oceanic & Atmospheric Administration
» NOAA Research
retrieved from https://gml.noaa.gov/grad/solcalc/
downloadable Excel sheets with detailed calculations

The function computes and returns a dataframe of detailed astronomical data,
resuting in the precise solar elevation and azimuth in degrees.
Arguments:
    date: datetime, should be time zone aware, defaults to UTC
    latitude, longitude: decimal angles in degrees (plus for N and E)
    timezone: in hours, used only for sunrise in local time and the like
    frame: yearly, monthly, or daily

Markus G Fischer, 2025-06-03, version 1.0 beta
"""
__version__ = "v1.0.beta"

import pandas as pd ; from pandas import DataFrame
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Literal
UTC = timezone(timedelta(0))

col_labels: dict[str: str] = dict(
    jd    = "j2000 day",
    jc    = "julian century",
    gmls  = "geom mean long sun [°]",
    gmas  = "geom mean anom sun [°]",
    eceo  = "Eccent Earth Orbit",
    seqc  = "Sun Eq of Ctr",
    stl   = "sun true long [°]",
    sta   = "sun true anom [°]",
    srv   = "sun rad vector (AUs)",
    sal   = "sun app long [°]",
    moe   = "mean obliq ecliptic [°]",
    oec   = "obliq corr [°]",
    srta  = "sun rt ascen [°]",
    sdec  = "sun declin [°]",
    vary  = "var y",
    eqti  = "eq of time [minutes]",
    hasr  = "ha sunrise [°]",
    noon  = "solar noon [lst]",
    rise  = "sunrise time [lst]",
    sset  = "sunset time [lst]",
    slid  = "sunlight duration [min]",
    tsti  = "true solar time [min]",
    hang  = "hour angle [°]",
    szea  = "solar zenith angle [°]",
    sela  = "solar elevation angle [°]",
    # aare  = "approx atmospheric refraction [°]",
    # selc  = "solar elevation corrected for atm refraction [°]",
    saza  = "solar azimuth angle (deg cw from N) [°]",
)

def ephemerides(
    date: datetime,
    latitude: float,
    longitude: float,
    frame: Literal['year', 'month', 'day']
    ) -> DataFrame:
    "date shouls be TZ aware, lat. and lon. are in degrees"

    d_zone = date.tzinfo or UTC
    # if d_zone is None: d_zone = UTC
    tz = d_zone.utcoffset(date).total_seconds()/3600
    match frame:
        case 'year':
            d_first = datetime(date.year, 1, 1, 12)
            d_last = datetime(date.year, 12, 31, 12)
            d_freq = timedelta(days=1)
        case 'month':
            d_first = datetime(date.year, date.month, 1, 12)
            d_last = d_first + timedelta(42)
            d_last = d_last - timedelta(d_last.day)
            d_freq = timedelta(1)
        case 'day':
            d_first = datetime(date.year, date.month, date.day, 0)
            d_last = d_first + timedelta(hours=23, minutes=59)
            d_freq = timedelta(minutes=10)
        case _:
            return None

    index = pd.date_range(d_first, d_last, tz=d_zone, freq=d_freq, name="datetime")
    ephem = pd.DataFrame(index)
    ephem['jd'] = ephem.datetime.astype(int).div(1e9).subtract(946_728_000.0).div(86400)
    ephem['jc'] = ephem.jd.div(36525)
    ephem['gmls'] = ephem.jc.multiply(0.0003032).add(36000.76983).multiply(ephem.jc).add(280.46646).mod(360)
    ephem['gmas'] = ephem.jc.multiply(-0.0001537).add(35999.05029).multiply(ephem.jc).add(357.52911)
    ephem['eceo'] = ephem.jc.multiply(0.0000001267).add(0.000042037).multiply(-ephem.jc).add(0.016708634)
    ephem['seqc'] = np.add(np.add(
        np.multiply(np.sin(np.deg2rad(ephem.gmas)), ephem.jc.multiply(0.000014).add(0.004817).multiply(-ephem.jc).add(1.914602)),
        np.multiply(np.sin(np.multiply(2, np.deg2rad(ephem.gmas))), ephem.jc.multiply(-0.000101).add(0.019993))),
        np.multiply(np.sin(np.multiply(3, np.deg2rad(ephem.gmas))), 0.000289)
        )
    ephem['stl'] = ephem.gmls.add(ephem.seqc)
    ephem['sta'] = ephem.gmas.add(ephem.seqc)
    ephem['srv'] = ephem.eceo.pow(2).multiply(-1).add(1).multiply(1.000001018).div(ephem.eceo.multiply(np.cos(np.deg2rad(ephem.sta))).add(1))
    ephem['sal'] = ephem.stl.subtract(0.00569).subtract(np.multiply(0.00478, np.sin(np.deg2rad(ephem.jc.multiply(-1934.136).add(125.04)))))
    ephem['moe'] = ephem.jc.multiply(-0.001813).add(0.00059).multiply(ephem.jc).add(46.815).multiply(-ephem.jc).add(21.448).div(60).add(26).div(60).add(23)
    ephem['oec'] = ephem.moe.add(np.multiply(0.00256, np.cos(np.deg2rad(ephem.jc.multiply(-1934.136).add(125.04)))))
    ephem['srta'] = np.rad2deg(np.atan2(np.multiply(np.cos(np.deg2rad(ephem.oec)), np.sin(np.deg2rad(ephem.sal))), np.cos(np.deg2rad(ephem.sal))))
    ephem['sdec'] = np.rad2deg(np.asin(np.multiply(np.sin(np.deg2rad(ephem.oec)), np.sin(np.deg2rad(ephem.sal)))))
    ephem['vary'] = np.pow(np.tan(np.divide(np.deg2rad(ephem.oec), 2)), 2)
    ephem['eqti'] = np.multiply(4, np.degrees(np.add(np.add(np.add(np.add(
        ephem.vary.multiply(np.sin(np.multiply(2, np.deg2rad(ephem.gmls)))),
        ephem.eceo.multiply(-2).multiply(np.sin(np.deg2rad(ephem.gmas)))),
        ephem.eceo.multiply(ephem.vary).multiply(+4).multiply(np.multiply(np.sin(np.deg2rad(ephem.gmas)), np.cos(np.multiply(2, np.deg2rad(ephem.gmls)))))),
        ephem.vary.pow(2).multiply(-0.5).multiply(np.sin(np.multiply(4, np.deg2rad(ephem.gmls))))),
        ephem.eceo.pow(2).multiply(-1.25).multiply(np.sin(np.multiply(2, np.deg2rad(ephem.gmas)))))
        ))
    ephem['hasr'] = np.rad2deg(np.acos(np.subtract(np.divide(np.cos(np.deg2rad(90.833)), np.multiply(np.cos(np.deg2rad(latitude)), np.cos(np.deg2rad(ephem.sdec)))), np.multiply(np.tan(np.deg2rad(latitude)), np.tan(np.deg2rad(ephem.sdec))))))
    ephem['noon'] = np.divide(np.add(np.subtract(np.subtract(720, np.multiply(4, longitude)), ephem.eqti), (tz*60)), 1440)
    ephem['rise'] = ephem.noon.subtract(ephem.hasr.multiply(4/1440))
    ephem['sset'] = ephem.noon.add(ephem.hasr.multiply(4/1440))
    ephem['slid'] = ephem.hasr.multiply(8)
    ephem['tsti'] = pd.to_timedelta(ephem.datetime.dt.tz_convert('UTC').dt.time.astype(str)).dt.total_seconds().div(60).add(ephem.eqti.add(4*longitude))
    ephem['hang'] = ephem.tsti.divide(4).add(np.multiply(np.sign(-ephem.tsti), 180))
    ephem['szea'] = np.rad2deg(np.acos(np.add(
        np.multiply(np.sin(np.deg2rad(latitude)), np.sin(np.deg2rad(ephem.sdec))), 
        np.multiply(np.multiply(np.cos(np.deg2rad(latitude)), np.cos(np.deg2rad(ephem.sdec))), np.cos(np.deg2rad(ephem.hang))))))
    ephem['sela'] = ephem.szea.multiply(-1).add(90)
    # ephem['aare']
    # ephem['selc']
    ephem['saza'] = np.mod(np.add(540, np.rad2deg(np.acos(np.multiply(np.sign(ephem.hang), 
        np.divide(
            np.subtract(np.multiply(np.sin(np.deg2rad(latitude)), np.cos(np.deg2rad(ephem.szea))), np.sin(np.deg2rad(ephem.sdec))), 
            np.multiply(np.cos(np.deg2rad(latitude)), np.sin(np.deg2rad(ephem.szea)))
            )
        )))), 360)
    return ephem
