import numpy as np
import pandas as pd
import json
import matplotlib.pyplot as plt
from trading_system import TradingSystem, TradingPartner, Consumer
from optimization import TradingOptimization

def load_csv_data(price_file, load_file, production_file):
    """Load price and load curve data from CSV files."""
    price_data = pd.read_csv(price_file, index_col=0)
    load_data = pd.read_csv(load_file, index_col=0)
    production_data = pd.read_csv(production_file, index_col=0)
    return price_data, load_data, production_data

def assign_consumers_to_prosumers(trading_system, trading_partners, consumers, sim_duration, base_price_curve):
    """
    Assign consumers to prosumers based on the production capacity of the prosumers.
    Each consumer can take energy from a prosumer only until the sum of the energy
    they take does not exceed the energy injected by that prosumer in that hour.
    Also, each prosumer cannot have more than 1 consumer using their energy in an hour.
    If a consumer does not find an available prosumer, they use normal electricity prices.
    """
    # Initialize a list to keep track of the remaining energy of each prosumer for each hour
    remaining_energy = np.zeros((len(trading_partners), sim_duration))
    for i, partner in enumerate(trading_partners):
        for hour in range(sim_duration):
            remaining_energy[i, hour] = trading_system.get_user_production(hour, i)

    # Initialize a list to keep track of the number of consumers assigned to each prosumer for each hour
    consumer_count = np.zeros((len(trading_partners), sim_duration), dtype=int)

    # Initialize a dictionary to keep track of the assignments
    assignments = {}

    # Initialize a list to keep track of the normal energy prices for each consumer
    normal_prices = {}

    # Assign consumers to prosumers
    for hour in range(sim_duration):
        # Sort the prosumers based on the score (from best to worst)
        sorted_partners = sorted(trading_partners, key=lambda x: x.score(hour))
        
        # Assign consumers to prosumers in order of score, respecting the constraints
        for consumer in consumers:
            best_prosumer = None
            for partner in sorted_partners:
                partner_index = trading_partners.index(partner)
                # Verify that the prosumer has energy available and does not already have 1 consumer assigned
                if remaining_energy[partner_index, hour] > 0 and consumer_count[partner_index, hour] < 1:
                    best_prosumer = (partner, partner_index)
                    break

            # Assign the consumer to the prosumer and reduce the remaining energy
            if best_prosumer:
                partner, partner_index = best_prosumer
                assignments[(consumer, hour)] = partner
                load = trading_system.get_user_load(hour, partner_index)
                remaining_energy[partner_index, hour] -= load
                consumer_count[partner_index, hour] += 1
            else:
                # If no prosumer is available, use normal electricity prices
                normal_prices[(consumer, hour)] = base_price_curve[hour]

    return assignments, normal_prices

def main():
    # Simulation
    sim_duration = 24  # Duration in hours
    while True:
        try:
            simulation_day = input("Enter the day of the week for the simulation (e.g., 'Sunday'): ").capitalize()
            if simulation_day not in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
                raise ValueError("Invalid day of the week. Please enter a valid day (e.g., 'Sunday').")
            break
        except ValueError as e:
            print(e)

    # User input for number of prosumers and consumers
    while True:
        try:
            number_prosumer = int(input("Enter the number of prosumers (e.g., 3): "))
            if number_prosumer < 0:
                raise ValueError("The number of prosumers must be a non-negative integer.")
            break
        except ValueError as e:
            print(f"Invalid input: {e}")

    while True:
        try:
            number_consumer = int(input("Enter the number of consumers (e.g., 3): "))
            if number_consumer < 0:
                raise ValueError("The number of consumers must be a non-negative integer.")
            break
        except ValueError as e:
            print(f"Invalid input: {e}")

    price_file = "price_curve.csv"
    load_file = "load_curve.csv"
    production_file = "production_curve.csv"
    price_data, load_data, production_data = load_csv_data(price_file, load_file, production_file)

    # Define the curve for the simulation day
    base_price_curve = price_data.loc[simulation_day].values.astype(float)
    load_curve = load_data.loc[simulation_day].values.astype(float)
    production_curve = production_data.loc[simulation_day].values.astype(float)

    # Evaluate the total load curve (load_curve * number_prosumer)
    total_load_curve = number_prosumer * load_curve

    # Load trading constraints
    with open("constraints.json") as fp:
        constraints = json.load(fp)

    # Define trading partners
    trading_partners = [
        TradingPartner(name=f"Producer {chr(65 + i)}", 
                       capacity=np.random.uniform(15, 25), 
                       reliability=np.random.uniform(0.85, 0.95),
                       base_price_curve=base_price_curve)
        for i in range(number_prosumer)
    ]

    # Create consumers
    consumers = [
        Consumer(name=f"Consumer {i + 1}", load=0)
        for i in range(number_consumer)
    ]

    # Create the trading system
    trading_system = TradingSystem(load_curve, base_price_curve, production_curve, constraints, trading_partners, consumers)

    # Distribute the total load to the partners
    distributed_load_curves = trading_system.distribute_load_curve()

    # Assign consumers to prosumers with the new policy
    assignments, normal_prices = assign_consumers_to_prosumers(trading_system, trading_partners, consumers, sim_duration, base_price_curve)

    trading_optimization = TradingOptimization(trading_system)
    trading_quantities, trading_prices, partner_details = trading_optimization.optimize_trading()

    # Print the details of the assignments
    print("------------" * 10)
    print("\nSelection of the best prosumers for each consumer:")
    for consumer in consumers:
        print(f"\n{consumer.name}:")
        for hour in range(sim_duration):
            best_prosumer = assignments.get((consumer, hour), None)
            if best_prosumer:
                print(f"  Hour {hour}: selects {best_prosumer.name} with score {best_prosumer.score(hour):.4f}")
            else:
                print(f"  Hour {hour}: No prosumer available. Using normal electricity prices: {normal_prices.get((consumer, hour), 'N/A'):.4f}")

    # Print the trading details
    print("\nTrading Details:")
    for i, partner in enumerate(trading_partners):
        print(f"\nPartner: {partner.name}, Scores: {[partner.score(hour) for hour in range(sim_duration)]}")
        for hour in range(sim_duration):
            consumed = distributed_load_curves[i][hour]
            injected = trading_quantities[i][hour]
            price = trading_prices[i][hour]
            print(f"  Hour {hour}: Consumed: {consumed:.2f}, Injected: {injected:.2f}, Price: {price:.2f}")
        print("-" * 50)

    # Print the consumption of the consumers
    print("\nConsumer Consumption:")
    for i, consumer in enumerate(consumers):
        print(f"\nConsumer {consumer.name} Load: {consumer.load:.2f} kW")
        for hour in range(sim_duration):
            load = distributed_load_curves[i + len(trading_partners)][hour]
            print(f"  Hour {hour}: Consumed: {load:.2f} kW")

    # Plot: Prices of the prosumers
    fig, ax = plt.subplots(figsize=(12, 7))
    for i, partner in enumerate(trading_partners):
        ax.plot(range(sim_duration), trading_prices[i], label=f"{partner.name} Price", linestyle='--')

    ax.set_xlabel('Hour')
    ax.set_ylabel('Price (€/kWh)')
    ax.set_title(f'Prosumer Prices - {simulation_day}')
    ax.legend()
    ax.grid()
    plt.show()

    # Plot: Contributes of the partners (consumption, injection) and total load
    fig, ax = plt.subplots(figsize=(12, 7))
    for i, partner in enumerate(trading_partners):
        ax.plot(range(sim_duration), trading_quantities[i], label=f"{partner.name} Injected")
        ax.plot(range(sim_duration), distributed_load_curves[i], label=f"{partner.name} Consumed", linestyle='--')

    # Power consumed by consumers
    for i, consumer in enumerate(consumers):
        ax.plot(range(sim_duration), distributed_load_curves[i + len(trading_partners)], label=f"{consumer.name} Consumed", linestyle=':')

    ax.plot(range(sim_duration), total_load_curve, label="Total Load Curve", color='black', linewidth=2)
    ax.set_xlabel('Hours')
    ax.set_ylabel('Load (kW)')
    ax.set_title(f'Total Load Curve and Partner Contributions - {simulation_day}')
    ax.legend()
    ax.grid()
    plt.show()

    # Plot: Energy injected and consumed by various actors
    fig, ax = plt.subplots(figsize=(12, 7))
    for i, partner in enumerate(trading_partners):
        ax.plot(range(sim_duration), trading_quantities[i], label=f"{partner.name} Injected")
        ax.plot(range(sim_duration), distributed_load_curves[i], label=f"{partner.name} Consumed", linestyle='--')

    for i, consumer in enumerate(consumers):
        ax.plot(range(sim_duration), distributed_load_curves[i + len(trading_partners)], label=f"{consumer.name} Consumed", linestyle=':')

    ax.set_xlabel('Hour')
    ax.set_ylabel('Energy (kW)')
    ax.set_title(f'Energy Injected and Consumed by Various Actors - {simulation_day}')
    ax.legend()
    ax.grid()
    plt.show()


    # Plot: Energy injected and consumed by each partner separately
    for i, partner in enumerate(trading_partners):
        fig, ax = plt.subplots(figsize=(12, 7))
        ax.plot(range(sim_duration), trading_quantities[i], label=f"{partner.name} Injected", color='blue')
        ax.plot(range(sim_duration), distributed_load_curves[i], label=f"{partner.name} Consumed", color='red', linestyle='--')
        ax.set_xlabel('Hour')
        ax.set_ylabel('Energy (kW)')
        ax.set_title(f'Energy Injected and Consumed by {partner.name} - {simulation_day}')
        ax.legend()
        ax.grid()
        plt.show()

    # Plot: Price of single consumer with score policy vs random policy
    fig, ax = plt.subplots(figsize=(12, 7))
    for i, consumer in enumerate(consumers):
        # Price with score policy
        price_with_score = []
        for hour in range(sim_duration):
            best_prosumer = assignments.get((consumer, hour), None)
            if best_prosumer:
                price_with_score.append(best_prosumer.price_curve[hour])
            else:
                # If no prosumer is available, use normal electricity prices
                price_with_score.append(normal_prices.get((consumer, hour), base_price_curve[hour]))
        
        ax.plot(range(sim_duration), price_with_score, label=f"{consumer.name} (Score Policy)", linestyle='-')

        # Price with random policy
        price_random = [trading_partners[np.random.randint(0, len(trading_partners))].price_curve[hour] for hour in range(sim_duration)]
        ax.plot(range(sim_duration), price_random, label=f"{consumer.name} (Random Policy)", linestyle='--')

    ax.set_xlabel('Hour')
    ax.set_ylabel('Price (€/kWh)')
    ax.set_title(f'Consumer Prices: Score Policy vs Random Policy - {simulation_day}')
    ax.legend()
    ax.grid()
    plt.show()

    distributed_load_curves = trading_system.distribute_load_curve()

    # Verify that the sum of the distributed curves is equal to the total load curve
    sum_distributed = np.sum(distributed_load_curves, axis=0)
    print("Total Load Curve:", total_load_curve)
    print("Sum of Distributed Curves:", sum_distributed)
    print("Are they equal?", np.allclose(total_load_curve, sum_distributed))

if __name__ == "__main__":
    main()