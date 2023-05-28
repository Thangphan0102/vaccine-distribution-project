-- Query 1: find the staff members working on 10.5.21: ssNo, role, vaccination status, location

SELECT sm.ssno, sm.name, sm.phone, sm.role, sm.status, v.location
FROM staffmembers sm
         JOIN shifts s
              ON sm.ssno = s.worker
         JOIN vaccinations v
              ON v.location = s.station
WHERE s.weekday = 'Monday'
  AND v.date = '2021-05-10';

-- Query 2: list all the doctors working on Wed in Helsinki

SELECT ssNo, staffmembers.name
FROM StaffMembers, Shifts, Vaccinationstations
    WHERE shifts.weekday = 'Wednesday'
    AND staffmembers.role = 'doctor'
    AND Shifts.worker = StaffMembers.ssNo
    AND staffmembers.hospital = vaccinationstations.name
    AND address LIKE '%HELSINKI';

-- Query 3: list batchID and phone number of hospitals where batches with inconsistent location data should be

SELECT tl.batchid, vb.location AS current_location, tl.arrival AS last_location
FROM (SELECT tl.batchid, MAX(tl.datearr) AS last_date
      FROM transportationlog tl
      GROUP BY tl.batchid) bld
         JOIN transportationlog tl
              ON tl.batchid = bld.batchid
                  AND tl.datearr = bld.last_date
         JOIN vaccinebatch vb
              ON tl.batchid = vb.batchid;

SELECT vaccinebatch.batchid, vaccinationstations.phone
FROM vaccinebatch, vaccinationstations,
(SELECT transportationlog.batchid AS batchid, transportationlog.arrival AS arrival
FROM transportationlog,
(SELECT transportationlog.batchID, MAX(datearr)
    FROM transportationlog GROUP BY batchID) AS latestarrival
    WHERE transportationlog.batchid = latestarrival.batchid
	AND transportationlog.datearr = latestarrival.max) AS latestlocation
WHERE latestlocation.batchid = vaccinebatch.batchid
AND vaccinebatch.location <> latestlocation.arrival
AND vaccinationstations.name = latestlocation.arrival;

-- Query 4: all patients with critical symptoms diagnosed after 10.5.21 matched with vaccination data

SELECT diagnosis.patient AS patient, vaccinebatch.batchID AS batchID, --can't test ths one yet
    vaccinetype.name AS vaccineType, vaccinations.date AS date,
    vaccinations.location AS location
FROM vaccinebatch, diagnosis, vaccinetype, vaccinations, symptoms, vaccinepatients
    WHERE symptoms.criticality = 1
    AND diagnosis.symptom = symptoms.name
    AND diagnosis.date > '2021-05-10'
    AND diagnosis.patient = vaccinepatients.patientssno
    AND vaccinations.batchID = vaccinebatch.batchid
    AND vaccinebatch.type = vaccinetype.id
    AND vaccinepatients.location = vaccinations.location
    AND vaccinepatients.date = vaccinations.date;

-- Query 5: create a view for patients with additional column vaccinationStatus (0/1)

CREATE OR REPLACE VIEW VaccinatedPatients AS
SELECT p.*,
       CASE
           WHEN doses_took >= 2 THEN 1
           ELSE 0
           END AS vaccinationStatus
FROM (SELECT patientssno, COUNT(*) AS doses_took
      FROM vaccinepatients
      GROUP BY patientssno) pdt
         JOIN patients p
              ON p.ssno = pdt.patientssno;

-- Query 6: find the total amount of vaccine doses in every clinic, as well as amounts of doses by vaccine type

SELECT sub.location,
       sub.vaccine,
       sub.amount,
       SUM(sub.amount) OVER (PARTITION BY sub.location) AS amount
FROM (SELECT location, mf.vaccine, SUM(amount) AS amount
      FROM vaccinebatch vb
               JOIN manufacturer mf
                    ON vb.manufacturer = mf.id
      GROUP BY location, mf.vaccine
      ORDER BY location, mf.vaccine) sub;