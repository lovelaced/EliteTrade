#!/usr/bin/env python3

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
    dict = {}
    def __init__(self):
        cur.execute("SELECT * FROM systems;")
        for n in cur: 
            self.dict[n[0]] = system(n[0], n[1], n[2], n[3])
    
    def add(self, system_name, x, y, z):
        global system #needed because otherwise system falls into local namespace.
        new_system = system(system_name, x, y, z)
        SQL  = "INSERT INTO systems (name, xcoord, ycoord, zcoord) VALUES (%s, %s, %s, %s);"
        data = (new_system.name, new_system.x, new_system.y, new_system.z)
        cur.execute(SQL, data)
        for system in self.dict:
            distance = new_system.calc_distance(self.dict[system])
            SQL  = "INSERT INTO distances (system_1, system_2, distance) VALUES (%s, %s, %s);"
            data = (new_system.name, self.dict[system].name, distance)
            cur.execute(SQL, data)

        self.dict[new_system.name] = new_system
        conn.commit()
        self.reset_distances()
    
    def remove(self, sysname):
        try:
            del self.dict[sysname]
        except KeyError:
            print(sysname + " not found in systems")
            return

        SQL  = "DELETE FROM distances WHERE system_1 = %s OR system_2 = %s;"
        data = (sysname, sysname)
        cur.execute(SQL, data)

        SQL  = "DELETE FROM systems WHERE name = %s;"
        data = (sysname,)
        cur.execute(SQL, data)

        conn.commit()
        self.reset_distances() 
            
    #TODO: finish me.
    def update(self, system_name, x, y, z):
        pass

    def reset_distances(self):
        # Drop all distance data and calculate anew.
        cur.execute("DELETE FROM distances")
        for system_1 in self.dict:
            for system_2 in self.dict:
                distance = self.dict[system_1].calc_distance(self.dict[system_2])
                SQL  = "INSERT INTO distances (system_1, system_2, distance) VALUES (%s, %s, %s);"
                data = (self.dict[system_1].name, self.dict[system_2].name, distance)
                cur.execute(SQL, data)
        conn.commit()

    def get_distance(self, system, low = 150, high = 180):
        SQL  = "SELECT system_2, distance FROM distances WHERE system_1 = %s AND distance BETWEEN %s AND %s;"
        data = (system,low,high)
        cur.execute(SQL, data)
        for n in cur:
            print(n)

if __name__ == '__main__':
    sys = systems()
    sys.reset_distances()
    sys.get_distance("Test0101")
    sys.add("Test0101", 0.1,0.1,0.1)
    sys.get_distance("Test0101")
    sys.remove("Test0101")
    #Examples
    #sys.add("39 Tauri", -7.31, -20.28, -50.91)
    #sys.add("Aegaenon", 46.91, 23.63, -59.75)
