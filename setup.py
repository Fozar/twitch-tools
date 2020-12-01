from setuptools import setup

setup(
    name="twitch-tools",
    version="0.3.0",
    packages=["twitch"],
    url="https://github.com/Fozar/twitch-tools",
    license="MIT",
    author="Fozar",
    author_email="fozar97@gmail.com",
    description="Twitch API Wrapper for Python",
    install_requires=[
       'aiohttp>=3.0.0,<4.0.0'
    ]
)
