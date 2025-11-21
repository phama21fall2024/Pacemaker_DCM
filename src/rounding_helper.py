class RoundingHelper:

    @staticmethod
    def round_value(value, low, high, step):
        """Clamps AND rounds value using given limits and increment."""
        try:
            val = float(value)
        except:
            return None

        # Clamp range
        if val < low:
            val = low
        elif val > high:
            val = high

        # Round to nearest step
        rounded = round((val - low) / step) * step + low

        # Clamp again
        if rounded < low:
            rounded = low
        if rounded > high:
            rounded = high

        return rounded
    
    def round_lrl(value, low=30.0, high=175.0):
        try:
            val = float(value)
        except:
            return None

        if val < low:
            val = low
        elif val > high:
            val = high

        if val <= 50.0:
            base = 30.0
            step = 5.0
        elif val <= 90.0:
            base = 50.0
            step = 1.0
        else:
            base = 90.0
            step = 5.0

        rounded = base + round((val - base) / step) * step

        if rounded < low:
            rounded = low
        if rounded > high:
            rounded = high

        return rounded