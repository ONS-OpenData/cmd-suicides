#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan  9 11:25:02 2019

@author: robertgrant
"""

import numpy as np
from databaker.framework import *
import pandas as pd
from databakerUtils.writers import v4Writer
import re
import requests
import json
import math
import glob
from databakerUtils.api import getAllCodes, getAllLabels

inputfile = '2017localauthority.xls'
outputfile = 'v4_suicides.csv'

tabsWeWant = ['Table 1']
tabs = loadxlstabs(inputfile, tabsWeWant)
conversionsegments = []

for tab in tabs:   
        
    # define a selection of cells as the observations
    obs = tab.excel_ref('E6').expand(DOWN).expand(RIGHT).is_not_blank().is_not_whitespace()
    

    area_id = tab.excel_ref('A6').expand(DOWN).is_not_blank().is_not_whitespace()
    area_label1 = tab.excel_ref('B6').expand(DOWN).is_not_blank().is_not_whitespace()
    area_label2 = tab.excel_ref('C6').expand(DOWN).is_not_blank().is_not_whitespace()
    area_label3 = tab.excel_ref('D6').expand(DOWN).is_not_blank().is_not_whitespace()
    year = tab.excel_ref('E4').expand(RIGHT).is_not_blank().is_not_whitespace()
    geography = area_label1|area_label2|area_label3

    dimensions = [
              HDim(year, "year", DIRECTLY, ABOVE),
              HDim(area_id, "la_code", DIRECTLY, LEFT),
              HDim(area_label1, "label1", DIRECTLY, LEFT),
              HDim(area_label2, "label2", DIRECTLY, LEFT),
              HDim(area_label3, "label3", DIRECTLY, LEFT),
              HDim(geography, "geography", DIRECTLY, LEFT)
                 ]
    
    
    
    conversionsegment = ConversionSegment(tab,dimensions,obs).topandas()
    conversionsegments.append(conversionsegment)
   
     
# print it all to data frame (this code never changes)
conversionsegments = pd.concat(conversionsegments)


col = list(conversionsegments.columns)[3:6]
conversionsegments = conversionsegments.drop(col, axis=1)

#get admin codelist
sheetNameURL = 'https://api.cmd-dev.onsdigital.co.uk/v1/code-lists/admin-geography/editions/one-off/codes'
admin_api = requests.get(sheetNameURL).json()

#convert to dataframe
admin_codelist = pd.DataFrame(admin_api['items'])
del admin_codelist['links']

conversionsegments2 = pd.merge(conversionsegments, admin_codelist, how = 'inner', left_on = 'la_code', right_on = 'id')

#check to see if numbers of rows match:
if len(conversionsegments) != len(conversionsegments2):
    raise Exception('Lengths do not match. Check your data for mismatching codes')


#convert years to strings

conversionsegments2['suicides-year'] = conversionsegments2['year'].str[:4]
conversionsegments2['year'] = conversionsegments2['suicides-year']

v4 = conversionsegments2[['OBS', 'suicides-year', 'year', 'la_code', 'label']]
v4.columns = ['V4_0', 'calendar-years', 'time', 'admin-geography', 'geography']

v4.to_csv(outputfile, index = False)
