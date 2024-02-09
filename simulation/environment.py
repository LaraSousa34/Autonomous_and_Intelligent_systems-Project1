import random

#--------------------------------------------------------------------------------------------------------------------------------------------------------------      

class Road:
    def __init__(self, name, traffic_light_name, zebra_crossing, traffic_sign):
        self.name = name # road id, ex: road_1
        self.traffic_light = traffic_light_name # Traffic light id of the one associated to the road, ex: Traffic_Light_1
        self.zebra_crossing = zebra_crossing # Zebra crossing id of the one associated to the road, ex: Zebra_Crossing_1
        self.traffic_sign = traffic_sign # Traffic Signal id of the one associated to the road, ex: Priority
 
#--------------------------------------------------------------------------------------------------------------------------------------------------------------      

# Every road that has a traffic light associated, by default it is positioned at the end of the road: road[5]
# Every road that has a zebra crossing associated, by default it is positioned at the end of the road: road[5]

#--------------------------------------------------------------------------------------------------------------------------------------------------------------      

class Environment:

    def __init__(self):
        self.car_agent = None

        self.cars = {} # Dictionary with all of the cars, ex: car_jid: CarAgent()
        self.ambulances = {} # Dictionary with all of the ambulances, ex: ambulance_jid: AmbulanceAgent()
        self.people = {} # Dictionary with all of the people, ex: person_jid: PersonAgent()

        # Roads with traffic lights
        self.road_1 = Road("road_1", "Traffic_Light_1", "Zebra_Crossing_1", "No traffic sign")  # the one on horizontal until the intersection - the one above
        self.road_2 = Road("road_2", "Traffic_Light_1", "Zebra_Crossing_1", "No traffic sign")  # the one on horizontal until the intersection - the one below
        self.road_3 = Road("road_3", "Traffic_Light_2", "Zebra_Crossing_2", "No traffic sign")  # the one on vertical until the intersection - the one on the left
        self.road_4 = Road("road_4", "Traffic_Light_3", "Zebra_Crossing_3", "No traffic sign")  # the one on vertical until the intersection - the one on the right 
        self.road_9 = Road("road_8", "No traffic light", "No Zebra Crossing", "Priority")  # the one on vertical on the right - the one below


        # Roads without traffic lights
        self.road_5 = Road("road_5", "No traffic light", "No Zebra Crossing", "No traffic sign")  # the one on horizontal from the intersection - the one above
        self.road_6 = Road("road_6", "No traffic light", "No Zebra Crossing", "No traffic sign")  # the one on horizontal from the intersection - the one below
        self.road_7 = Road("road_7", "No traffic light", "No Zebra Crossing", "No traffic sign")  # the one on vertical from the intersection - the one on the left
        self.road_8 = Road("road_8", "No traffic light", "No Zebra Crossing", "No traffic sign")  # the one on vertical from the intersection - the one on the right 

        self.road_10 = Road("road_8", "No traffic light", "No Zebra Crossing", "No traffic sign")  # the one on vertical on the right - the one above 
        self.road_11 = Road("road_8", "No traffic light", "No Zebra Crossing", "No traffic sign")  # the one on horizontal on the right- the one above 
        self.road_12 = Road("road_8", "No traffic light", "No Zebra Crossing", "No traffic sign")  # the one on horizontal on the right - the one above 

        
        self.traffic_lights = {"Traffic_Light_1": "red", 
                               "Traffic_Light_2": "yellow", 
                               "Traffic_Light_3": "green"}  # Default traffic light color name
        
    

        self.choose_road_after_intersection = {self.road_1: [self.road_5, self.road_7],
                                                self.road_2: [self.road_6],
                                                self.road_3: [self.road_8, self.road_6],
                                                self.road_4: [self.road_7],
                                                self.road_5: [self.road_11],
                                                self.road_6: [self.road_12],
                                                self.road_9: [self.road_10]} # Being on the "key road", the vehicle can choose were to go next (after de intersection)
        
        self.choose_new_road = [self.road_1, self.road_2, self.road_3, self.road_4, self.road_9] # When the car reaches the end of a road, it can choose a new one to start all over - cicle
      
        self.choose_zebra_crossing = [self.road_1, self.road_3, self.road_4] # When a person crosses a zebra crossing, he can choose a new one




    # Functions to add the agents to the environment (the corresponding dictionary)
    def add_car_agent(self, car_agent):
        self.car_agent = car_agent
        self.cars[self.car_agent.jid] = self.car_agent 

    def add_ambulance_agent(self, ambulance_agent):
        self.ambulance_agent = ambulance_agent
        self.ambulances[self.ambulance_agent.jid] = self.ambulance_agent

    def add_person_agent(self, person_agent):
        self.person_agent = person_agent
        self.people[self.person_agent.jid] = self.person_agent




    # Function to update(change) the traffic light color
    def update_traffic_light(self, traffic_light_name, color_name, event):
        
        self.traffic_lights[traffic_light_name] = color_name
        if event is not None:

            if event == "emergency":
                print(f"{traffic_light_name} is now {color_name} due to an emergency")

            elif event == "person":
                print(f"{traffic_light_name} is now {color_name} due to the zebra crossing")



    # Function to get the color of the traffic light at that moment
    def get_traffic_light(self, traffic_light_name):
        # This method returns the state of a traffic light
        return self.traffic_lights.get(traffic_light_name, self.traffic_lights[traffic_light_name] )



    # Funtions to choose a new zebra crossing/road
    def change_zebra_crossing (self, person_jid):
        self.people[person_jid].road = random.choice(self.choose_zebra_crossing)

    def change_road(self, vehicle_jid, vehicle_id, road, type_vehicle):

        if type_vehicle == "car":
            current_position = self.cars[vehicle_jid].position
        
        else: #type_vehicle == "ambulance"
            current_position = self.ambulances[vehicle_jid].position

        if current_position == 5:

            # Reaching the intersection, the vehicle chooses one of the possible roads
            if road.name in ["road_1", "road_2", "road_3", "road_4"]:
                if type_vehicle == "car":
                    self.cars[vehicle_jid].position = 0
                    self.cars[vehicle_jid].road = random.choice(self.choose_road_after_intersection[self.cars[vehicle_jid].road])
                    print(f"{vehicle_id}: reached an intersection, choosing a new road: {self.cars[vehicle_jid].road.name}")

                else: # type_vehicle == "ambulance"
                    self.ambulances[vehicle_jid].position = 0
                    self.ambulances[vehicle_jid].road = random.choice(self.choose_road_after_intersection[self.ambulances[vehicle_jid].road])
                    print(f"{vehicle_id}: reached an intersection, choosing a new road: {self.ambulances[vehicle_jid].road.name}")
            
            # Reaching the end of the "trip" the car chooses a new road to start all over
            else:
                if type_vehicle == "car": 
                    self.cars[vehicle_jid].position = 0
                    self.cars[vehicle_jid].road = random.choice(self.choose_new_road)
                
                else: #type_vehicle == "ambulance"
                    self.ambulances[vehicle_jid].position = 0
                    self.ambulances[vehicle_jid].road = random.choice(self.choose_new_road)

                print(f"{vehicle_id}: reached the end of the road, choosing a new road: {road.name}")




    # Function to verify if there is some vehicle ahead
    def is_vehicle_ahead(self, vehicle_jid, type_vehicle):
        
        # Checks if theres any sort of vehicle ahead
        if type_vehicle == "car": 
            current_position = self.cars[vehicle_jid].position

            # Check if there is any ambulance in front of it
            for ambulance_jid, ambulance in self.ambulances.items():
                if ambulance.road == self.cars[vehicle_jid].road and ambulance.position == current_position + 1:
                    return True
            
            # Check if there is any car in front of it
            for other_car_jid, other_car in self.cars.items():
                if other_car_jid != vehicle_jid and other_car.road == self.cars[vehicle_jid].road and other_car.position == current_position + 1:
                    return True
            return False

        # Is an ambulance - only checks if there is an ambulance ahead
        else: 
            current_position = self.ambulances[vehicle_jid].position

            # Check if there is any ambulance in front of it
            for other_ambulance_jid, other_ambulance in self.ambulances.items():
                if other_ambulance_jid != vehicle_jid and other_ambulance.road == self.ambulances[vehicle_jid].road and other_ambulance.position == current_position + 1:
                    return True
            return False