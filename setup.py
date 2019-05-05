from setuptools import setup

setup(
    name='aioacme',
    version='0.0.1',
    description='Asynchronous ACME client library',
    python_requires='>=3.6',
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Security',
        'Topic :: Security :: Cryptography',
    ],
    packages=['aioacme'],
    install_requires=[
        'aiohttp>=3.5.4,<4',
        'attrs>=19.1.0,<20',
        'iso8601>=0.1.12,<0.2',
        'josepy>=1.1.0,<2',
        'yarl>=1.3.0,<2',
    ],
)
