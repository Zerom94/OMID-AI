def factorial(n):
    if n<0:
        raise ValueError('Negative input')
    res=1
    for i in range(2, n+1):
        res*=i
    return res

if __name__=='__main__':
    import sys
    n=int(sys.argv[1]) if len(sys.argv)>1 else 5
    print(factorial(n))