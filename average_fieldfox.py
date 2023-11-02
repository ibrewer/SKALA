#######################################################################################
# Python code to take data with FieldFox Handheld portable combination analyzer       #
# Requires VISA installed on controlling PC, 'http://pyvisa.sourceforge.net/pyvisa/'  #
# Keysight IO Libraries 18.1.22x 32-Bit Keysight VISA (as primary)                    #
# Anaconda Python 4.4.0 32 bit                                                        #
# pyvisa 3.6.x                                                                        #
# Currently using a mini-USB connection                                               #
#######################################################################################

import pyvisa
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import time
import h5py

# Example of how to use this code:
# python FieldFox.py 'S21' -60 1000 myFileName
# python FieldFox.py -S parameter (str) -power level (+/- int) -number of traces (int) -file name (str)

param = (sys.argv[1])
pow_param = str(sys.argv[2])
num_traces = int(sys.argv[3])
file_name = sys.argv[4]

# Open a VISA resource manager pointing to the installation folder for the Keysight Visa libraries.
rm = pyvisa.ResourceManager('/opt/keysight/iolibs/libktvisa32.so')
# Based on the resource manager, open a session to a specific VISA resource string as provided via Keysight 
# Connection Expert
myFieldFox = rm.open_resource("USB0::0x2A8D::0x5C18::MY61262579::0::INSTR") 

# Define Error Check Function
def Errcheck():
    myError = []
    ErrorList = myFieldFox.query("SYST:ERR?").split(',')
    Error = ErrorList[0]
    if int(Error) == 0:
        print("+0, No Error!")
    else:
        while int(Error)!=0:
            print("Error #: " + ErrorList[0])
            print("Error Description: " + ErrorList[1])
            myError.append(ErrorList[0])
            myError.append(ErrorList[1])
            ErrorList = myFieldFox.query("SYST:ERR?").split(',')
            Error = ErrorList[0]
            myError = list(myError)
    return myError

def set_initial_params(param, output_pow, points, myFieldFox):
    """ 
    output_pow = str; +/- output power in dB, ex. '-60'
    points = str; number of points per sweep
    avg_sweep = str; average number of sweeps
    """
    ## Set some initial parameters, query *IDN?
    myFieldFox.timeout = 10000 #Set Timeout - 10 seconds
    myFieldFox.write("*CLS") # Clear the event status registers and empty the error queue
    myFieldFox.write("*IDN?") # Query identification string *IDN?
    print("FieldFox Version:" + myFieldFox.read())
    # Preset the FieldFox and wait for operation complete via the *OPC?, i.e. the operation complete query.
    myFieldFox.write("SYST:PRES;*OPC?")
    print("Preset complete, *OPC? returned : " + myFieldFox.read())
    myFieldFox.write("INST:SEL 'NA';*OPC?") # Set mode to Network Analyzer and wait for operation complete via the *OPC?
    myFieldFox.read()
    myFieldFox.write('SOUR:POW '+output_pow) # Set the output power (dB)
    myFieldFox.write(':SOURce:POWer?') # Query power value
    pow_val = myFieldFox.read().strip('\n')
    myFieldFox.write("INIT:CONT ON") # Make sure it is running continuosly
    myFieldFox.write("CALC:PAR:DEF "+param) # Measure the S parameter
    ## Set the start and stop frequency and print out the values
    myFieldFox.write("FREQ:STAR MIN") # Set the starting frequency to a miminum
    myFieldFox.write("SENS:FREQ:START?") # Query to make sure it is working
    startFreq = myFieldFox.read().strip('\n') # Save the starting frequency
    myFieldFox.write("FREQ:STOP 500e6") # Set the stopping frequency to 500 MHz
    myFieldFox.write("SENS:FREQ:STOP?") # Query
    stopFreq = myFieldFox.read().strip('\n') # Save stop value
    print("FieldFox start frequency = " + startFreq + ", stop frequency = " + stopFreq)
    myFieldFox.write("SWE:POIN "+points) # Set number of points in a sweep
    myFieldFox.write("SENS:SWE:POIN?") # Query to make sure it's set correctly
    numPoints = myFieldFox.read().strip('\n') # Save the number of points in a sweep
    print("Number of trace points = " + numPoints)
    myFieldFox.write("AVER:COUN 100") # Average over x many sweeps
    myFieldFox.write("AVER:CLE") # Clear sweeps
    freqs = np.linspace(int(startFreq), int(stopFreq), int(numPoints)) # Create an array of freqs
    
    return freqs, numPoints, pow_val

def take_data(no_of_traces, numPoints, myFieldFox):
    """
    Take data with FieldFox.
    no_of_traces = int; number of traces you want to record.
    numPoints = str; number of points in a trace as recorded by FieldFox
    myFieldFox = object; FieldFox as defined by VISA Resource Manager
    """

    trace_array = np.zeros((no_of_traces, int(numPoints)))
    time.sleep(1)

    for i in range(no_of_traces):
    	# Once you've waited a while, hold
        t = 50
        while t:
            mins, secs = divmod(t, 60)
            timer = '{:02d}:{:02d}'.format(mins, secs)
            print(timer, end="\r")
            time.sleep(1)
            t -= 1
        myFieldFox.write("INIT:CONT 0;*OPC?") # Hold
        myFieldFox.read()
        myFieldFox.write("INIT:IMMediate;*OPC?") # Trigger on a measurement
        myFieldFox.read()
        myFieldFox.write("CALC:SMO 1") # Apply smoothing I think
        myFieldFox.write("CALC:DATA:FDATa?") # Read data from selected trace
        trace = myFieldFox.read() # Save that data
        # Clean up the data, save the trace as an array of floats
        trace = trace.split(',')
        for m in range(len(trace)):
            if '\n' in trace[m]:
                trace[m].strip('\n')
            trace[m] = float(trace[m])
        trace = np.array(trace)
        trace_array[i] = trace
        if i % 100 == 0:
            print("%d / %d traces complete..."%((i+1), no_of_traces))
        myFieldFox.write("INIT:CONT ON") # Continue sweeping, run in continuous mode
        myFieldFox.write("AVER:CLE") # Reset your sweep
	    
    return trace_array

def save_data(trace_array, freqs, pow_val, file_name):
	"""
	Save the data as a h5py file and a txt file.
	trace_array = array; Data taken with FieldFox (size = number of traces x number of points)
	freqs = 1-D array; Range of frequencies covered by FieldFox
	pow_val = str; output power as recorded by FieldFox
	file_name = str; name of file (no file extensions!)
	"""

	with h5py.File(file_name+".hdf5", "w") as f:
		dset = f.create_dataset('trace_data', data=trace_array)
		dset = f.create_dataset('freq_vals', data=freqs)
		dset = f.create_dataset('power_val', data=pow_val)

	np.savetxt(file_name+".txt", trace_array)

	return

def plot_data(freqs, data, title):
    """
    freqs = 1-D array; Range of frequencies covered by FieldFox
    data = array; Data taken with FieldFox (size = number of traces x number of points)
    title = str; Save this file!
    """
    plt.figure(figsize=(10,8))
    for trace in data:
        plt.plot(freqs, trace)
    plt.xlabel('Frequency (MHz)', fontsize=22)
    plt.ylabel('dB',fontsize=22)
    plt.xticks(fontsize=15)
    plt.yticks(fontsize=15)
    #plt.savefig(title+'.png')
    plt.show()
    
    return

print(Errcheck())
freqs, numPoints, pow_val = set_initial_params(param, pow_param, '450', myFieldFox) 
trace_data = take_data(num_traces, numPoints, myFieldFox)
save_data(trace_data, freqs, pow_val, file_name)
plot_data(freqs, trace_data, file_name)