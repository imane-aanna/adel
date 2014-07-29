""" Check progression of leaf areas """

import matplotlib.pyplot as plt
plt.ion()

# Imports for wheat
import pickle
from alinea.adel.newmtg import move_properties
from alinea.echap.architectural_reconstructions import reconst_db
from alinea.alep.disease_outputs import SeptoRecorder

# Imports for weather
from alinea.astk.TimeControl import *
from alinea.echap.weather_data import *
from alinea.alep.alep_weather import basic_degree_days

# Temporary
from alinea.adel.mtg_interpreter import plot3d
from openalea.plantgl.all import Viewer

def get_leaf_ids(g):
    labels = g.property('label')
    stems = [id for id,lb in labels.iteritems() if lb.startswith('MS')]
    blades = [id for id,lb in labels.iteritems() if lb.startswith('blade')]
    leaf_sectors = {}
    ind_plant = 0
    for st in stems:
        ind_plant += 1
        leaf_sectors['P%d' % ind_plant] = {}
        nff = int(g.node(st).properties()['nff'])
        leaves = [bl for bl in blades if bl>st][:nff]
        ind_lf = nff+1
        for lf in leaves:
            ind_lf -= 1
            stem_elt = int(g.node(lf).components()[0].index())
            leaf_sectors['P%d' % ind_plant]['F%d' % ind_lf] = range(stem_elt+1, stem_elt+nsect+1)
            #leaf_sectors['P%d' % ind_plant]['F%d' % ind_lf] = range(lf+1, lf+nsect+1)
    return leaf_sectors

# Initialize wheat plant
Mercia = reconst_db['Mercia']
nsect = 5
pgen, adel, domain, domain_area, convUnit, nplants = Mercia(nplants = 1, nsect=nsect, disc_level=20)
g = adel.setup_canopy(age=600.)

# Manage weather and time control
# start_date="2010-10-15 12:00:00"
start_date="2011-03-01 12:00:00"
end_date="2011-06-20 01:00:00"
weather = Boigneville_2010_2011()
weather.check(varnames=['degree_days'], models={'degree_days':basic_degree_days}, start_date=start_date)
seq = pandas.date_range(start = start_date, end = end_date, freq='H')
TTmodel = DegreeDayModel(Tbase = 0)
every_dd = thermal_time_filter(seq, weather, TTmodel, delay = 20)
canopy_timing = IterWithDelays(*time_control(seq, every_dd, weather.data))
    
# Prepare saving of outputs
recorders = {}
leaf_sectors = get_leaf_ids(g)
for plant in leaf_sectors:
    recorders[plant] = {}
    for leaf, lf_sectors in leaf_sectors[plant].iteritems():
        recorders[plant][leaf] = SeptoRecorder(vids=lf_sectors, group_dus=True)
        
# Reconstruction
for canopy_iter in canopy_timing:
    if canopy_iter:
        date = canopy_iter.value.index[0]
        print date
        
        # Grow wheat
        g = adel.grow(g, canopy_iter.value)
        
        # Temporary : 3D display
        scene = plot3d(g)
        Viewer.display(scene)
        
        # Save variables
        leaf_sectors = get_leaf_ids(g)
        for plant in recorders:
            for lf, recorder in recorders[plant].iteritems():
                recorder.update_vids(vids=leaf_sectors[plant][lf])
                recorder.record_only_leaf_data(g, date, degree_days = canopy_iter.value.degree_days[-1])

for plant in recorders:
    for recorder in recorders[plant].itervalues():
        recorder.create_dataframe_only_leaf_data()
        
leaves = ['F%d' % lf for lf in range(13)]
fig, axs = plt.subplots(3, 3)
for plant in recorders:
    for recorder in recorders[plant].itervalues():
        data = recorder.data
        axs[0][0].plot(data.degree_days, data.leaf_area)
        axs[0][0].set_ylabel('leaf area (cm2)', fontsize = 18)
        axs[0][1].plot(data.degree_days, data.leaf_green_area)
        axs[0][1].set_ylabel('leaf green area (cm2)', fontsize = 18)
        axs[0][2].plot(data.degree_days, data.senesced_area)
        axs[0][2].set_ylabel('leaf senesced area (cm2)', fontsize = 18)
        axs[1][0].plot(data.degree_days, data.leaf_length)
        axs[1][0].set_ylabel('leaf length (cm)', fontsize = 18)
        axs[1][1].plot(data.degree_days, data.leaf_green_length)
        axs[1][1].set_ylabel('leaf green length (cm)', fontsize = 18)
        axs[1][2].plot(data.degree_days, data.leaf_senesced_length)
        axs[1][2].set_ylabel('leaf senesced length (cm2)', fontsize = 18)
        axs[2][0].plot(data.degree_days, data.leaf_min_height)
        axs[2][0].set_ylabel('leaf bottom height (cm)', fontsize = 18)
        axs[2][1].plot(data.degree_days, data.leaf_mean_height)
        axs[2][1].set_ylabel('leaf mean height (cm)', fontsize = 18)
        axs[2][2].plot(data.degree_days, data.leaf_max_height)
        axs[2][2].set_ylabel('leaf top height (cm)', fontsize = 18)
        ylims = [min([ax.get_ylim()[0] for ax in axs[2]]), max([ax.get_ylim()[1] for ax in axs[2]])]
        for ax in axs[2]:
            ax.set_ylim(ylims)