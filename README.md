# VehiPark - A vehicle parking app

This app aims to ease the process of finding and parking on spot across many destinations.

A basic Flask web application with user and admin login, session handling, and database integration using SQLAlchemy. The project uses environment variables for configuration and follows a modular structure with templates and models separated.

## Demo Links

Live Demo of the project: [Live Demo Link](https://vehipark.onrender.com/login)

Demo Video of the project: [Demo Video Link](https://drive.google.com/file/d/1aqssogkvOXlIhdmeXllthIzn8s3EPeEA/view?usp=sharing)

## Screeshots

<img width="1407" height="810" alt="Screenshot 2026-05-23 at 6 08 21 AM" src="https://github.com/user-attachments/assets/8247aca7-8462-4557-bffa-669e01160344" />
<img width="1408" height="812" alt="Screenshot 2026-05-23 at 6 08 53 AM" src="https://github.com/user-attachments/assets/87f7acbb-8f5b-4a37-b710-76c56e7de9c8" />
<img width="1408" height="808" alt="Screenshot 2026-05-23 at 6 03 26 AM" src="https://github.com/user-attachments/assets/fd89ead0-21a6-437e-9331-61648d801914" />
<img width="1409" height="812" alt="Screenshot 2026-05-23 at 6 04 15 AM" src="https://github.com/user-attachments/assets/b23b027d-0e50-4089-9c5e-51b9637e60fa" />

## How to Run locally?

### Set up a virtual environment:

   Run `python -m venv venv`
   then activate using `source venv/bin/activate`
   
### Install the dependencies:

   Run `pip install -r requirements.txt`
   
### configure the `.env` file with below variables:

  `SQLALCHEMY_DATABASE_URI=sqlite:///db.sqlite3`
  
  `SECRET_KEY=your-secret-here`
  
  `SQLALCHEMY_TRACK_MODIFICATIONS=False`
  
  `ADMIN_USERNAME=sample-username`
  
  `ADMIN_PASSWORD=sample-pass`
  
### Run 
`python app.py`



