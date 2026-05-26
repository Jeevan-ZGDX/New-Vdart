from setuptools import setup, find_packages

setup(
    name="talkcraft_coach",
    version="4.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "fastapi>=0.110.0",
        "uvicorn>=0.29.0",
        "sqlalchemy>=2.0.30",
        "pyjwt>=2.8.0",
        "pydantic>=2.7.0",
        "pydantic[email]>=2.7.0",
    ],
    extras_require={
        "dashboard": ["streamlit>=1.35.0", "plotly>=5.22.0"],
        "http": ["httpx>=0.27.0"],
    },
    python_requires=">=3.10",
)
