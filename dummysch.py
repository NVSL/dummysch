#!/usr/bin/env python

import argparse
from lxml import etree as ET

import MakeSchematics

parser = argparse.ArgumentParser(description="Looks in a gcom directory to make dummy schematics for components.")

parser.add_argument("-d", required=True, metavar="gcom_dir", type=str, nargs=1, help="the directory containing the gcom directory of each component")
parser.add_argument("-c", required=True, metavar="catalog", type=str, nargs=1, help="the catalog file containing all the component specifications")
parser.add_argument("-t", required=True, metavar="sch_template", type=str, nargs=1, help="an empty schematic template")
parser.add_argument("-l", required=True, metavar="libraries", type=str, nargs='*', help="libraries to draw from")


args = parser.parse_args()
args.c = args.c[0]
args.d = args.d[0]
args.t = args.t[0]

new_cat = MakeSchematics.make_eagle_device_schematics(gcom_dir=args.d, catalog=ET.parse(args.c), sch_template=ET.parse(args.t), libraries=args.l)
new_cat.write(args.c)