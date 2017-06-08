from distutils.core import setup


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
    install_requires=[
        'setuptools'
    ],
    entry_pooints={
        'console_scripts':[
            'asocks-server=server.__main__:start_serve' 
        ]
    },
)
