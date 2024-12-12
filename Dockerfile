# Clone the repository
# RUN git pull

FROM python:3.10

WORKDIR ./workdir

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose port 2000 (if required)
EXPOSE 5000

# Specify the command to run the Python application
CMD ["python", "./server.py"]


