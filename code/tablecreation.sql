--CREATE TYPE binary_enum AS ENUM ('0', '1'); --I'm not sure do we need this one, we can use boolean

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
     name varchar(30) NOT NULL, --decreased the size to 30
     doses int NOT NULL CHECK (doses>0 and doses <3), --doses can be up to two so I've changed the type to int + added a check
     tempMin Int CHECK (tempMin >= -90 AND tempMin <= 8 and tempMax>=tempMin) NOT NULL,
     tempMax Int CHECK (tempMax >= -90 AND tempMax <= 8 and tempMax>=tempMin) NOT NULL
);

CREATE TABLE  Manufacturer(
     ID varchar(2) PRIMARY KEY, --added UNIQUE constraint
     country varchar(30), --decreased the size to 30
     phone varchar(20), --removed the UNIQUE constraint as I don't find it necessary, decreased varchar size to 12
     vaccine varchar (3),
     FOREIGN KEY (vaccine) REFERENCES VaccineType(ID) --changed this one to a foreign key
);

CREATE TABLE VaccinationStations ( --name changed to plural
  name varchar (50) PRIMARY KEY NOT NULL, --name changed back to name
  address varchar (100) DEFAULT null,
  phone varchar (20) DEFAULT null
);

CREATE TABLE  VaccineBatch(
     batchID varchar(4) PRIMARY KEY NOT NULL,
     amount Int CHECK (amount >= 10 AND amount <= 20) NOT NULL, --swapped amount and type attributes
     type varchar(3) not null,
     manufacturer varchar(2) ,
     manufDate date NOT NULL,
     expiration date NOT NULL,
     location varchar(50) NOT null, --decreased the size
     FOREIGN key (manufacturer) REFERENCES Manufacturer(ID),
     FOREIGN key (type) REFERENCES VaccineType(ID),
     FOREIGN KEY (location) REFERENCES VaccinationStations(name)
);

CREATE TABLE TransportationLog (
  batchID varchar(4),
  arrival varchar (50),
  departure varchar(50),
  dateArr date, --changed the data type
  dateDep date,--changed the data type
  FOREIGN key (arrival) REFERENCES VaccinationStations (name),
  FOREIGN key (departure) REFERENCES VaccinationStations (name),
  FOREIGN KEY (batchID) REFERENCES VaccineBatch(batchID),
  PRIMARY KEY (batchID, arrival,departure,dateArr,dateDep)
);

CREATE TABLE StaffMembers (
  ssNo varchar PRIMARY KEY, --added UNIQUE constraint
  name varchar (30) NOT NULL,
  birthday date NOT NULL, --changed the data type
  phone varchar (20),
  role staff DEFAULT null,
  status int CHECK (status = 0 OR status = 1) DEFAULT null, --changed the data type again
  hospital varchar (50),
  foreign key (hospital) references VaccinationStations(name)
);

create table Shifts(
  station varchar (50),
  weekday weekdays NOT NULL,
  worker varchar,
  foreign key (station) references VaccinationStations(name),
  foreign key (worker) references StaffMembers(ssNo),
  PRIMARY KEY (station, weekday, worker)
);

CREATE TABLE Vaccinations ( --added table
  date date,
  location varchar (50),
  batchID varchar (4),
  foreign key (location) references VaccinationStations(name),
  foreign key (batchID) references VaccineBatch(batchID),
  PRIMARY KEY (date, location)
);

CREATE TABLE Patients (
  ssNo varchar PRIMARY KEY,
  name varchar NOT NULL,
  birthday date NOT NULL,
  gender genders NOT NULL
);

CREATE TABLE VaccinePatients (
  date date ,
  location varchar,
  patientSsNo varchar, --changed to match the example data column name
  foreign key (patientSsNo) references Patients(ssNo),
  foreign key (location) references VaccinationStations(name),
  PRIMARY KEY (date, patientSsNo)

);

CREATE TABLE Symptoms (
  name varchar(50) PRIMARY KEY,  --name changed back to name
  criticality int CHECK (criticality = 0 OR criticality = 1) NOT NULL
);

CREATE TABLE Diagnosis ( --changed name to match the sheet name
  patient char,
  symptom varchar not null,
  date date not null,
  foreign key (patient) references Patients(ssNo),
  foreign key (symptom) references Symptoms(name),
  PRIMARY KEY (patient, symptom) --changed the other attribute to symptom, in case one patient reports several symptoms
);


--create table Appointment(
--	patient char(11) not null,
--	doctor char(11) not null,
--	date date,
--	location varchar,
--	timeSlot int,
--	foreign key (patient) references Patients(ssNo),
--	foreign key (doctor) references StaffMembers(ssNo),
--	foreign key (location) references VaccinationStations(name),
--	PRIMARY KEY (patient, doctor, date, location timeslot)
--);