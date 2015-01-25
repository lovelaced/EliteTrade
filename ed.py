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
        
        dist_list = []
        for n in cur:
            dist_list.append(n)
        return dist_list

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

if __name__ == '__main__':
    sys = systems()
    #sys.reset_distances()
    #sys.add("Test0101", 0.1,0.1,0.1)
    sys.get_distance("Test0101",180, 500)
    #Examples
    #sys.add("39 Tauri", -7.31, -20.28, -50.91)
    #sys.add("Aegaenon", 46.91, 23.63, -59.75)
