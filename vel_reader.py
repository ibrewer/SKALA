#!/bin/env python3

import numpy as np

from icecube import icetray, radcube, dataclasses
from icecube.icetray import I3Units

vresponse = radcube.I3AntennaResponse()
test = vresponse.GetVectorEffectiveLength(150*I3Units.megahertz, -5*I3Units.degree, -5*I3Units.degree)
print(test)

#Note: these are the maximum bounds on which things are defined.
#Values are defined every 1 deg in zen/azi and every 1 MHz in freq
#Between these, values are interpolated.
#Any arbitrary value can be asked for, but just know that this is the limit

#gain_array = np.zeros(shape=(len(np.linspace(0, 359, 360)),len(np.linspace(-90, 90, 181)),len(np.linspace(50, 350, 301))))
#ex_array = np.zeros(shape=(len(np.linspace(0, 359, 360)),len(np.linspace(-90, 90, 181)),len(np.linspace(50, 350, 301))))
#ey_array = np.zeros(shape=(len(np.linspace(0, 359, 360)),len(np.linspace(-90, 90, 181)),len(np.linspace(50, 350, 301))))

#azi = np.linspace(0, 359, 360)* I3Units.degree
#zen = np.linspace(0, 90, 91)* I3Units.degree
#zen = np.linspace(-90, 90, 181)* I3Units.degree
#f = np.linspace(50, 350, 301)* I3Units.megahertz

azi = np.arange(0, 360, 1)* I3Units.degree
#zen = np.linspace(0, 90, 91)* I3Units.degree
zen = np.arange(0, 90, 1)* I3Units.degree
f = np.linspace(50, 350, 301)* I3Units.megahertz

gain_array = np.zeros(shape=(len(azi),len(zen),len(f)))
ex_array = np.zeros(shape=(len(azi),len(zen),len(f)))
ey_array = np.zeros(shape=(len(azi),len(zen),len(f)))

for l in range(0,len(azi)): # azimuth angle
    for m in range(0,len(zen)): # zen angle
        for n in range(0,len(f)): # f in MHz
            vel = vresponse.GetVectorEffectiveLength(f[n], azi[l], zen[m])
            gain = vresponse.GetEffectiveArea(f[n], azi[l], zen[m]) * 4 * np.pi  / (dataclasses.I3Constants.c / f[n])**2
            ex_array[l,m,n] = abs(vel[0])
            ey_array[l,m,n] = abs(vel[1])
            gain = gain.magnitude()
            gain_array[l,m,n] = gain
            
            #GetVectorEffectiveLength, gives you an I3 complex vector, (3x2) array

        
      # ...Put it into a container or whatever here
    
    
