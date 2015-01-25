#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Authors: Anton Vilhelm Ásgeirsson <anton@antonvilhelm.is>, valka <valka@tfwno.gf>
# A tool to help determine the best trade routes in Elite & Dangerous
# LICENSE: WTFPL

import psycopg2
import math
import random
 
conn = psycopg2.connect("dbname=postgres user=postgres")
cur = conn.cursor()
 
 
# Base structure for an individual system.
class system:
    def __init__(self, system_name, x, y, z):
        self.name = system_name
        self.x = x
        self.y = y
        self.z = z

    def calc_distance(self, other):
        lightyears = math.sqrt((other.x - self.x)**2 + (other.y - self.y)**2 + (other.z - self.z)**2)
        return lightyears

 
# Base structure for a collection of systems.
class systems:
    _dict = {}
    def __init__(self):
        cur.execute("SELECT * FROM systems;")
        for n in cur: 
            self._dict[n[0]] = system(n[0], n[1], n[2], n[3])
    
    # Adds a system to the dict, writes to DB and calculates distance vectors
    # from this system to all other known systems.
    def add(self, system_name, x, y, z):
        global system #needed because otherwise system falls into local namespace.
        new_system = system(system_name, x, y, z)
        SQL  = "INSERT INTO systems (name, xcoord, ycoord, zcoord) VALUES (%s, %s, %s, %s);"
        data = (new_system.name, new_system.x, new_system.y, new_system.z)
        cur.execute(SQL, data)
        for system in self._dict:
            distance = new_system.calc_distance(self._dict[system])
            SQL  = "INSERT INTO distances (system_1, system_2, distance) VALUES (%s, %s, %s);"
            data = (new_system.name, self._dict[system].name, distance)
            cur.execute(SQL, data)

        self._dict[new_system.name] = new_system
        conn.commit()
        self.reset_distances()
    
    # Removes a system from the DB as well as any distance vectors.
    def remove(self, sysname):
        try:
            del self._dict[sysname]
            SQL  = "DELETE FROM distances WHERE system_1 = %s OR system_2 = %s;"
            data = (sysname, sysname)
            cur.execute(SQL, data)

            SQL  = "DELETE FROM systems WHERE name = %s;"
            data = (sysname,)
            cur.execute(SQL, data)

            conn.commit()
        except KeyError:
            print(sysname + " not found in systems")
            return

            
    # Updates a vector in the DB and creates new distance vectors
    #TODO: Should names be updatable?
    #TODO: Update distance vectors.
    def update(self, sysname, x, y, z):
        try:
            self._dict[sysname].x = x 
            self._dict[sysname].y = y 
            self._dict[sysname].z = z 

            SQL  = "UPDATE systems SET xcoord = %s, ycoord = %s, zcoord = %s WHERE name = %s;"
            data = (x, y, z, sysname)
            cur.execute(SQL, data)
            conn.commit()
        except KeyError:
            print(sysname + " not found in systems")

    # Drop all distance vectors from table and recalculate. Use sparingly.
    def reset_distances(self):
        # Drop all distance data and calculate anew.
        cur.execute("DELETE FROM distances")
        for system_1 in self._dict:
            for system_2 in self._dict:
                distance = self._dict[system_1].calc_distance(self._dict[system_2])
                SQL  = """
                          INSERT INTO distances (system_1, system_2, distance) 
                          VALUES (%s, %s, %s);
                       """
                data = (self._dict[system_1].name, self._dict[system_2].name, distance)
                cur.execute(SQL, data)
        conn.commit()

    def get_distance(self, system, low = None, high = None):
        if low is None:
            low  = 150
        if high is None:
            high = 180

        SQL  = """
                  SELECT 
                      system_2, distance 
                  FROM 
                      distances 
                  WHERE 
                      system_1 = %s AND distance BETWEEN %s AND %s
                  ORDER BY 
                      distance ASC;
               """
        data = (system,low,high)
        cur.execute(SQL, data)

        print("{0:20} {1:s}".format('System', 'distance'))
        print('-'*30)
        for n in cur:
            print("{0:20} {1:1f}".format(n[0], n[1]))

    # Returns the number of systems logged.
    def get_size(self):
        return len(self._dict)

    # Returns a list of the system names.
    def get_system_names(self):
        list = []
        for s in self._dict:
           list.append(s) 
        return list
    
    # Returns a system object, handles KeyErrors.
    def get_system(self, sysname):
        try:
            return self._dict[sysname]
        except KeyError:
            print("There's no system by that name.")

    # Returns a list of possible jumps from a given system
    def getjumps(self, sysname, low = 1, high = 65):
        return self.get_distance(sysname, low, high)

    # Returns the dict of systems
    def get_list(self):
        return self._dict

    # Attempts to find the best route between systems from a given starting point
    def findroute(self, i, start, pairs, routelist, firstrun):
        if firstrun:
            for system1 in sys.getjumps(i.name):
                for system2 in sys.getjumps(system1[0]):
                    k=0
                    for system3 in sys.getjumps(system2[0]):
                        for k in pairs:
                            print pairs[0][k][0]
                        if system3 in pairs:
                            routelist.append(self.get_system(system1))
                            routelist.append(self.get_system(system2))
                            routelist.append(self.get_system(system3))
                            print routelist
                            print i.name + ", " + system1[0] + ", " + system2[0] + ", " + system3[0] + ", "
                            if system3[0] == start.name:
                                print "End route."
                                return 0
                            self.findroute(start, i, pairs, routelist, False)
if __name__ == '__main__':
    sys = systems()
    #sys.reset_distances()
    #sys.add("Test0101", 0.1,0.1,0.1)
    k = 0
    routelist = []
    print sys.get_list()

    for i in sys.get_list():
        pairlist = []
        pairlist.append(sys.get_distance(i.name))
        routelist.append(i.name)
        sys.findroute(i, sys.get_list()[k], pairlist, routelist, True)
        k+=1
    #Examples
    #sys.add("39 Tauri", -7.31, -20.28, -50.91)
    #sys.add("Aegaenon", 46.91, 23.63, -59.75)
