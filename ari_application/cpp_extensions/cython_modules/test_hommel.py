# test_hommel.py

# Test: 
# cd /Users/lucaspeek/PostDocs/Weeda/NewApp/BrainNav
# export PYTHONPATH=$(pwd):$PYTHONPATH
# python cpp_extensions/cython_modules/test_hommel.py

# Import the compiled module
from cpp_extensions.cython_modules import hommel

# Test data
m = 10
p = [0.01 * i for i in range(1, m + 1)]
simesfactor = [1.0] * (m + 1)
simes = True

# Test the functions
print("findhull:")
print(hommel.py_findhull(m, p))

print("\nfindalpha:")
print(hommel.py_findalpha(p, m, simesfactor, simes))

print("\nfindsimesfactor:")
print(hommel.py_findsimesfactor(simes, m))

print("\nadjustedElementary:")
print(hommel.py_adjustedElementary(p, simesfactor, m, simesfactor))

print("\nadjustedIntersection:")
print(hommel.py_adjustedIntersection(p[0], simesfactor, m, simesfactor))

print("\nfindHalpha:")
print(hommel.py_findHalpha(simesfactor, 0.5, m))

print("\nfindConcentration:")
print(hommel.py_findConcentration(p, 1.0, 5, 0.5, m))

print("\nfindDiscoveries:")
print(hommel.py_findDiscoveries([1, 2, 3, 4, 5], p, 1.0, 5, 0.5, 5, m))