import asyncio
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
from queue import Queue
from asyncio import Lock

#--------------------------------------------------------------------------------------------------------------------------------------------------------------

# List of the possible colors of the traffic lights
colors = ["green", "yellow", "red"]

#--------------------------------------------------------------------------------------------------------------------------------------------------------------      

class TrafficLightAgent(Agent):
    def __init__(self, jid, password, environment, traffic_light_name, central_jid):
        super().__init__(jid, password)
        self.environment = environment  # Reference to the simulation environment
        self.traffic_light_name = traffic_light_name # Traffic Light id, ex: "Traffic_Light_1"
        self.central_jid = central_jid # The JID of the CentralCordinateAgent

    async def setup(self):
        print(f"{self.traffic_light_name} started")
        self.add_behaviour(self.TrafficLightBehaviour())

    class TrafficLightBehaviour(CyclicBehaviour):
        async def run(self):

            current_color_name = self.agent.environment.get_traffic_light(self.agent.traffic_light_name)

            # Waits for a message from the CentralCordinateAgent
            msg = await self.receive(timeout=1)

            if msg:

                # If the message is to know the color of the traffic light at the moment
                if msg.body == "color":
                    msg = Message(to=str(self.agent.central_jid))
                    msg.set_metadata("performative", "inform")
                    msg.body = current_color_name
                    await self.send(msg)

                # If the message is to let the traffic light know it is an emergency and that it needs to change itself to green
                elif msg.body == "emergency":
                    await self.change_color_ambulance()

                #  If the message is to let the traffic light know there is a person who wants to cross the street and that it needs to change itself to red
                elif msg.body == "person":
                    await self.change_color_person()
                
                # Check if the message is (new_color:event) type
                elif isinstance(msg.body, str):
                    
                    parts = msg.body.split(':')

                    if len(parts) == 2:
                        new_color_name, event_type = parts

                        if new_color_name in colors and event_type in ["emergency", "person"]:

                            if event_type == "emergency":
                                self.agent.environment.update_traffic_light(self.agent.traffic_light_name, new_color_name, "emergency")
                            else:
                                self.agent.environment.update_traffic_light(self.agent.traffic_light_name, new_color_name, "person")
                
            # Wait for some time before changing the color again
            await asyncio.sleep(2)

            # Find the next color name in the cycle
            next_color_name = colors[(colors.index(current_color_name) + 1) % len(colors)]
            
            # Update the traffic light color in the environment
            self.agent.environment.update_traffic_light(self.agent.traffic_light_name, next_color_name, None)
    

        # Changes itself to green/red in case of emergency/person wanting to cross
        async def change_color_ambulance(self):
            # Method to send to the central a warning that it is going to change to green so that the others change to other colors (pre defined)
            msg_change = Message(to=str(self.agent.central_jid))
            msg_change.set_metadata("performative", "request")
            msg_change.body = "changed to green"
            await self.send(msg_change)

            # Change itself to green
            await asyncio.sleep(2)
            self.agent.environment.update_traffic_light(self.agent.traffic_light_name, "green", "emergency")
    
        async def change_color_person(self):
            # Method to send to the central a warning that it is going to change to red so that the others change to other colors (pre defined)
            msg_change = Message(to=str(self.agent.central_jid))
            msg_change.set_metadata("performative", "request")
            msg_change.body = "changed to red"
            await self.send(msg_change)

            # Change itself to red
            await asyncio.sleep(2)
            self.agent.environment.update_traffic_light(self.agent.traffic_light_name, "red", "person")
            
#--------------------------------------------------------------------------------------------------------------------------------------------------------------      

class CentralCordinateAgent(Agent):
    def __init__(self, jid, password, environment, traffic_light_jid_1, traffic_light_jid_2, traffic_light_jid_3):
        super().__init__(jid, password)
        self.environment = environment  # Reference to the simulation environment
        self.traffic_light_jid_1 = traffic_light_jid_1 # JID of the different traffic lights
        self.traffic_light_jid_2 = traffic_light_jid_2
        self.traffic_light_jid_3 = traffic_light_jid_3
        self.message_queue = Queue() # Queue to store the messages by order
        self.lock = Lock() # Method used so that actions occure exclusively to avoid concurrency problems
        
    async def setup(self):
        print(f"CentralCordinateAgent started")
        self.add_behaviour(self.CentralBehaviour(self))

    class CentralBehaviour(CyclicBehaviour):
        def __init__(self, agent, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.agent = agent 
            self.message_queue = Queue()
            self.lock = Lock() 

        async def run(self):

            await asyncio.sleep(1)
     
            # Recieves the messages and stores them
            message = await self.receive(timeout=0.25)
            while message:
                self.message_queue.put(message)
                message = await self.receive(timeout=0.25)
                

            # Processes the messages from the queue
            async with self.agent.lock:
                while not self.message_queue.empty():
                    msg = self.message_queue.get() 

                #--------------------------------------------------------------------------------------------------------------------------------------------------------------     

                    # If the message is from an ambulance
                    if "ambulance" in str(msg.sender):
                        # If the message is to inform there is an emergency
                        if msg.body == "emergency":
                            
                            ambulance_jid = msg.sender

                            # Get the ambulance instance
                            ambulance = self.agent.environment.ambulances[ambulance_jid]
                
                            # Checks if the road where the ambulance is at has a traffic light
                            if ambulance.road.traffic_light != "No traffic light":

                                if ambulance.road.traffic_light == "Traffic_Light_1":
                                    traffic_light_jid = self.agent.traffic_light_jid_1
                                
                                elif ambulance.road.traffic_light == "Traffic_Light_2":
                                    traffic_light_jid = self.agent.traffic_light_jid_2

                                elif ambulance.road.traffic_light == "Traffic_Light_3":
                                    traffic_light_jid = self.agent.traffic_light_jid_3
                
                                # Construct the message to the traffic light agent - only the one on its road
                                traffic_light_msg = Message(to=str(traffic_light_jid))
                                traffic_light_msg.set_metadata("performative", "inform")
                                traffic_light_msg.body = "emergency" 
                                await self.send(traffic_light_msg)

                                print(f"Emergency at {ambulance.ambulance_id}. Changing traffic light {ambulance.road.traffic_light} to green. All the cars on {ambulance.road.name} must stop")

                                # Construct the message to the car agents - only the ones on its road
                                car_agents = list(self.agent.environment.cars.keys())  # Convert dict_keys to a list

                                for car_jid in car_agents:
                                    
                                    car = self.agent.environment.cars[car_jid]  # Get the car instance 
                            
                                    # Ensure car has the same road as the ambulance
                                    if car.road.name == ambulance.road.name:
                                        
                                        car_msg = Message(to=str(traffic_light_jid))
                                        car_msg.set_metadata("performative", "inform")
                                        car_msg.body = "emergency" 
                                        await self.send(car_msg)
                                
                            
                            # The road where the ambulance is at does not have a traffic light
                            else:

                                # Construct the message to the car agents - only the ones on its road
                                car_agents = list(self.agent.environment.cars.keys())  # Convert dict_keys to a list
                                
                                for car_jid in car_agents:
                                    
                                    car = self.agent.environment.cars[car_jid]  # Get the car instance 
                                    
                                    # Ensure car has the same road as the ambulance
                                    if car.road.name == ambulance.road.name:
                                        
                                        car_msg = Message(to=str(car_jid))
                                        car_msg.set_metadata("performative", "inform")
                                        car_msg.body = "emergency" 
                                        await self.send(car_msg)

                                print(f"Emergency at {ambulance.ambulance_id}. All the cars on {ambulance.road.name} must stop.")


                        # If the message is to know the state of the traffic light at the ambulance's road
                        elif msg.body == "color":

                            ambulance_jid = msg.sender

                            # Get the ambulance instance
                            ambulance = self.agent.environment.ambulances[ambulance_jid]

                            if ambulance.road.traffic_light == "Traffic_Light_1":
                                traffic_light_jid = self.agent.traffic_light_jid_1
                            
                            elif ambulance.road.traffic_light == "Traffic_Light_2":
                                traffic_light_jid = self.agent.traffic_light_jid_2

                            elif ambulance.road.traffic_light == "Traffic_Light_3":
                                traffic_light_jid = self.agent.traffic_light_jid_3
                            
                            # Construct the message to the traffic light agent - only the one on its road - to ask for its color
                            traffic_light_msg = Message(to=str(traffic_light_jid))
                            traffic_light_msg.set_metadata("performative", "inform")
                            traffic_light_msg.body = "color" 
                            await self.send(traffic_light_msg)
                            
                            # Wait for a response from the CentralCordinateAgent
                            expected_sender = str(traffic_light_jid)
                            msg_1 = None

                            # Loop to wait for the expected message
                            while not msg_1 or str(msg_1.sender) != expected_sender:
                                msg_1 = await self.receive(timeout=1) 
                
                            if msg_1:
                                if msg_1.body in colors:
                                    
                                    # Sends back the color of the ambulance
                                    ambulance_msg = Message(to=str(ambulance_jid))
                                    ambulance_msg.set_metadata("performative", "inform")
                                    ambulance_msg.body = msg_1.body
                                    await self.send(ambulance_msg)

                #--------------------------------------------------------------------------------------------------------------------------------------------------------------      

                    # If the message is from a car
                    elif "vehicle" in str(msg.sender):
                        
                        # If the message is to ask if it can go ahead
                        if msg.body == "may i go?":

                            car_jid = msg.sender

                            # Get the car instance
                            car = self.agent.environment.cars[car_jid]

                            # If the road where the car is at has a traffic light
                            if car.road.traffic_light != "No traffic light":

                                if car.road.traffic_light == "Traffic_Light_1":
                                    traffic_light_jid = self.agent.traffic_light_jid_1
                                
                                elif car.road.traffic_light == "Traffic_Light_2":
                                    traffic_light_jid = self.agent.traffic_light_jid_2

                                elif car.road.traffic_light == "Traffic_Light_3":
                                    traffic_light_jid = self.agent.traffic_light_jid_3
                                
                                # Construct the message to the traffic light agent - only the one on its road - to ask for its color
                                traffic_light_msg = Message(to=str(traffic_light_jid))
                                traffic_light_msg.set_metadata("performative", "inform")
                                traffic_light_msg.body = "color" 
                                await self.send(traffic_light_msg)

                                # Waits for a response from the traffic light
                                expected_sender = str(traffic_light_jid)
                                msg_2 = None

                                # Loop to wait for the expected message
                                while not msg_2 or str(msg_2.sender) != expected_sender:
                                    msg_2 = await self.receive(timeout=1) 
                    
                                if msg_2:
                                    if msg_2.body in colors:

                                        if msg_2.body == "green":
                                            command = "move"
                                        
                                        else:
                                            command = "stop"
                    

                            # If the road where the car is at has no traffic light, which means it is at road_9 which has a traffic signal
                            else:
                                
                                # Check if there is any vehicle ou ambulance on position 5 on the roads: road_5 and road_6
                                for car_jid, car in self.cars.items():
                                    if car.road.name == "road_5" or car.road.name == "road_6":
                                        if car.position == 5:
                                            command = "give priority"

                                for ambulance_jid, ambulance in self.ambulances.items():
                                    if ambulance.road.name == "road_5" or ambulance.road.name == "road_6":
                                        if ambulance.position == 5:
                                            command = "give priority"


                            # Sends back the command to the car
                            car_msg = Message(to=str(car_jid))
                            car_msg.set_metadata("performative", "inform")
                            car_msg.body = command
                            await self.send(car_msg)

                #--------------------------------------------------------------------------------------------------------------------------------------------------------------      

                    # If the message is from a traffic light
                    elif "traffic_light" in str(msg.sender):

                        # If the message is for the other traffic lights - the sender changed to green so the others must change themselfs to the correspondant colors
                        if msg.body == "changed to green":

                            # Extract the number of the traffic light that sent the msg
                            traffic_light_number = int(str(msg.sender).split("@")[0][-1])

                            # Create the traffic_light_name based on the number extracted above
                            traffic_light_name = f"Traffic_Light_{traffic_light_number}"

                            # Define the new colors based on the traffic light that sent the message
                            new_colors = self.define_new_colors_ambulance(traffic_light_name)

                            # Sends the messages to the other traffic lights with the new colors - the ones they must change to
                            for other_traffic_light, new_color in new_colors.items():
                                change_msg = Message(to=str(other_traffic_light))
                                change_msg.set_metadata("performative", "inform")
                                change_msg.body = f"{new_color}:emergency" # The event is only for print purposes so the user can identify the reason why the traffic light has changed
                                await self.send(change_msg)

                        # If the message is for the other traffic lights - the sender changed to red so that the others must change themselfs to the correspondant colors
                        elif msg.body == "changed to red":

                            # Extract the number of the traffic light that sent the msg
                            traffic_light_number = int(str(msg.sender).split("@")[0][-1])

                            # Create the traffic_light_name based on the number extracted above
                            traffic_light_name = f"Traffic_Light_{traffic_light_number}"

                            # Define the new colors based on the traffic light that sent the message
                            new_colors = self.define_new_colors_person(traffic_light_name)

                            # Sends the messages to the other traffic lights with the new colors - the ones they must change to
                            for other_traffic_light, new_color in new_colors.items():
                                change_msg = Message(to=str(other_traffic_light))
                                change_msg.set_metadata("performative", "inform")
                                change_msg.body = f"{new_color}:person" # The event is only for print purposes so that the user can identify the reason why the traffic light has changed
                                await self.send(change_msg)

                #--------------------------------------------------------------------------------------------------------------------------------------------------------------      

                    # If the message is from a person
                    elif "person" in str(msg.sender):

                        # If the message is to request the traffic light at his road to change to red
                        if msg.body == "change to red":

                            person_jid = msg.sender

                            # Get the person instance
                            person = self.agent.environment.people[person_jid]
            
                            if person.road.zebra_crossing == "Zebra_Crossing_1":
                                traffic_light_jid = self.agent.traffic_light_jid_1
                            
                            elif person.road.zebra_crossing == "Zebra_Crossing_2":
                                traffic_light_jid = self.agent.traffic_light_jid_2

                            elif person.road.zebra_crossing == "Zebra_Crossing_3":
                                traffic_light_jid = self.agent.traffic_light_jid_3

                            # Construct the message to the traffic light agent - only the one on its road - to ask for its color
                            traffic_light_msg = Message(to=str(traffic_light_jid))
                            traffic_light_msg.set_metadata("performative", "inform")
                            traffic_light_msg.body = "color" 
                            await self.send(traffic_light_msg)

                            # Wait for a response from the CentralCordinateAgent
                            expected_sender = str(traffic_light_jid)
                            msg_3 = None

                            # Loop to wait for the expected message
                            while not msg_3 or str(msg_3.sender) != expected_sender:
                                msg_3 = await self.receive(timeout=1) 

                            command = "move" #default command

                            if msg_3:
                                if msg_3.body in colors:
                                    
                                    if msg.body == "red":
                                        command = "move"
                                    else:
                                        # Check if there's an "emergency" message from any ambulance on a road with a traffic light - the ambulance has priority
                                        ambulance_queue = Queue()

                                        # Creates a copy of the message_queue so that the original one is not changed
                                        ambulance_queue.queue = self.message_queue.queue.copy()
                                        
                                        # Checks if theres any emergency on any road with a traffic light
                                        while not ambulance_queue.empty():
                            
                                            ambulance_msg = ambulance_queue.get()

                                            if ambulance_msg.body == "emergency":
                                                ambulance_jid = msg.sender

                                                ambulance = self.agent.environment.ambulances[ambulance_jid]

                                                # If there is some emergency
                                                if ambulance.road.traffic_light != "No traffic light":
                                                    command = "wait"

                                        # If there is not any emergency
                                        if command != "wait":    

                                            # Construct the message to the traffic light agent - only the one on its road - to change the traffic light to red
                                            traffic_light_msg = Message(to=str(traffic_light_jid))
                                            traffic_light_msg.set_metadata("performative", "inform")
                                            traffic_light_msg.body = "person" 
                                            await self.send(traffic_light_msg)
                                            
                                            print(f"Changing {person.road.traffic_light} to red.")

                                            command = "move"

                                    # Send the command (move or wait) to the person
                                    person_msg = Message(to=str(person_jid))
                                    person_msg.set_metadata("performative", "inform")
                                    person_msg.body = command
                                    await self.send(person_msg)


                        


        # Define the new colors based on the traffic light that sent the message
        def define_new_colors_ambulance(self, sender_traffic_light):

            new_colors = {}

            if sender_traffic_light == "Traffic_Light_1":
                new_colors[self.agent.traffic_light_jid_2] = "red"
                new_colors[self.agent.traffic_light_jid_3] = "yellow"

            elif sender_traffic_light == "Traffic_Light_2":
                new_colors[self.agent.traffic_light_jid_1] = "yellow"
                new_colors[self.agent.traffic_light_jid_3] = "red"

            elif sender_traffic_light == "Traffic_Light_3":
                new_colors[self.agent.traffic_light_jid_1] = "red"
                new_colors[self.agent.traffic_light_jid_2] = "yellow"

            return new_colors
        
        def define_new_colors_person(self, sender_traffic_light):

            new_colors = {}

            if sender_traffic_light == "Traffic_Light_1":
                new_colors[self.agent.traffic_light_jid_2] = "yellow"
                new_colors[self.agent.traffic_light_jid_3] = "green"

            elif sender_traffic_light == "Traffic_Light_2":
                new_colors[self.agent.traffic_light_jid_1] = "green"
                new_colors[self.agent.traffic_light_jid_3] = "yellow"

            elif sender_traffic_light == "Traffic_Light_3":
                new_colors[self.agent.traffic_light_jid_1] = "yellow"
                new_colors[self.agent.traffic_light_jid_2] = "green"

            return new_colors

#--------------------------------------------------------------------------------------------------------------------------------------------------------------      

class CarAgent(Agent):
    def __init__(self, jid, password, environment, car_id, road, central_jid):
        super().__init__(jid, password)
        self.environment = environment  # Reference to the simulation environment
        self.car_id = car_id  # Unique identifier for the car, ex: car_1
        self.road = road 
        self.position = 0 # Default position
        self.central_jid = central_jid

    async def setup(self):
        print(f"CarAgent: {self.car_id} started")
        self.add_behaviour(self.CarBehaviour(self)) 

    class CarBehaviour(CyclicBehaviour):
        def __init__(self, agent, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.agent = agent

        async def run(self):

            # Check if the path is clear before moving
            if not self.agent.environment.is_vehicle_ahead(self.agent.jid, "car"):

                await asyncio.sleep(3)
                self.agent.environment.change_road(self.agent.jid, self.agent.car_id, self.agent.road, "car") 
                self.agent.position += 1
                print(f"{self.agent.car_id}: Moving to position {self.agent.position} on {self.agent.road.name}.")

            else:

                # Keep the car's position
                print(f"{self.agent.car_id}: Waiting, there's a vehicle ahead on {self.agent.road.name}.")


            # Wait for a message from the CentralCordinateAgent
            msg = await self.receive(timeout=1)  
            if msg:
                if msg.body == "emergency":

                    # Keep the car's position
                    print(f"{self.agent.car_id}: Stopping due to an emergency on {self.agent.road.name}.")

            if self.agent.position == 4:
                # If the road where the car is at has a traffic light
                if self.agent.road.name in ["road_1", "road_2", "road_3", "road_4", "road_9"]:

                    # Send request to the Central Agent to know if it can go ahead
                    msg = Message(to=str(self.agent.central_jid))
                    msg.set_metadata("performative", "inform")
                    msg.body = "may i go?"
                    await self.send(msg)

                    # Wait for a message from the CentralCordinateAgent
                    msg = await self.receive(timeout=1)  
                    if msg:
                        command = msg.body

                        # If there is an emergency on the car's road
                        if command == "emergency":

                            # Keep the car's position
                            print(f"{self.agent.car_id}: Stopping due to an emergency on {self.agent.road.name}.")

                        # If it can move
                        elif command == "move":

                            self.agent.environment.change_road(self.agent.jid, self.agent.car_id, self.agent.road, "car") 
                            self.agent.position += 1
                            print(f"{self.agent.car_id}: Moving to position {self.agent.position} on {self.agent.road.name}.")

                        # If the traffic light is red
                        elif command == "stop":

                            # Keep the car's position
                            print(f"{self.agent.car_id}: Stopping.")

                        # If it has to let the other cars go ahead
                        elif command == "give priority":
                            
                            # Keep the car's position
                            print(f"{self.agent.car_id}: Giving priority.")


            await asyncio.sleep(3)


#-------------------------------------------------------------------------------------------------------------------------------------------------------------- 

class AmbulanceAgent(Agent):
    def __init__(self, jid, password, environment,  ambulance_id, road, central_jid):
        super().__init__(jid, password)
        self.environment = environment # Reference to the simulation environment
        self.central_jid = central_jid
        self.position = 0  # Default position
        self.ambulance_id = ambulance_id # Unique identifier, ex: ambulance_1
        self.road = road

    async def setup(self):
        print(f"AmbulanceAgent: {self.ambulance_id} started")
        self.add_behaviour(self.AmbulanceBehaviour(self))

    class AmbulanceBehaviour(CyclicBehaviour):
        def __init__(self, agent, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.agent = agent

        async def run(self):

            # Check if the path is clear before moving
            if not self.agent.environment.is_vehicle_ahead(self.agent.jid, "ambulance"):

                await asyncio.sleep(2)
                self.agent.environment.change_road(self.agent.jid, self.agent.ambulance_id, self.agent.road, "ambulance") 
                self.agent.position += 1
                print(f"{self.agent.ambulance_id}: Moving to position {self.agent.position} on {self.agent.road.name}.")

            else:

                print(f"{self.agent.ambulance_id}: Waiting, there's an ambulance ahead on {self.agent.road.name}.")

            # It asks on the 4th position so it has time to communicate without stopping
            if self.agent.position == 4:
                
                # If the road where the ambulance is at has a traffic light
                if self.agent.road.name in ["road_1", "road_2", "road_3", "road_4"]:

                    # Send request to the Central Agent to know the color of the traffic light
                    msg = Message(to=str(self.agent.central_jid))
                    msg.set_metadata("performative", "inform")
                    msg.body = "color"
                    await self.send(msg)

                    # Wait for a response from the CentralCordinateAgent
                    msg_1 = None
                    
                    # Loop to wait for the expected message
                    while not msg_1:
                        msg_1 = await self.receive(timeout=1) 
                  
                    msg_color_traffic_light = msg_1.body

                    if msg_color_traffic_light in ["red", "yellow"]:
                        
                        # Ambulance sends an emergency message to the central agent
                        msg_emergency = Message(to=str(self.agent.central_jid))
                        msg_emergency.set_metadata("performative", "inform")
                        msg_emergency.body = "emergency"
                        await self.send(msg_emergency)
                        
                        # Wait for some time to simulate the ambulance moving
                        await asyncio.sleep(2)
                        
                    # If the traffic light on its road is green
                    else: 
                        print(f"Emergency at {self.agent.ambulance_id}: Traffic Light green. Going forward, be careful.")
                
                # If the road where the ambulance is at does not have a traffic light - it is only necessary to let the cars know they must stop
                else:

                    # Ambulance sends an emergency message to the central agent
                    msg = Message(to=str(self.agent.central_jid))
                    msg.set_metadata("performative", "inform")
                    msg.body = "emergency"
                    await self.send(msg)

                    # Wait for some time to simulate the ambulance moving
                    await asyncio.sleep(2)

            await asyncio.sleep(2)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------

class PersonAgent(Agent):
    def __init__(self, jid, password, central_jid, environment, person_id, road):
        super().__init__(jid, password)
        self.central_jid = central_jid
        self.environment = environment  # Reference to the simulation environment
        self.road = road  # The road where the zebra crossing the person is interested is at
        self.person_id = person_id # Unique identifier, ex: person_1

    async def setup(self):
        print(f"Person Agent: {self.person_id} started")
        self.add_behaviour(self.PersonBehaviour(self))

    class PersonBehaviour(CyclicBehaviour):
        def __init__(self, agent):
            super().__init__()
            self.agent = agent

        async def run(self):

            print(f"{self.agent.person_id} approaching a zebra crossing on {self.agent.road.name}.")

            # Person requests the traffic light, at their intersection, to change to red
            msg_request = Message(to=str(self.agent.central_jid))
            msg_request.set_metadata("performative", "inform")
            msg_request.body = "change to red"
            await self.send(msg_request)

            # Wait for a response from the CentralCordinateAgent
            msg_response = None 

            # Loop to wait for the expected message
            while not msg_response:
                msg_response = await self.receive(timeout=1) 

            if msg_response.body == "move":
                
                print(f"Central Agent responded with: {msg_response.body}. {self.agent.person_id} crossing the street.")
                # the person already crossed so he chooses a new zebra crossing
                self.agent.environment.change_zebra_crossing(self.agent.jid) 

            else: 

                # He needs to wait (the behaviour repetes)
                print(f"Central Agent responded with: {msg_response.body}. {self.agent.person_id} waiting.")

            # Wait for some time to simulate the person approaching a new zebra crossing
            await asyncio.sleep(20)