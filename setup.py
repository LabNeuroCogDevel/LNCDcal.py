from setuptools import setup

setup(name='LNCDcal',
      version='0.2.1',
      description='google calendar for the LNCD',
      url='http://github.com/LabNeuroCogDevel/LNCDcal.py',
      author='Will Foran',
      author_email='willforan+github@gmail.com',
      license='MIT',
      packages=['LNCDcal'],
      install_requires=[
          'configparser',
          'httplib2',
          'oauth2client',
          'pytz',
          'google-api-python-client'
       ],
      zip_safe=False)

