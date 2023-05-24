CREATE TYPE binary_enum AS ENUM ('0', '1');

CREATE TABLE  VaccineType(
     ID varchar(3) primary key not null,
     name varchar(255) not null,
     doses binary_enum not null,
     tempMin Int CHECK (tempMin >= -90 AND tempMin <= 8 and tempMax>=tempMin) not null,
     tempMax Int CHECK (tempMax >= -90 AND tempMax <= 8 and tempMax>=tempMin) not null
);


CREATE TABLE  Manufacturer(
     ID varchar(2) primary key,
     country varchar(255),
     phone varchar(255) unique,
     vaccine varchar(3)
);


CREATE TABLE  VaccineBatch(
     batchID varchar(4) primary key not null,
     type varchar(3) not null,
     amount Int CHECK (amount >= 10 AND amount <= 20) not null,
     manufacturer varchar(2) not null,
     manufDate timestamp not null,
     expiration timestamp not null,
     location varchar(255) not null
);