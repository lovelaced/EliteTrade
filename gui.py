#!/usr/bin/env python

import sys
import math
import ed

from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.opengl as gl
import pyqtgraph as pg
import numpy as np

app = QtGui.QApplication([])
pg.setConfigOptions(antialias=True)
w = gl.GLViewWidget()
w.opts['distance'] = 20
w.show()
w.setWindowTitle('Elite Trading Visualisation')

#X axis
gx = gl.GLGridItem()
gx.rotate(90, 0 ,1, 0)
gx.translate(-10, 0, 0)
w.addItem(gx)

#Y axis
gy = gl.GLGridItem()
gy.rotate(90, 1, 0, 0)
gy.translate(0, -10, 0)
w.addItem(gy)

#Z axis
gz = gl.GLGridItem()
gz.translate(0, 0, -10)
w.addItem(gz)

##
##  First example is a set of points with pxMode=False
##  These demonstrate the ability to have points with real size down to a very small scale 
## 

systems =  ed.systems()
n = len(systems.list)
pos = np.empty((n, 3))
for i in range(0, n):
    s = systems.list[i]
    pos[i] = (s.x/10,s.y/10,s.z/10)
                            
sp1 = gl.GLScatterPlotItem(pos=pos, size=(0.2,), color=(1.0, 0.0, 0.0, 0.8), pxMode=False)
#sp1.translate(5,5,0)
w.addItem(sp1)

## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()

