
import asyncio
from environment import Environment
from agents import CarAgent, TrafficLightAgent, CentralCordinateAgent, AmbulanceAgent, PersonAgent

async def main():
    # XMPP credentials for your agents
    car_jid_1 = "vehicle1@localhost"
    car_jid_2 = "vehicle2@localhost"
    car_jid_3 = "vehicle3@localhost"
    car_jid_4 = "vehicle4@localhost"

    person_jid_1 = "person1@localhost"
    person_jid_2 = "person2@localhost"

    ambulance_jid_1 = "ambulance1@localhost"
    ambulance_jid_2 = "ambulance2@localhost"

    traffic_light_jid_1 = "traffic_light1@localhost"
    traffic_light_jid_2 = "traffic_light2@localhost"
    traffic_light_jid_3 = "traffic_light3@localhost"

    central_jid = "central@localhost"

    password = "060303"  # Change to your desired password
    

    # Instantiate the environment
    env = Environment()  


    # Instantiate the agents with their JID and password
    car_agent_1 = CarAgent(car_jid_1, password, env, "car_1", env.road_1, central_jid)
    car_agent_2 = CarAgent(car_jid_2, password, env, "car_2", env.road_2, central_jid)
    car_agent_3 = CarAgent(car_jid_3, password, env, "car_3", env.road_3, central_jid)
    car_agent_4 = CarAgent(car_jid_4, password, env, "car_4", env.road_4, central_jid)

    ambulance_agent_1 = AmbulanceAgent(ambulance_jid_1, password, env, "ambulance_1", env.road_1, central_jid)
    ambulance_agent_2 = AmbulanceAgent(ambulance_jid_2, password, env, "ambulance_2", env.road_4, central_jid)

    traffic_light_agent_1 = TrafficLightAgent(traffic_light_jid_1, password, env, "Traffic_Light_1", central_jid)
    traffic_light_agent_2 = TrafficLightAgent(traffic_light_jid_2, password, env, "Traffic_Light_2", central_jid)
    traffic_light_agent_3 = TrafficLightAgent(traffic_light_jid_3, password, env, "Traffic_Light_3", central_jid)

    central_agent = CentralCordinateAgent(central_jid, password, env, traffic_light_jid_1, traffic_light_jid_2, traffic_light_jid_3)

    person_agent_1 = PersonAgent(person_jid_1, password, central_jid, env, "person_1", env.road_1)
    person_agent_2 = PersonAgent(person_jid_2, password, central_jid, env, "person_2", env.road_4)



    # Add the car_agents to the environment
    env.add_car_agent(car_agent_1)
    env.add_car_agent(car_agent_2) 
    env.add_car_agent(car_agent_3) 
    env.add_car_agent(car_agent_4) 

    env.add_ambulance_agent(ambulance_agent_1)
    env.add_ambulance_agent(ambulance_agent_2)
    
    env.add_person_agent(person_agent_1)
    env.add_person_agent(person_agent_2)



    # Start the agents
    await car_agent_1.start(auto_register=True)
    await car_agent_2.start(auto_register=True)
    await car_agent_3.start(auto_register=True)
    await car_agent_4.start(auto_register=True)

    await ambulance_agent_1.start(auto_register=True)
    await ambulance_agent_2.start(auto_register=True)

    await traffic_light_agent_1.start(auto_register=True)
    await traffic_light_agent_2.start(auto_register=True)
    await traffic_light_agent_3.start(auto_register=True)

    await central_agent.start(auto_register=True)

    await person_agent_1.start(auto_register=True)
    await person_agent_2.start(auto_register=True)


    try:
        await asyncio.sleep(60)
    except asyncio.CancelledError:
        pass 


    # Stop the agents
    await car_agent_1.stop()
    await car_agent_2.stop()
    await car_agent_3.stop()
    await car_agent_4.stop()

    await ambulance_agent_1.stop()
    await ambulance_agent_2.stop()

    await traffic_light_agent_1.stop()
    await traffic_light_agent_2.stop()
    await traffic_light_agent_3.stop()

    await central_agent.stop()

    await person_agent_1.stop()
    await person_agent_2.stop()

if __name__ == "__main__":
    asyncio.run(main())
