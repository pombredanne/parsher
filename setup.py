from setuptools import setup, find_packages

setup(name='parsher',
        version='0.1.0',
        description='Parsher, a python module to parse bash scripts',
        author='Jonathan W Goodwin',
        url='https://github.com/jonathanwgoodwin/parsher',
        packages=find_packages(),
        include_package_data=True,
        install_requires=[],
        zip_safe=False,
        # entry_points={
        #   'console_scripts':['parsher=module_name.file_name:main'],
        #   }
        test_suite = "parsher.tests.test_all")
