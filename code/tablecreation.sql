DROP TABLE IF EXISTS vaccinetype CASCADE;

DROP TABLE IF EXISTS manufacturer CASCADE;

DROP TABLE IF EXISTS vaccinationstations CASCADE;

DROP TABLE IF EXISTS vaccinebatch CASCADE;

DROP TABLE IF EXISTS transportationlog CASCADE;

DROP TABLE IF EXISTS staffmembers CASCADE;

DROP TABLE IF EXISTS shifts CASCADE;

DROP TABLE IF EXISTS vaccinations CASCADE;

DROP TABLE IF EXISTS patients CASCADE;

DROP TABLE IF EXISTS vaccinepatients CASCADE;

DROP TABLE IF EXISTS symptoms CASCADE;

DROP TABLE IF EXISTS diagnosis CASCADE;

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

CREATE TABLE VaccineType
(
    ID      VARCHAR(3) PRIMARY KEY,
    name    VARCHAR(30) NOT NULL,                                 --decreased the size to 30
    doses   INT         NOT NULL CHECK (doses > 0 AND doses < 3), --doses can be up to two so I've changed the type to int + added a check
    tempMin INT         NOT NULL CHECK (tempMin >= -90 AND tempMin <= 8 AND tempMax >= tempMin),
    tempMax INT         NOT NULL CHECK (tempMax >= -90 AND tempMax <= 8 AND tempMax >= tempMin)
);

CREATE TABLE Manufacturer
(
    ID      VARCHAR(2) PRIMARY KEY,
    country VARCHAR(30),                              --decreased the size to 30
    phone   VARCHAR(20),                              --removed the UNIQUE constraint as I don't find it necessary, decreased varchar size to 12
    vaccine VARCHAR(3),
    FOREIGN KEY (vaccine) REFERENCES VaccineType (ID) --changed this one to a foreign key
);

CREATE TABLE VaccinationStations
(                                    --name changed to plural
    name    VARCHAR(50) PRIMARY KEY, --name changed back to name
    address VARCHAR(100) DEFAULT NULL,
    phone   VARCHAR(20)  DEFAULT NULL
);

CREATE TABLE VaccineBatch
(
    batchID      VARCHAR(4) PRIMARY KEY,
    amount       INT CHECK (amount >= 10 AND amount <= 20) NOT NULL, --swapped amount and type attributes
    manufacturer VARCHAR(2)                                NOT NULL,
    manufDate    DATE                                      NOT NULL,
    expiration   DATE                                      NOT NULL,
    location     VARCHAR(50)                               NOT NULL, --decreased the size
    FOREIGN KEY (manufacturer) REFERENCES Manufacturer (ID),
    FOREIGN KEY (location) REFERENCES VaccinationStations (name)
);

CREATE TABLE TransportationLog
(
    batchID   VARCHAR(4),
    arrival   VARCHAR(50),
    departure VARCHAR(50),
    dateArr   DATE, --changed the data type
    dateDep   DATE, --changed the data type
    FOREIGN KEY (arrival) REFERENCES VaccinationStations (name),
    FOREIGN KEY (departure) REFERENCES VaccinationStations (name),
    FOREIGN KEY (batchID) REFERENCES VaccineBatch (batchID),
    PRIMARY KEY (batchID, arrival, departure, dateArr, dateDep)
);

CREATE TABLE StaffMembers
(
    ssNo     VARCHAR PRIMARY KEY,
    name     VARCHAR(30) NOT NULL,
    birthday DATE        NOT NULL,                              --changed the data type
    phone    VARCHAR(20),
    role     staff                                DEFAULT NULL,
    status   INT CHECK (status = 0 OR status = 1) DEFAULT NULL, --changed the data type again
    hospital VARCHAR(50),
    FOREIGN KEY (hospital) REFERENCES VaccinationStations (name)
);

CREATE TABLE Shifts
(
    station VARCHAR(50),
    weekday weekdays,
    worker  VARCHAR,
    FOREIGN KEY (station) REFERENCES VaccinationStations (name),
    FOREIGN KEY (worker) REFERENCES StaffMembers (ssNo),
    PRIMARY KEY (station, weekday, worker)
);

CREATE TABLE Vaccinations
(
    date     DATE,
    location VARCHAR(50),
    batchID  VARCHAR(4),
    FOREIGN KEY (location) REFERENCES VaccinationStations (name),
    FOREIGN KEY (batchID) REFERENCES VaccineBatch (batchID),
    PRIMARY KEY (date, location)
);

CREATE TABLE Patients
(
    ssNo     VARCHAR PRIMARY KEY,
    name     VARCHAR NOT NULL,
    birthday DATE    NOT NULL,
    gender   genders NOT NULL
);

CREATE TABLE VaccinePatients
(
    date        DATE,
    location    VARCHAR,
    patientSsNo VARCHAR, --changed to match the example data column name
    FOREIGN KEY (patientSsNo) REFERENCES Patients (ssNo),
    FOREIGN KEY (location) REFERENCES VaccinationStations (name),
    PRIMARY KEY (date, patientSsNo)
);

CREATE TABLE Symptoms
(
    name        VARCHAR(50) PRIMARY KEY, --name changed back to name
    criticality INT CHECK (criticality = 0 OR criticality = 1) NOT NULL
);

CREATE TABLE Diagnosis
(
    patient VARCHAR,
    symptom VARCHAR,
    date    DATE,
    FOREIGN KEY (patient) REFERENCES Patients (ssNo),
    FOREIGN KEY (symptom) REFERENCES Symptoms (name),
    PRIMARY KEY (patient, symptom, date) --changed the other attribute to symptom, in case one patient reports several symptoms
);
