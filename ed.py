#!/usr/bin/env python3
import psycopg2
import math
import random
 
conn = psycopg2.connect("dbname=postgres user=postgres")
cur = conn.cursor()
 
 
class system:
    def __init__(self, system_name, x, y, z):
        self.name = system_name
        self.x = x
        self.y = y
        self.z = z
        self.distancefrom = {}
        self.possiblejumps = []

    def calc_distance(self, other):
        lightyears = math.sqrt((other.x - self.x)**2 + (other.y - self.y)**2 + (other.z - self.z)**2)
        return lightyears

    #consider adding basic CRUD here (sans Creation)
 
class systems:
    list = []
    def __init__(self):
        cur.execute("SELECT * FROM systems;")
        for n in cur: 
            self.list.append(system(n[0], n[1], n[2], n[3]))
    
    def add(self, system_name, x, y, z):
        global system #needed because otherwise system falls into local namespace.
        new_system = system(system_name, x, y, z)
        cur.execute("INSERT INTO systems (name, xcoord, ycoord, zcoord) VALUES (%s, %s, %s, %s)",
                (new_system.name, new_system.x, new_system.y, new_system.z))
        for system in systems.list:
            distance = new_system.calc_distance(system)
            cur.execute("INSERT INTO distances (system_1, system_2, distance) VALUES (%s, %s, %s)",
                (new_system.name, system.name, distance))

        self.list.append(new_system)
        conn.commit()

    def reset_distances(self):
        # Drop all distance data and calculate anew.
        cur.execute("DELETE FROM distances")
        for system_1 in systems.list:
            for system_2 in systems.list:
                distance = system_1.calc_distance(system_2)
                cur.execute("INSERT INTO distances (system_1, system_2, distance) VALUES (%s, %s, %s)",
                    (system_1.name, system_2.name, distance))
        conn.commit()


if __name__ == '__main__':
    sys = systems()
    sys.reset_distances()
    #Examples
    #sys.add("39 Tauri", -7.31, -20.28, -50.91)
    #sys.add("Aegaenon", 46.91, 23.63, -59.75)
