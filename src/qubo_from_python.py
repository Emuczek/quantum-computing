import sympy as sp
import numpy as np
from typing import Dict, Tuple, Any, Callable
import re

class SymbolicVariableArray:
    """
    A dict-like object that creates SymPy symbols on-the-fly when accessed.
    
    Usage:
        x = SymbolicVariableArray('x')
        expr = x[0,1,2]  # Creates Symbol('x_0_1_2')
    """
    
    def __init__(self, name: str):
        self.name = name
        self._cache = {} 
    
    def __getitem__(self, key):

        if not isinstance(key, tuple):
            key = (key,)
        
        if key not in self._cache:
            var_name = f"{self.name}_{'_'.join(map(str, key))}"
            self._cache[key] = sp.Symbol(var_name, binary=True)
        
        return self._cache[key]
    
    def get_all_variables(self):
        """Return all created variables as a sorted list."""
        return sorted(self._cache.values(), key=lambda s: s.name)