from setuptools import setup, find_packages

setup(
    author='Marcin Kurczewski',
    author_email='rr-@sakuya.pl',
    name='mpvmd',
    long_description='mpv music daemon',
    version='0.1',
    url='https://github.com/rr-/mpvmd',
    packages=find_packages(),

    entry_points={
        'console_scripts': [
            'mpvmd = mpvmd.server.__main__:main',
            'mpvmc = mpvmd.client.__main__:main'
        ]
    },

    install_requires=[
        'mpv',
        'parsimonious',
    ],
    dependency_links=[
        'git+ssh://git@github.com/jaseg/python-mpv.git#egg=mpv-0.1',
    ],

    classifiers=[
        'Environment :: Console',
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Desktop Environment',
        'Topic :: Multimedia :: Sound/Audio :: Players',
    ])
