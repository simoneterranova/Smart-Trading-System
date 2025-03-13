import numpy as np

class TradingOptimization:
    def __init__(self, trading_system):
        self.trading_system = trading_system

    def optimize_trading(self):
        """ Optimizes trading quantities and prices for each prosumer. """
        duration = len(self.trading_system.load_curve)
        num_partners = len(self.trading_system.trading_partners)

        trading_quantities = np.zeros((num_partners, duration))
        trading_prices = np.zeros((num_partners, duration))

        # Parameters of the Gaussian distribution
        peak_hour = 12  # Peak production at noon
        sigma = 2.5     # Width of the Gaussian distribution

        # Generate a normalized Gaussian curve
        hours = np.arange(duration)
        gaussian_curve = np.exp(-0.5 * ((hours - peak_hour) / sigma) ** 2)
        gaussian_curve /= gaussian_curve.max()  # Normalize the curve between 0 and 1
        gaussian_curve *= 0.6

        for i, partner in enumerate(self.trading_system.trading_partners):
            # Scale the curve based on the partner's capacity 
            max_energy = partner.capacity  # Maximum capacity of the prosumer
            partner_production = gaussian_curve * max_energy

            for hour in range(duration):
                # Partner's production follows the scaled Gaussian curve
                production = partner_production[hour]

                # Current load of the grid
                load = self.trading_system.load_curve[hour]

                # Calculate the energy available for sale
                to_sell = production - load if production > load else production
                to_sell = max(to_sell, 0) # Ensure it is not negative

                # Dynamically update the price based on production and consumption
                if to_sell > production/2:
                    partner.price_curve[hour] *= 0.95  # Reduce the price by 5% if production is greater than consumption
                else:
                    partner.price_curve[hour] *= 1.05  # Increase the price by 5% if production is less than consumption

                # Assign energy and price
                trading_quantities[i, hour] = to_sell
                trading_prices[i, hour] = partner.price_curve[hour]

        return trading_quantities, trading_prices, None
