#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Authors: Anton Vilhelm Ásgeirsson <anton@antonvilhelm.is>, valka <valka@tfwno.gf>
# A tool to help determine the best trade routes in Elite & Dangerous
# LICENSE: WTFPL

import psycopg2
import math
import random
import pprint
 
conn = psycopg2.connect("dbname=postgres user=postgres")
cur = conn.cursor()
 
 
# Base structure for an individual system.
# TODO: add more system stats?
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
        SQL  = """
                  INSERT INTO 
                      systems (name, xcoord, ycoord, zcoord) 
                  VALUES 
                      (%s, %s, %s, %s);
               """
        data = (new_system.name, new_system.x, new_system.y, new_system.z)
        cur.execute(SQL, data)
        for system in self._dict:
            distance = new_system.calc_distance(self._dict[system])
            SQL  = """
                      INSERT INTO 
                          distances (system_1, system_2, distance) 
                      VALUES 
                          (%s, %s, %s);
                   """
            data = (new_system.name, self._dict[system].name, distance)
            cur.execute(SQL, data)

        self._dict[new_system.name] = new_system
        conn.commit()
        self.reset_distances()
    
    # Removes a system from the DB as well as any distance vectors.
    def remove(self, system_name):
        try:
            del self._dict[system_name]
            SQL  = """
                      DELETE FROM 
                          distances 
                      WHERE 
                          system_1 = %s 
                      OR
                          system_2 = %s;
                   """
            data = (system_name, system_name)
            cur.execute(SQL, data)

            SQL  = """
                      DELETE FROM 
                          systems 
                      WHERE 
                          name = %s;
                   """
            data = (system_name,)
            cur.execute(SQL, data)

            conn.commit()
        except KeyError:
            print(system_name + " not found in systems")
            return

            
    # Updates a vector in the DB and creates new distance vectors
    #TODO: Should names be updatable?
    #TODO: Update distance vectors.
    def update(self, system_name, x, y, z):
        try:
            self._dict[system_name].x = x 
            self._dict[system_name].y = y 
            self._dict[system_name].z = z 

            SQL  = """
                      UPDATE 
                          systems 
                      SET 
                          xcoord = %s, 
                          ycoord = %s, 
                          zcoord = %s 
                      WHERE 
                          name = %s;
                   """
            data = (x, y, z, system_name)
            cur.execute(SQL, data)
            conn.commit()
            reset_system_distances(system_name)
        except KeyError:
            print(system_name + " not found in systems")

    # Reset system vectors for a specific system.
    # Helper function for update.
    # Should be less expensive than the reset_distances() function.
    def reset_system_distances(self, system_name):
        try:
            SQL = """
                     DELETE FROM 
                         distances
                     WHERE
                         system_1 = %s
                     OR 
                         system_2 = %s;
                  """
            data = (system_name, system_name)
            cur.execute(SQL, data)
            for system_1 in self._dict:
                distance = self._dict[system_1].calc_distance(self._dict[system_name])
                SQL  = """
                          INSERT INTO 
                              distances (system_1, system_2, distance) 
                          VALUES 
                              (%s, %s, %s);
                       """
                data = (self._dict[system_1].name, self._dict[system_name].name, distance)
                cur.execute(SQL, data)
            for system_2 in self._dict:
                distance = self._dict[system_name].calc_distance(self._dict[system_2])
                SQL  = """
                          INSERT INTO 
                              distances (system_1, system_2, distance) 
                          VALUES 
                              (%s, %s, %s);
                       """
                data = (self._dict[system_name].name, self._dict[system_2].name, distance)
                cur.execute(SQL, data)
            conn.commit()

        except KeyError:
            print(system_name + " not found in systems")

    # Drop all distance vectors from table and recalculate. Use sparingly.
    def reset_distances(self):
        # Drop all distance data and calculate anew.
        cur.execute("DELETE FROM distances")
        for system_1 in self._dict:
            for system_2 in self._dict:
                distance = self._dict[system_1].calc_distance(self._dict[system_2])
                SQL  = """
                          INSERT INTO 
                              distances (system_1, system_2, distance) 
                          VALUES 
                              (%s, %s, %s);
                       """
                data = (self._dict[system_1].name, self._dict[system_2].name, distance)
                cur.execute(SQL, data)
        conn.commit()

    # Queries the distance table for all systems within the low/high limits.
    # If called with no params it defaults to 150/180.
    def get_distance(self, system_name, low = 160, high = 180):
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
        data = (system_name,low,high)
        cur.execute(SQL, data)
        
        dist_set = set() 
        for n in cur:
            dist_set.add(n[0])
        return dist_set

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
    def get_system(self, system_name):
        try:
            return self._dict[system_name]
        except KeyError:
            print("There's no system by that name.")

    # Returns a list of possible jumps from a given system
    def get_jumps(self, system_name, low = 1, high = 65):
        return self.get_distance(system_name, low, high)

    # Attempts to find the best route between systems from system_name and ending there as well.
    def find_route(self, system_name, jump_list = [], jump_min = 6):
        try:
            target_systems = self.get_distance(system_name)
            route_dict = {}
            graph = self.gen_graph()
            #route_dict[target_systems] = self.reverse_route(target_systems, system_name, graph)
            for target in target_systems:
                l = []
                for r in self.reverse_route(target, system_name, graph):
                    l.append(r) 
                route_dict[target] = l
            
            for r in route_dict.items():
                for n in r[1]:
                    if len(n) < 6:
                        print(n)
                #pprint.PrettyPrinter(indent=4).pprint(route_dict["Rapa Bao"])

            #self.reverse_route(str(target_systems[0][1]), system_name, 0, 2)
            
        except KeyError:
            print(system_name + " not found in systems.")


    # Helper function for find_route
    def reverse_route(self, target, origin, graph, visited=None):
        if visited is None:
            visited = set()

        visited |= {target}
        for s in graph[target]:
            if s in visited:
                continue
            if s == origin:
                yield [target, origin]
            else:
                for route in self.reverse_route(s, origin, graph, visited):
                    yield [target] + route

    # Generates graphs of all connected systems and puts it in a dictionary.
    def gen_graph(self):
        d = {}
        for s in self._dict:
            d[s] = self.get_jumps(s)
        return d

if __name__ == '__main__':
    sys = systems()
    l = sys.get_system_names()
    for s in l:
        sys.find_route(s)
    #sys.find_route("Arouca")
    #b = sys.gen_graph()
    #pprint.PrettyPrinter(indent=4).pprint(b)
    
    #Examples
    #sys.add("39 Tauri", -7.31, -20.28, -50.91)
    #sys.add("Aegaenon", 46.91, 23.63, -59.75)
