from setuptools import setup

setup(
    name = 'asocks',
    version = '0.1.0',
    description = 'A SOCKS5 proxy server implementation based on '
                  'async IO model.',
    author = 'Nan Wu',
    author_email = 'nanbytesflow@gmail.com',
    license='MIT',
    url = 'https://github.com/nanwu/asocks',
    keywords = ['socks', 'proxy', 'python3', 'async'],
    classifiers=[
        # 3: Alpha
        # 4: Beta
        # 5: Production/Stable
	'Developemnt Status :: 3 - Alpha',

        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5'
    ],
    packages=['server'],
    py_modules=['auth', 'networking', 'logger', 'exception'],
    entry_points={
        'console_scripts':[
            'asocks-server=server.__main__:main' 
        ]
    },
)
