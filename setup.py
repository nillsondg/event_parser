import os
from min_cult import mincult_folder

if not os.path.exists("events"):
    os.makedirs("events")

if not os.path.exists("events_desc"):
    os.makedirs("events_desc")

if not os.path.exists(mincult_folder):
    os.makedirs(mincult_folder)
