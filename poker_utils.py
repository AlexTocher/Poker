

# Define the scale boundaries in seconds
# We use standard scientific notation for clarity (e.g., 1e-6 seconds = 1 microsecond)
TIME_SCALES = (
    # Threshold (in seconds), Unit Name
    (31536000.0, "years"),      # 365 days     
    (86400.0, "days"),          # 24 hours
    (3600.0, "h"),          # 60 minutes
    (60.0, "min"),          # 60 seconds
    (1.0, "s"),           # 1 second
    (1e-3, "ms"),     # 1/1,000 second
    (1e-6, "μs"),     # 1/1,000,000 second
    (1e-9, "ns"),      # 1/1,000,000,000 second
)

def format_time(seconds: float) -> str:
    """
    Converts a time duration in seconds into a human-readable string, 
    automatically selecting the most appropriate scale (e.g., '1.5 seconds', 
    '500 milliseconds', '2 days').

    Args:
        seconds (float): The time duration in seconds.

    Returns:
        str: A formatted string representing the duration.
    """
    if seconds == 0:
        return "0 seconds"

    # Ensure the duration is positive for calculation
    abs_seconds = abs(seconds)
    
    # Iterate through scales from largest to smallest
    for threshold, unit in TIME_SCALES:
        # If the absolute time is greater than or equal to the threshold for the unit,
        # this is the most appropriate unit to use (e.g., 65 seconds is > 60, so use minutes)
        if abs_seconds >= threshold:
            # Calculate the formatted value
            value = abs_seconds / threshold
            
            # Use '%.2f' for two decimal places unless the value is very large
            if value >= 10:
                 formatted_value = f"{value:.1f}"
            else:
                 formatted_value = f"{value:.2f}"
            
            # Construct the final string
            return f"{formatted_value} {unit}"
            
    # If the time is smaller than the smallest scale (nanoseconds), 
    # use nanoseconds or return a very small number in scientific notation.
    # Since the scale is inclusive, this fallback is primarily for edge cases.
    nanoseconds = abs_seconds / 1e-9
    return f"{nanoseconds:.2f} ns"
