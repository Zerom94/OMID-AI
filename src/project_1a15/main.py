def fibonacci(n):
    """Return the nth Fibonacci number (0-indexed)."""
    if n < 0:
        raise ValueError('n must be non-negative')
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a

# Example usage:
if __name__ == "__main__":
    for i in range(10):
        print(fibonacci(i))
