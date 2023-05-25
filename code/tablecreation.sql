CREATE TYPE binary_enum AS ENUM ('0', '1'); --I'm not sure do we need this one, we can use boolean

CREATE TYPE staff AS ENUM (
  'nurse',
  'doctor',
  'null'
);

CREATE TYPE weekdays AS ENUM (
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday'
);

CREATE TYPE genders AS ENUM (
  'M',
  'F'
);

CREATE TABLE  VaccineType(
     ID varchar(3) PRIMARY KEY UNIQUE NOT NULL, --added UNIQUE constraint
     name varchar(255) NOT NULL,
     doses int NOT NULL CHECK (doses>0 and doses <3), --doses can be up to two so I've cn´hanged the type to int + added a check
     tempMin Int CHECK (tempMin >= -90 AND tempMin <= 8 and tempMax>=tempMin) NOT NULL,
     tempMax Int CHECK (tempMax >= -90 AND tempMax <= 8 and tempMax>=tempMin) NOT NULL
);




CREATE TABLE  Manufacturer(
     ID varchar(2) PRIMARY KEY, --added UNIQUE constraint
     country varchar(255),
     phone varchar(12), --removed the UNIQUE constraint as I don't find it necessary, decreased varchar size to 12
     vaccine varchar(3)
);


CREATE TABLE  VaccineBatch(
     batchID varchar(4) PRIMARY KEY NOT NULL,
     type varchar(3) not null,
     amount Int CHECK (amount >= 10 AND amount <= 20) NOT NULL,
     manufacturer varchar(2) ,
     manufDate timestamp NOT NULL,
     expiration timestamp NOT NULL,
     location varchar(255) NOT null,
     FOREIGN key (manufacturer) REFERENCES Manufacturer(ID),
     FOREIGN key (type) REFERENCES VaccineType(ID)
);



CREATE TABLE VaccinationStation (
  stationName varchar PRIMARY KEY NOT NULL, --name changed to stationName
  address varchar DEFAULT null,
  phone varchar DEFAULT null
);

CREATE TABLE TransportationLog (
  batchID varchar(4),
  arrival varchar,
  departure varchar,
  dateArr timestamp,
  dateDep timestamp,
  FOREIGN key (arrival) REFERENCES VaccinationStation(stationName),
  FOREIGN key (departure) REFERENCES VaccinationStation(stationName),
  foreign key (batchid) references VaccineBatch(batchID),
  PRIMARY KEY (batchID, arrival,departure,dateArr,dateDep)
);

CREATE TABLE StaffMembers (
  ssNo char(13) PRIMARY KEY, --added UNIQUE constraint
  name varchar NOT NULL,
  birthday timestamp NOT NULL,
  phone varchar,
  role staff DEFAULT null,
  status boolean DEFAULT null,
  hospital varchar,
  foreign key (hospital) references VaccinationStation(stationName)
);

create table Shifts(
  station varchar,
  weekday weekdays,
  worker char(13),
  foreign key (station) references VaccinationStation(stationName),
  foreign key (worker) references StaffMembers(ssNo),
  PRIMARY KEY (station, weekday, worker)
);


CREATE TABLE Patients (
  ssNo char(13) PRIMARY KEY, --added UNIQUE constraint
  name varchar NOT NULL,
  birthday timestamp NOT NULL,
  gender genders NOT NULL
);

CREATE TABLE VaccinePatients (
  date timestamp ,
  location varchar,
  ssNo char(13),
  foreign key (ssNo) references Patients(ssNo),
  foreign key (location) references VaccinationStation(stationName),
  PRIMARY KEY (date, ssNo)
  
);

CREATE TABLE Symptoms (
  symptomName varchar(50) PRIMARY KEY,  --name changed to symptomName
  criticality binary_enum NOT NULL
);

CREATE TABLE SymptomReport (
  ssNo char(13),
  symptomName varchar not null,
  date timestamp not null,
  foreign key (ssNo) references Patients(ssNo),
  foreign key (symptomName) references Symptoms(symptomName),
  PRIMARY KEY (ssNo, date)
);

create table Appointment(
	patient char(13) not null,
	doctor char(13) not null,
	date timestamp,
	location varchar,
	timeSlot int,
	foreign key (patient) references Patients(ssNo),
	foreign key (doctor) references StaffMembers(ssNo),
	foreign key (location) references VaccinationStation(stationName),
	PRIMARY KEY (patient, doctor, date, location, timeslot)
)

