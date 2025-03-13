import numpy as np

class TradingPartner:
    def __init__(self, name, capacity, reliability, base_price_curve):
        self.name = name
        self.capacity = capacity
        self.reliability = reliability
        # Initialize individual price curve with a 5% variation
        variazione = np.random.uniform(0.95, 1.05, size=len(base_price_curve))
        self.price_curve = base_price_curve * variazione

    def score(self, hour):
        """ Evaluates the score based on the formula price / (capacity * reliability)."""
        return self.price_curve[hour] / (self.capacity * self.reliability)

class TradingSystem:
    def __init__(self, load_curve, base_price_curve, production_curve, constraints, trading_partners, consumers):
        self.load_curve = load_curve
        self.base_price_curve = base_price_curve
        self.constraints = constraints
        self.trading_partners = trading_partners
        self.consumers = consumers
        self.production_curve = production_curve
        # Generation of random percentages that sum up to 1
        num_partners = len(trading_partners)
        num_consumers = len(consumers)
        num_actors = num_partners + num_consumers
        self.load_distribution = np.random.dirichlet(np.ones(num_actors), size=1)[0]  # random percentages

    def get_price(self, partner_index, hour):
        """ Returns the price for a specific hour and prosumer."""
        return self.trading_partners[partner_index].price_curve[hour]

    def get_user_load(self, hour, partner_index):
        """ Returns the load for a specific hour and partner."""
        # Load is calculated as a fraction of the original load_curve
        return self.load_curve[hour] * self.load_distribution[partner_index]

    def get_user_production(self, hour, partner_index):
        """ Returns the production for a specific hour and partner."""
        # Production is calculated based on the prosumer's capacity and a Gaussian curve
        partner = self.trading_partners[partner_index]
        peak_hour = 12
        sigma = 4
        gaussian_value = np.exp(-0.5 * ((hour - peak_hour) / sigma) ** 2)
        gaussian_value /= np.exp(-0.5 * ((0 - peak_hour) / sigma) ** 2) # Normalizes with respect to the peak
        production = partner.capacity * (0.95 + 0.1 * gaussian_value)  # Variation between 95% and 105%
        return production

    def distribute_load_curve(self):
        """ Distributes the total load curve to the partners following the percentages."""
        num_partners = len(self.trading_partners)
        num_consumers = len(self.consumers)
        num_actors = num_partners + num_consumers
        distributed_curves = np.zeros((num_actors, len(self.load_curve)))
        
        # Evaluate the total load curve (load_curve * number_prosumer)
        total_load_curve = self.load_curve * len(self.trading_partners)

        # Distribute the load based on the percentages
        for i in range(num_actors):
            distributed_curves[i] = total_load_curve * self.load_distribution[i]

        # Normalizes the distributed curves to ensure that the sum is equal to the total load curve
        sum_distributed = np.sum(distributed_curves, axis=0)
        normalization_factors = total_load_curve / sum_distributed
        distributed_curves = distributed_curves * normalization_factors

        return distributed_curves

    def select_best_prosumer_for_consumer(self, consumer, hour):
        """ Selects the best prosumer for a consumer based on the score at the given hour."""
        best_score = float('inf')
        best_prosumer = None

        for partner in self.trading_partners:
            score = partner.score(hour)
            if score < best_score:
                best_score = score
                best_prosumer = partner

        return best_prosumer

class Consumer:
    def __init__(self, name, load):
        self.name = name
        self.load = load  # Consumer load