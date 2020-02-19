### load modules
from pyDeltaRCM import BmiDelta
from pymt.models import Cem
import numpy as np
import matplotlib.pyplot as plt

### Create classes for each model
delta = BmiDelta()
dcomp = BmiDelta()
coast = Cem()

### Initialize deltaRCM model
delta.initialize('deltaRCM.yaml')
dcomp.initialize('deltaRCM2.yaml')
[nrows, ncols] = delta.get_grid_shape(1)
[sp, sp1] = delta.get_grid_spacing(1)

### inlet filling
[a,b] = np.shape(delta._delta.eta)
for i in range(0,a):
    for j in range(0,b):
        if delta._delta.eta[i,j] > 0:
            delta._delta.eta[i,j] = 1
filled_inlet = delta._delta.eta[0:20,:].copy()
inlet = delta._delta.eta[0:20,:].copy()
filled_inlet[:,48:50] = filled_inlet[:,45:47]
filled_inlet[:,50:52] = filled_inlet[:,53:55]

# use values from deltaRCM to init other models
args = coast.setup(number_of_rows=nrows, number_of_cols=ncols, grid_spacing=50., shoreface_depth=5.0)
coast.initialize(*args)

# set some values
coast.set_value('sea_surface_water_wave__height', 2.)
coast.set_value('sea_surface_water_wave__period', 7.)
coast.set_value('sea_surface_water_wave__azimuth_angle_of_opposite_of_phase_velocity',0. * np.pi / 180.)

# matching initial topography
grid_id = coast.get_var_grid('land_surface__elevation')
spacing = coast.get_grid_spacing(grid_id)
shape = coast.get_grid_shape(grid_id)
L = np.empty(shape)
[a,b] = np.shape(L)
for i in range(0,a):
    for j in range(0,b):
        L[i,j] = delta._delta.eta[i,j]
coast.set_value('land_surface__elevation',L)
coast.get_value('land_surface__elevation',out=L)
delta.set_value('sea_bottom_surface__elevation',L)
dcomp.set_value('sea_bottom_surface__elevation',L)

# running the model
for i in range(0,5000):
    # first update deltaRCM
    print('Time:', delta.get_current_time())
    print('Running deltaRCM')
    delta.update()
    dcomp.update()

    # use eta from deltaRCM but fill in inlet channel for CEM
    print('Updating CEM elevations from deltaRCM')
    Lnew = delta._delta.eta.copy()
    inlet = delta._delta.eta[0:20,:].copy()
    Lnew[0:20,:] = filled_inlet
    grid_id = coast.get_var_grid('land_surface__elevation')
    spacing = coast.get_grid_spacing(grid_id)
    shape = coast.get_grid_shape(grid_id)
    L = np.empty(shape)
    [a,b] = np.shape(L)
    for i in range(0,a):
        for j in range(0,b):
            L[i,j] = Lnew[i,j]
    coast.set_value('land_surface__elevation',L)
    print('Running CEM')
    coast.update()

    # update land surface from CEM to deltaRCM
    print('Updating eta from CEM to deltaRCM')
    coast.get_value('land_surface__elevation',out=L)
    # re-dig the inlet that was filled for CEM
    L[0:20,:] = inlet
    delta.set_value('sea_bottom_surface__elevation',L)
