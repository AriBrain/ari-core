# from setuptools import setup, Extension
# from Cython.Build import cythonize
# import numpy as np

# extensions = [
#     Extension(
#         name="my_application.cython.findsimesfactor",
#         sources=["my_application/cython/findsimesfactor.pyx", "my_application/cython/findsimesfactor.cpp"],
#         language="c++",
#         include_dirs=[np.get_include()],  # Include numpy headers
#     ),
# ]

# setup(
#     name="ARIBrain",
#     version="0.1.0",
#     description="ARIBrain package",
#     author="Lucas Peek",
#     author_email="lucaspeek@live.nl",
#     packages=["ARIBrain", "ARIBrain.cython"],
#     ext_modules=cythonize(extensions),
#     install_requires=[
#         "numpy",
#         # Add other dependencies here
#     ],
#     setup_requires=[
#         "cython",
#         "numpy",
#     ],
#     test_suite="tests",
# )


# from setuptools import setup, Extension
# from Cython.Build import cythonize
# import numpy as np
# import os


# # Get the absolute path of the current directory
# current_dir = os.path.dirname(os.path.abspath(__file__))

# # Define the common sources
# common_sources = [
#     os.path.join(current_dir, "cpp_extensions/cpp_sources/hommel.cpp"),
# ]

# # Compiler and linker arguments for debugging
# debug_args = ["-g", "-O0", "-Wall"]

# extensions = [
#     Extension(
#         name="cpp_extensions.cython_modules.hommel",
#         sources=[
#             os.path.join(current_dir, "cpp_extensions/cython_modules/hommel.pyx"),
#             os.path.join(current_dir, "cpp_extensions/cpp_sources/hommel.cpp")
#         ],
#         language="c++",
#         include_dirs=[np.get_include()],  # Include numpy headers
#         extra_compile_args=debug_args,    # Add debugging arguments
#         extra_link_args=debug_args,        # Add debugging arguments
#     ),
#     Extension(
#         name="cpp_extensions.cython_modules.ARICluster",
#         sources=[
#             os.path.join(current_dir, "cpp_extensions/cython_modules/ARICluster.pyx"),
#             os.path.join(current_dir, "cpp_extensions/cpp_sources/ARICluster.cpp"),
#             *common_sources  # Include common sources for linkage
#         ],
#         language="c++",
#         include_dirs=[np.get_include()],  # Include numpy headers
#         extra_compile_args=debug_args,    # Add debugging arguments
#         extra_link_args=debug_args,        # Add debugging arguments
#     ),
# ]

# setup(
#     name="ARI",
#     ext_modules=cythonize(extensions),
#     include_dirs=[np.get_include()],
#     extra_compile_args=debug_args,    # Add debugging arguments
#     extra_link_args=debug_args        # Add debugging arguments

# )




# from setuptools import setup, Extension
# from Cython.Build import cythonize
# import numpy as np
# import os

# # Get the absolute path of the current directory
# current_dir = os.path.dirname(os.path.abspath(__file__))

# # Define the common sources
# common_sources = [
#     os.path.join(current_dir, "cpp_extensions/cpp_sources/hommel.cpp"),
# ]

# # Compiler and linker arguments for debugging
# debug_args = ["-g", "-O0", "-Wall"]

# extensions = [
#     Extension(
#         name="cpp_extensions.cython_modules.hommel",
#         sources=[
#             os.path.join(current_dir, "cpp_extensions/cython_modules/hommel.pyx"),
#             os.path.join(current_dir, "cpp_extensions/cpp_sources/hommel.cpp")
#         ],
#         language="c++",
#         include_dirs=[np.get_include()],  # Include numpy headers
#         extra_compile_args=debug_args,    # Add debugging arguments
#         extra_link_args=debug_args,        # Add debugging arguments
#     ),
#     Extension(
#         name="cpp_extensions.cython_modules.ARICluster",
#         sources=[
#             os.path.join(current_dir, "cpp_extensions/cython_modules/ARICluster.pyx"),
#             os.path.join(current_dir, "cpp_extensions/cpp_sources/ARICluster.cpp"),
#             *common_sources  # Include common sources for linkage
#         ],
#         language="c++",
#         include_dirs=[np.get_include()],  # Include numpy headers
#         extra_compile_args=debug_args,    # Add debugging arguments
#         extra_link_args=debug_args,        # Add debugging arguments
#     ),
# ]

# setup(
#     name="ARI",
#     ext_modules=cythonize(extensions),
#     include_dirs=[np.get_include(), os.path.join(current_dir, "cpp_extensions/cpp_sources")],
#     install_requires=[
#         "numpy",
#         "cython"
#     ],
#     setup_requires=[
#         "cython",
#         "numpy",
#     ],
# )




from setuptools import setup, Extension, find_packages
from Cython.Build import cythonize
import numpy as np
import os

current_dir = os.path.dirname(os.path.abspath(__file__))

debug_args = ["-g", "-O0", "-Wall"]
common_sources = [os.path.join(current_dir, "ari_application/cpp_extensions/cpp_sources/hommel.cpp")]

extensions = [
    Extension(
        name="ari_application.cpp_extensions.cython_modules.hommel",
        sources=[
            os.path.join(current_dir, "ari_application/cpp_extensions/cython_modules/hommel.pyx"),
            os.path.join(current_dir, "ari_application/cpp_extensions/cpp_sources/hommel.cpp")
        ],
        language="c++",
        include_dirs=[np.get_include()],
        extra_compile_args=debug_args,
        extra_link_args=debug_args,
    ),
    Extension(
        name="ari_application.cpp_extensions.cython_modules.ARICluster",
        sources=[
            os.path.join(current_dir, "ari_application/cpp_extensions/cython_modules/ARICluster.pyx"),
            os.path.join(current_dir, "ari_application/cpp_extensions/cpp_sources/ARICluster.cpp"),
            *common_sources
        ],
        language="c++",
        include_dirs=[np.get_include()],
        extra_compile_args=debug_args,
        extra_link_args=debug_args,
    ),
]

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="aribrain",
    version="0.1.0",
    packages=find_packages(),
    ext_modules=cythonize(extensions),
    include_dirs=[np.get_include()],
    python_requires=">=3.10.11,<=3.10.14"
    install_requires=requirements,
    entry_points={
        'gui_scripts': [
            'aribrain = ari_application.main:main'
        ]
    },
)


# Make sure you have a C++ compiler installed:

# 	•	Linux: sudo apt-get install g++
# 	•	macOS: brew install gcc
# 	•	Windows: Install Visual Studio with C++ build tools

# python setup.py build_ext --inplace


# The .pyx file is a Cython file that acts as a bridge between Python and C++.
# 	•	Import Statements: The file uses Cython’s capabilities to import C++ functionalities. 
#       Specifically, it imports the vector from the C++ Standard Library.
# 	•	Extern Block: This block declares the external C++ function (findsimesfactor) so 
#       Cython knows how to call it.
# 	•	Python Wrapper Function: A Python-friendly function (py_findsimesfactor) is defined, 
#       which calls the C++ function and converts the result into a Python list.