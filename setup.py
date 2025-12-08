from setuptools import setup, find_packages

setup(
    name="editdna",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "numpy>=1.21.0",
        "opencv-python>=4.5.0",
        "pytesseract>=0.3.8",
        "pydub>=0.25.1",
        "ffmpeg-python>=0.2.0",
        "python-dotenv>=0.19.0",
    ],
    python_requires=">=3.8",
)