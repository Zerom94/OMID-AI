def _validate_non_negative_int(n):
    """Validate that n is a non‑negative integer.
    
    Raises:
        TypeError: If n is not an int.
        ValueError: If n is negative.
    """
    if not isinstance(n, int):
        raise TypeError(f"Expected int, got {type(n).__name__}")
    if n < 0:
        raise ValueError("Factorial is undefined for negative integers")
    return n


def factorial_iterative(n):
    """Return the factorial of a non‑negative integer using an iterative approach.
    
    Example:
        >>> factorial_iterative(5)
        120
    """
    _validate_non_negative_int(n)
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


def factorial_recursive(n):
    """Return the factorial of a non‑negative integer using recursion.
    
    Example:
        >>> factorial_recursive(5)
        120
    """
    _validate_non_negative_int(n)
    if n in (0, 1):
        return 1
    return n * factorial_recursive(n - 1)

if __name__ == "__main__":
    # Demo usage
    for func in (factorial_iterative, factorial_recursive):
        print(f"{func.__name__}(5) =", func(5))
        try:
            func(-1)
        except Exception as e:
            print(f"Calling {func.__name__}(-1) raised {type(e).__name__}: {e}")
        try:
            func(3.5)
        except Exception as e:
            print(f"Calling {func.__name__}(3.5) raised {type(e).__name__}: {e}")
