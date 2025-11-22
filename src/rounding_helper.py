class RoundingHelper:

    @staticmethod
    def round_value(value, low, high, step):
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
    